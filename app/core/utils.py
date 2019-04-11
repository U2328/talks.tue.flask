__all__ = (
    'make_unique',
)


# because sets rely on hashing, rather than equality by value...
def make_unique(iterable):
    vals = []
    for val in iterable:
        if val not in vals:
            vals.append(val)
    return vals
