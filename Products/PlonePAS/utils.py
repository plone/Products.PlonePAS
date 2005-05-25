def unique(iterable):
    d = {}
    for i in iterable:
        d[i] = None
    return d.keys()
