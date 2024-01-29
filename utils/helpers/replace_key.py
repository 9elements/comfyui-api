def replace_key(json_obj, key, value):
    if key in json_obj:
        json_obj[key] = value
        return json_obj[key]
    for k, v in json_obj.items():
        if isinstance(v, dict):
            item = replace_key(v, key, value)
            if item is not None:
                item = value
                return item
    return None