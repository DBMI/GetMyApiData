def join_headers(h1: list, h2: list) -> list:
    if h1 is None:
        if h2 is None:
            return []
        else:
            return h2
    if h2 is None:
        return h1

    set1 = set(h1)
    set2 = set(h2)
    combined = set1 | set2
    return list(combined)


def make_header(dict1: dict) -> list:
    ret = []

    for key in dict1.keys():
        ret.append(key)

    return ret
