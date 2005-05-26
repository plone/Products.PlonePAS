"""
$Id: utils.py,v 1.3 2005/05/26 01:32:47 dreamcatcher Exp $
"""

def unique(iterable):
    d = {}
    for i in iterable:
        d[i] = None
    return d.keys()
