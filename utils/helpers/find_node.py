def find_node(json_obj, key):
    if key in json_obj:
        return json_obj[key]
    for k, v in json_obj.items():
        if isinstance(v, dict):
            item = find_node(v, key)
            if item is not None:
                return item
    return None