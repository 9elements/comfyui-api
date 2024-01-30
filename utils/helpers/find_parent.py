def find_parent_of_key(json_obj, key, parent=None):
    if key in json_obj:
        return parent
    for k, v in json_obj.items():
        if isinstance(v, dict):
            # Pass the current object as the parent for the next level of recursion
            parent_obj = find_parent_of_key(v, key, parent=json_obj)
            if parent_obj is not None:
                return parent_obj
    return None