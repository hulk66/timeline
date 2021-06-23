'''
Copyright (C) 2021 Tobias Himstedt


This file is part of Timeline.

Timeline is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Timeline is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

import logging
import numpy
from celery import chain
from flask import current_app
from pymysql.err import InternalError
from scipy.spatial.distance import cdist
from sklearn.cluster import DBSCAN
from sqlalchemy import and_, or_
from timeline.domain import Face, Person, Photo, Status
from timeline.extensions import celery, db

logger = logging.getLogger(__name__)
MAX_CLUSTER_SIZE = 50


def assign_new_person(face, person):
    if not face or not person:
        # nothing we can do, can only happen due to parallel tasks
        # working on the same entities
        return

    former_person = face.person
    if former_person:
        former_person.faces.remove(face)
        if len(former_person.faces) == 0:
            logger.debug(
                "Deleting Person %i as it has no more faces attached", former_person.id)
            db.session.delete(former_person)
    face.person = person


def distance(s):
    return float(current_app.config[s])


def distance_very_safe():
    return distance('FACE_DISTANCE_VERY_SAFE')


def distance_safe():
    return distance('FACE_DISTANCE_SAFE')


def distance_maybe():
    return distance('FACE_DISTANCE_MAYBE')


def get_confidence_level(distance):

    if distance < distance_very_safe():
        result = Face.CLASSIFICATION_CONFIDENCE_LEVEL_VERY_SAFE
    elif distance_very_safe() <= distance < distance_safe():
        result = Face.CLASSIFICATION_CONFIDENCE_LEVEL_SAFE
    elif distance_safe() <= distance < distance_maybe():
        result = Face.CLASSIFICATION_CONFIDENCE_LEVEL_MAYBE
    else:
        result = Face.CLASSIFICATION_CONFIDENCE_NONE
    return result


def face_distance_euc(face_encodings, face_to_compare):
    """
    Given a list of face encodings, compare them to a known face encoding and get a euclidean distance
    for each comparison face. The distance tells you how similar the faces are.
    :param faces: List of face encodings to compare
    :param face_to_compare: A face encoding to compare against
    :return: A numpy ndarray with the distance for each face in the same order as the 'faces' array
    """
    if len(face_encodings) == 0:
        return numpy.empty((0))

    return numpy.linalg.norm(face_encodings - face_to_compare, axis=1)


def remove_unconfirmed_persons():
    persons = Person.query.filter(Person.confirmed == False)
    for person in persons:
        person.faces = []
    persons.delete()


@celery.task(name="Group Faces", ignore_result=True)
def group_faces():
    logger.debug("Group Faces")
    status = Status.query.first()
    epsilon = float(current_app.config['FACE_CLUSTER_EPSILON'])
    min_samples = int(current_app.config['FACE_CLUSTER_MIN_SAMPLES'])
    max_faces = int(current_app.config['FACE_CLUSTER_MAX_FACES'])
    logger.debug("using EPSILON %f and MIN_SAMPLES %i", epsilon, min_samples)
    result = find_unclassified_and_unclustered_faces(limit=max_faces)

    # mark_faces = len(result) == max_faces
    logger.debug("found %i to match", len(result))
    if len(result) < max_faces:
        logger.debug("All faces clustered already. Reset them")
        # it seems all faces have been already subject of clustering
        # or the set of faces is too small to do clustering
        # let's start from the beginning then.
        # Therefore reset the clustering information
        clustered_faces = find_unclassified_clustered_faces()
        # clustered_faces.update({Face.already_clustered:False})
        for f in clustered_faces:
            f.already_clustered = False
        result = find_unclassified_and_unclustered_faces(limit=max_faces)

    if len(result) > 0:
        face_ids, encodings = zip(*result)

        face_ids = numpy.asarray(face_ids)
        encodings = numpy.asarray(encodings)
        logger.debug("Group Faces - Starting DBSCAN - might take a minute or two")
        cluster_data = DBSCAN(eps=epsilon, min_samples=min_samples).fit(encodings)
        labels = cluster_data.labels_

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        logger.debug("Group Faces - Found %i clusters", n_clusters)
        if n_clusters > 0:
            for cluster in range(n_clusters - 1):
                logger.debug("Group Faces - Cluster %i/%i",
                             cluster, n_clusters-1)
                indices = numpy.where(labels == cluster)
                logger.debug(
                    "Group Faces - Creating Cluster with %i faces", len(indices[0]))
                person = None
                for index in indices[0][:MAX_CLUSTER_SIZE]:
                    face_id = int(face_ids[index])
                    face = Face.query.get(face_id)
                    # face.already_clustered = True
                    if not face.person or not face.person.confirmed:
                        face.distance_to_human_classified = 2
                        face.confidence_level = Face.CLASSIFICATION_CONFIDENCE_NONE
                        face.confidence = 1.0
                    if face.person and not person:
                        person = face.person
                        logger.debug(
                            "Use existing person for the identified group")
                if person is None:
                    status.new_faces = True
                    person = Person()
                    person.name = "Unknown"
                    person.confirmed = False
                    person.ignore = False
                    logger.debug("Create new person for face group")

                # Now make sure all faces belong to the same person we already have identified
                for index in indices[0][:MAX_CLUSTER_SIZE]:
                    face_id = int(face_ids[index])
                    face = Face.query.get(face_id)
                    face.person = person
                db.session.commit()

        # Finally delete persons which have no related face anymore
        Person.query.filter(~Person.faces.any()).delete(
            synchronize_session=False)

    db.session.commit()
    logger.debug("Grouping done")


@celery.task(ignore_result=True)
def schedule_next_grouping(minutes=None):
    if minutes:
        group_schedule = minutes
    else:
        group_schedule = int(current_app.config['GROUP_FACES_EVERY_MINUTES'])
    logger.debug("Scheduling next face grouping in %i minutes", group_schedule)
    # task = (group_faces.si() | schedule_next_grouping.si()).apply_async(args=(), countdown=group_schedule * 60, queue="beat")
    c = chain(group_faces.s().set(queue="beat"),
              schedule_next_grouping.si().set(queue="beat"))
    c.apply_async(countdown=group_schedule*60)


def check_for_face_grouping():
    max_faces = current_app.config['FACE_CLUSTER_MAX_FACES']

    if Face.query.filter(Face.person == None).count() > max_faces:
        logger.debug("Already %i new faces found, clustering will be invoked")
        group_faces()


def find_unclassified_clustered_faces():
    # find all faces, which are not ignored and are
    # not assigned to a person and which have been already
    # clustered

    q = Face.query.filter(
        and_(
            Face.ignore == False,
            Face.person_id == None,
            Face.already_clustered == True
        ))
    return q


def find_unclassified_and_unclustered_faces(limit=None):
    # Find all faces which
    # are not to be ignored and
    #   have either no person assigned or
    #      if a person is assigned then then this assignment is only a maybe

    q = Face.query.join(Photo).join(Person, isouter=True) \
        .filter(and_(Face.ignore == False,
                     Face.already_clustered == False,
                     Face.photo_id == Photo.id,
                     or_(Face.person == None,
                         Face.confidence_level <= Face.CLASSIFICATION_CONFIDENCE_LEVEL_MAYBE))).order_by(Photo.created.desc())

    if limit:
        q = q.limit(limit)

    logger.debug(q)
    return q.with_entities(Face.id, Face.encoding).all()


def find_all_non_manual_classified_or_unclassified_faces(limit=None):
    # Find all faces which
    # are not to be ignored and
    #   have either person assigned or
    #      if a person is assigned then this is a person which is is not confirmed by the user

    q = Face.query.join(Photo).join(Person, isouter=True) \
        .filter(and_(
            Face.ignore == False,
            Face.photo_id == Photo.id,
            or_(Face.person == None,
                Face.confidence_level == Face.CLASSIFICATION_CONFIDENCE_LEVEL_MAYBE,
                and_(Face.person_id == Person.id, Person.confirmed == False))))

    if limit:
        q = q.order_by(db.func.random()).limit(limit)

    logger.debug(q)
    return q.with_entities(Face.id, Face.encoding).all()


def find_unclassified_faces(limit=None):
    # Find all faces which
    # are not to be ignored and
    #   have either person assigned or
    #      if a person is assigned then this is a person which is is not confirmed by the user

    q = Face.query.join(Person, isouter=True) \
        .filter(and_(Face.ignore == False,
                     or_(Face.person == None,
                         and_(Face.person_id == Person.id, Person.confirmed == False))))
    if limit:
        q = q.limit(limit)
    # logger.debug(q)
    return q.with_entities(Face.id, Face.encoding).all()


@celery.task(name="Match all unknown Faces", ignore_result=True)
def match_all_unknown_faces():
    """Iterate over all unknown faces and compare them against already classified faces.
    For each classified face it is recognized how "far" it is away from a manual face 
    confirmed by the user (distance = 0).
    The close an unknow face to a manual classified faces is, the less close it has to be.
    This is to prevent that the radius of a detected person is getting wider and wider 
    (and therefore less precise with more false positive matches)
    """
    logger.debug("Match all unknown faces")

    totalAssigned = 0

    max_faces = int(current_app.config['FACE_CLUSTER_MAX_FACES'])
    unmatched = find_all_non_manual_classified_or_unclassified_faces(
        limit=max_faces)
    if len(unmatched) > 0:
        unknown_ids, unkown_encodings = get_ids_and_encodings(unmatched)
        # logger.debug("Found %i unclassified faces", len(unmatched))

        # Make the limit configurable
        known_faces = find_all_classified_known_faces(limit=max_faces)
        if len(known_faces) > 0:

            known_ids, known_encodings = get_ids_and_encodings(known_faces)
            logger.debug("Found %i unclassified faces to match against %i classified faces", len(
                unmatched), len(known_faces))

            logger.debug("Calculating Distances - might take a few minutes")
            distances = cdist(unkown_encodings,
                              known_encodings, metric="euclidean")
            logger.debug("Calc Distances done")

            l = len(distances)
            counter = 0
            for d in distances:
                percent = counter/l * 100
                if percent % 10 == 0:
                    logger.debug("Checking unknown face %i percent", percent)
                unknown_face_id = int(unknown_ids[counter])
                unknown_face = Face.query.get(unknown_face_id)
                counter += 1

                min_index = numpy.argmin(d)
                distance = d[min_index]
                found_face_id = int(known_ids[min_index])
                found_face = Face.query.get(found_face_id)
                # confidence = get_confidence_level(distance)
                if classify_face(distance, found_face, unknown_face):
                    totalAssigned += 1

            db.session.commit()

    logger.debug("Match Faces - could classify %i faces", totalAssigned)


@celery.task(ignore_result=True)
def do_background_face_tasks():
    match_all_unknown_faces()
    match_all_ignored_faces()
    group_faces()
    match_faces_schedule = int(current_app.config['MATCH_FACES_EVERY_MINUTES'])
    do_background_face_tasks.apply_async(
        (), queue="beat", countdown=match_faces_schedule*60)


def classify_face(distance, found_face, unknown_face):
    confidence = get_confidence_level(distance)

    if found_face.distance_to_human_classified == 0 and distance < distance_maybe():
        assign_new_person(unknown_face, found_face.person)
        unknown_face.confidence_level = confidence
        unknown_face.confidence = distance.item()
        unknown_face.distance_to_human_classified = 1
        logger.debug("Found person classified by human; face %i is %s with confidence %f",
                     unknown_face.id, found_face.person.name, unknown_face.confidence)
        return True
    elif found_face.distance_to_human_classified == 1 and distance < distance_safe():
        assign_new_person(unknown_face, found_face.person)
        unknown_face.confidence_level = confidence
        unknown_face.confidence = distance.item()
        unknown_face.distance_to_human_classified = 2
        logger.debug("Found person classified by classifier with distance 1 to human classified; face %i is %s with confidence %f",
                     unknown_face.id, found_face.person.name, unknown_face.confidence)
        return True

    elif found_face.distance_to_human_classified == 2 and distance < distance_very_safe():
        assign_new_person(unknown_face, found_face.person)
        unknown_face.confidence_level = confidence
        unknown_face.confidence = distance.item()
        unknown_face.distance_to_human_classified = 3
        logger.debug("Found person classified by classifier with distance 2 to human classified; face %i is %s with confidence %f",
                     unknown_face.id, found_face.person.name, unknown_face.confidence)
        return True
    return False


@celery.task(ignore_result=True)
def schedule_next_match_all_unknown_faces(minutes=None):
    if minutes:
        match_faces_schedule = minutes
    else:
        match_faces_schedule = int(
            current_app.config['MATCH_FACES_EVERY_MINUTES'])
    logger.debug("Scheduling next face matching in %i minutes",
                 match_faces_schedule)
    # task = (match_all_unknown_faces.si() | schedule_next_match_all_unknown_faces.si()) \
    #    .apply_async(args=(), countdown=match_faces_schedule*60, queue="beat")
    c = chain(match_all_unknown_faces.s().set(queue="beat"),
              schedule_next_match_all_unknown_faces.si().set(queue="beat"))
    c.apply_async(countdown=match_faces_schedule*60)


def get_ids_and_encodings(face_list):
    ids, encodings = zip(*face_list)
    ids = numpy.asarray(ids)
    encodings = numpy.asarray(encodings)
    return ids, encodings


@celery.task(name="Identify Faces", autoretry_for=(InternalError,))
def match_unknown_face(face_id):
    """Tries to find an already classified face for one that that is not yet classified
    face_id - The Face ID which is to classified against existing other faces
    """
    unknown_face = Face.query.get(face_id)
    classified_faces = find_all_classified_known_faces()

    classified_faces_len = len(classified_faces)
    logger.debug("Match unknown Face %i - Considering %i classified faces",
                 face_id, classified_faces_len)

    if classified_faces_len > 0:

        id, distance = find_closest(unknown_face, classified_faces)

        found_face = Face.query.get(id)
        # logger.debug("Match unknown Face %i. Closest is %s with distance %f",face_id, found_face.person.name, distance)
        # confidence = get_confidence_level(distance)

        classify_face(distance, found_face, unknown_face)
        db.session.commit()

@celery.task(name="Match allignored Faces", ignore_result=True)
def match_all_ignored_faces():
    """Iterate over all unknown faces and compare them against already ignored faces.
    For each classified face it is recognized how "far" it is away from a manual face 
    confirmed by the user (distance = 0).
    The closeer an unknow face to a manual ignored faces is, the less closer it has to be.
    This is to prevent that the radius of a detected person is getting wider and wider 
    (and therefore less precise with more false positive matches)
    """
    logger.debug("Match all ignored faces")

    totalAssigned = 0

    max_faces = int(current_app.config['FACE_CLUSTER_MAX_FACES'])
    unmatched = find_all_non_manual_classified_or_unclassified_faces(
        limit=max_faces)
    if len(unmatched) > 0:
        unknown_ids, unkown_encodings = get_ids_and_encodings(unmatched)
        ignored_faces = find_all_ignored_faces()
        if len(ignored_faces) > 0:

            ignored_ids, ignored_encodings = get_ids_and_encodings(ignored_faces)
            logger.debug("Found %i unclassified faces to match against %i ignored faces", len(
                unmatched), len(ignored_faces))

            logger.debug("Calculating Distances - might take a few minutes")
            distances = cdist(unkown_encodings,
                              ignored_encodings, metric="euclidean")
            logger.debug("Calc Distances done")

            counter = 0
            l = len(distances)

            for d in distances:
                percent = counter/l * 100
                if percent % 10 == 0:
                    logger.debug("Checking ignored face %i percent", percent)
                unknown_face_id = int(unknown_ids[counter])
                unknown_face = Face.query.get(unknown_face_id)
                counter += 1

                min_index = numpy.argmin(d)
                distance = d[min_index]
                found_face_id = int(ignored_ids[min_index])
                found_face = Face.query.get(found_face_id)
                if check_ignore(found_face, unknown_face, distance):
                    totalAssigned += 1

            db.session.commit()

    logger.debug("atch all ignored faces - additionaly %i faces will be ignored", totalAssigned)


def check_ignore(found_face, unknown_face, distance):
    if found_face.distance_to_human_classified == 0 and distance < distance_safe():
        logger.debug("Ignoring face %d as it is close to an already ignored face %d", unknown_face.id, found_face.id)
        unknown_face.ignore = True
        unknown_face.distance_to_human_classified = 1
        return  True
    elif found_face.distance_to_human_classified == 1 and distance < distance_very_safe():
        logger.debug("Ignoring face %d as it is close to an already ignored face %d", unknown_face.id, found_face.id)
        unknown_face.ignore = True
        unknown_face.distance_to_human_classified = 2
        return True
    return False


@celery.task(name="Match ignored Faces", autoretry_for=(InternalError,))
def match_ignored_faces(face_id):
    """Compare the face with the ignored faces. If it is very close this will be also categorized 
    as ignore. Ortherwise we will see the same face over over popping up during the grouping
    """
    unknown_face = Face.query.get(face_id)
    ignored_faces = find_all_ignored_faces()
    ignored_faces_len = len(ignored_faces)
    logger.debug("Match unknown Face %i - Considering %i ignored faces",
                 face_id, ignored_faces_len)
    if ignored_faces_len > 0:
        id, distance = find_closest(unknown_face, ignored_faces)
        found_face = Face.query.get(id)
        check_ignore(found_face, unknown_face, distance)
        db.session.commit()


def find_all_ignored_faces():
    faces = Face.query.filter(Face.ignore == True) \
        .with_entities(Face.id, Face.encoding).all()
    return faces


def find_all_classified_faces():
    classified_faces = Face.query.join(Person) \
        .filter(and_(Face.person_id == Person.id, Person.confirmed == True)) \
        .with_entities(Face.id, Face.encoding).all()
    return classified_faces


def find_all_classified_known_faces(limit=None):
    classified_faces = Face.query.join(Person) \
        .filter(
            and_(
                Face.person_id == Person.id, 
                Person.confirmed == True,
                Face.confidence_level > Face.CLASSIFICATION_CONFIDENCE_LEVEL_MAYBE))
    if limit:
        classified_faces = classified_faces.order_by(
            db.func.random()).limit(limit)
    return classified_faces.with_entities(Face.id, Face.encoding).all()


# def find_manual_classified_faces():
#    classified_faces = Face.query.join(Person) \
#        .filter(and_(Face.person_id == Person.id, Face.distance_to_human_classified == 0)) \
#        .with_entities(Face.id, Face.encoding).all()
#    return classified_faces


def find_closest(face, face_id_encoding_list):
    face_ids_known, encodings_known = zip(*face_id_encoding_list)
    face_ids_known = numpy.asarray(face_ids_known)
    encodings_known = numpy.asarray(encodings_known)

    test = numpy.expand_dims(face.encoding, axis=0)
    r = face_distance_euc(encodings_known, test)

    # Find the index with the lowest / nearest distance
    min_index = numpy.argmin(r)
    id = int(face_ids_known[min_index])
    distance = r[min_index]
    return id, distance


@celery.task
def reset_person(person_id):
    logger.debug("Forgetting person %d, cleaning everything", person_id)
    Face.query.filter(Face.person_id == person_id).update( 
        {"person_id": None, 
        "ignore":False, 
        "already_clustered": False,
        "confidence_level": None,
        "distance_to_human_classified": None} )
    Person.query.filter(Person.id == person_id).delete()
    db.session.commit()


"""
# Currently Unused
@celery.task(name="Match similar Faces")
def match_known_face(face_id):
    known_face = Face.query.get(face_id)
    logger.debug("Match known face for %s", known_face.person.name)

    unclassified_faces = find_unclassified_faces()

    unclassified_faces_len = len(unclassified_faces)
    logger.debug(
        "Match known face - Considering %i unclassified faces", unclassified_faces_len)

    if unclassified_faces_len > 0:

        face_ids_unknown, encodings_unknown = zip(*unclassified_faces)
        face_ids_unknown = numpy.asarray(face_ids_unknown)
        encodings_unknown = numpy.asarray(encodings_unknown)

        test = numpy.expand_dims(known_face.encoding, axis=0)
        r = face_distance_euc(encodings_unknown, test)

        # Find the index with the lowest / nearest distance
        face_min_index = numpy.nonzero(r < Face.DISTANCE_SAFE)
        logger.debug("Match known Faces - Found %i similar faces",
                     len(face_min_index[0]))
        for found_face_index in face_min_index[0]:
            found_face_id = int(face_ids_unknown[found_face_index])
            found_face = Face.query.get(found_face_id)
            assign_new_person(found_face, known_face.person)
            logger.debug("Euclidean Distance: Nearest face for %i is %i",
                         known_face.id, found_face.id)
            db.session.commit()
"""

""" def classify_face2(distance, found_face, unknown_face):
    confidence = get_confidence_level(distance)

    if found_face.distance_to_human_classified == 0:
        if distance < Face.DISTANCE_MAYBE:
            assign_new_person(unknown_face, found_face.person)
            unknown_face.confidence_level = confidence
            unknown_face.confidence = distance.item()
            unknown_face.classified_by = Face.CLASSIFIER
            unknown_face.distance_to_human_classified = 1
            logger.debug("Found person classified by human; face %i is %s with confidence %f",
                         unknown_face.id, found_face.person.name, unknown_face.confidence)
            return True
    elif found_face.distance_to_human_classified == 1:
        if distance < Face.DISTANCE_SAFE:
            assign_new_person(unknown_face, found_face.person)
            unknown_face.confidence_level = confidence
            unknown_face.confidence = distance.item()
            unknown_face.classified_by = Face.CLASSIFIER
            unknown_face.distance_to_human_classified = 2
            logger.debug("Found person classified by classifier with distance 1 to human classified; face %i is %s with confidence %f",
                         unknown_face.id, found_face.person.name, unknown_face.confidence)
            return True

    elif found_face.distance_to_human_classified == 2:
        if distance < Face.DISTANCE_VERY_SAFE:
            assign_new_person(unknown_face, found_face.person)
            unknown_face.confidence_level = confidence
            unknown_face.confidence = distance.item()
            unknown_face.classified_by = Face.CLASSIFIER
            unknown_face.distance_to_human_classified = 3
            logger.debug("Found person classified by classifier with distance 2 to human classified; face %i is %s with confidence %f",
                         unknown_face.id, found_face.person.name, unknown_face.confidence)
            return True
 """
