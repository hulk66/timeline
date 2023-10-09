from timeline.domain import Tag


def parse_tags(tags_str: str):
    tags = tags_str.lower().split(",")
    return tags


def find_new_tags(tags_to_add, current_tags, all_available_tags):
    available_tags = tags_to_str(all_available_tags)
    new_tags = [tag for tag in tags_to_add if tag not in current_tags]
    tags_to_create = [tag for tag in new_tags if tag not in available_tags]
    available_tags = [tag for tag in all_available_tags if tag.name in tags_to_add]
    return (new_tags, tags_to_create, available_tags)


def _find_or_create_tag(tags_to_add, current_tags, registered_tags):
    new_tags = [tag for tag in tags_to_add if tag not in current_tags]
    tags_to_create = [tag for tag in new_tags if tag not in registered_tags]
    registered_tags = [tag for tag in current_tags if tag.name in new_tags]
    return (new_tags, tags_to_create, registered_tags)


def tags_to_str(tags: Tag):
    return [tag.name for tag in tags]
