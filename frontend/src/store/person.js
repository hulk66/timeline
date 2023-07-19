import axios from "axios";
export const person = {
    state: {
        newFaces: false,
        persons: [],
        allPersons: [],
        knownPersons: [],
        unknownFaces: [],
        recentFaces: [],
        facesToConfirm: [],
        markMode: false,
        previewHeight: 100,

    },

    mutations: {
        setNewFaces(state, v) {
            state.newFaces = v;
        },

        setAllPersons(state, all) {
            state.allPersons = all;
        },
        setPersons(state, all) {
            state.persons = all;
        },
        setKnownPersons(state, known) {
            state.knownPersons = known;
        },
        setUnknownFaces(state, unknown) {
            state.unknownFaces = unknown;
        },
        setRecentFaces(state, recent) {
            state.recentFaces = recent;
        },
        setFacesToConfirm(state, unknown) {
            state.facesToConfirm = unknown;
        },

        markMode(state, v) {
            state.markMode = v;
        },

        setPreviewHeight(state, v) {
            state.previewHeight = v;
        }
    },

    actions: {

        setRating(context, {photo, stars}) {
            let url = `/api/asset/setRating/${photo.id}/${stars}`;
            return new Promise((resolve => {
                axios.get(url).then( result => {
                    resolve(result.data);
                })
            }))

        },

        ignoreFace(context, face) {
            let url = `/api/face/ignore/${face.id}`;
            return new Promise((resolve => {
                axios.get(url).then( result => {
                    resolve(result.data);
                })
            }))

        },
        getClosestPerson(context, face) {
            let url = `/api/face/nearestKnownFaces/${face.id}`
            return new Promise((resolve => {
                axios.get(url).then( result => {
                    resolve(result.data);
                })
            }))

        },
        forgetPerson(context, person) {
            let url = `/api/person/forget/${person.id}`
            return new Promise((resolve => {
                axios.get(url).then( result => {
                    resolve(result.data);
                })
            }))
        },

        ignoreUnknownPerson(context, person) {
            let url = `/api/person/ignore_unknown_person/${person.id}`
            return new Promise((resolve => {
                axios.get(url).then( result => {
                    resolve(result.data);
                })
            }))
        },

        getAllUnknownFaces(context, {page, size}) {
            let url = `/api/face/allUnknownAndClosest/${page}/${size}`;
            axios.get(url).then( result => {
                context.commit("setUnknownFaces", result.data);    
            })
            
        },

        getRecentFaces(context, {page, size}) {
            let url = `/api/face/recent/${page}/${size}`;
            axios.get(url).then( result => {
                context.commit("setRecentFaces", result.data);    
            })
            
        },

        getFacesToConfirm(context, {page, size}) {
            let url = `/api/face/facesToConfirm/${page}/${size}`;
            axios.get(url).then( result => {
                context.commit("setFacesToConfirm", result.data);    
            })
        },

        assignFaceToPerson(context, { person, name, faceId }) {
            let pid = null;
            if (person)
                pid = person.id;
            return new Promise((resolve => {
                axios.post("/api/face/assign_face_to_person", {
                    personId: pid,
                    name: name,
                    faceId: faceId,
                }).then( result => {
                    resolve(result.data);
                })
            }))

        },

        mergePerson(context, {src_person, target_person}) {
            let url = `/api/person/merge/${src_person.id}/${target_person.id}`;
            return new Promise((resolve) => {
                axios.get(url).then( result => {
                    resolve(result.data);
                })
            });

        },

        renamePerson(context, {person, name}) {
            return new Promise((resolve) => {
                axios.post("/api/person/rename", {
                    personId: person.id,
                    name: name
                }).then( result => {
                    resolve(result.data);
                })
            });

        },
        /*
        getKnownPersons() {
            return new Promise((resolve => {
                axios.get("/api/person/known").then (result => {
                    resolve(result.data)
                })
            }))
        },
        */
        getKnownPersons(context) {
            axios.get("/api/person/known").then (result => {
                context.commit("setKnownPersons", result.data);    
            });
        },

        getAllPersons(context) {
            axios.get("/api/person/all").then (result => {
                context.commit("setAllPersons", result.data);
            });
        },

        getPersons(context, {page, size}) {
            let url = `/api/person/${page}/${size}`;
            axios.get(url).then( result => {
                context.commit("setPersons", result.data);    
            })
        },

        getPersonsByPhoto(context, photo) {
            return new Promise((resolve => {
                axios.get("/api/person/by_asset/" + photo.id).then((result) =>{
                    resolve(result.data);
                })
            }))
        },
        getFacesByPhoto(context, photo) {
            return new Promise((resolve => {
                axios.get("/api/face/by_asset/" + photo.id).then((result) =>{
                    resolve(result.data);
                })
            }))
        },
        getExifForPhoto(context, photo) {
            return new Promise((resolve => {
                axios.get("/api/asset/exif/" + photo.id).then((result) =>{
                    resolve(result.data);
                })
            }))
        },

        getGpsForPhoto(context, photo) {
            return new Promise((resolve => {
                axios.get("/api/asset/gps/" + photo.id).then((result) =>{
                    resolve(result.data);
                })
            }))
        },

        getThingsForPhoto(context, photo) {
            return new Promise((resolve => {
                axios.get("/api/asset/things/" + photo.id).then((result) =>{
                    resolve(result.data);
                })
            }))
        },

        getUnknownFaces(context, index) {
            return new Promise((resolve => {

                axios.get("/api/cluster/faces/" + index).then((result) => {
                    resolve(result.data);
                })
            }))
        },

    }
}
  