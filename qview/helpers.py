def from_val(d=None, val=None):
    """
    Return a dictionary key from a value, for 'inverted' getting.
    :param d:
    :param val:
    :return:
    """
    return {val:key for key, val in d.items()}[val]