if val is None:
    return 0
elif isinstance(val, int) or isinstance(val, float):
    return int(val)
else:
    if not isinstance(val, basestring):
        val = unicode(val)
    val = re.match(r'[\+-]?[0-9\.]*', val.strip()).group(0)
    if not val:
        return 0
    else:
        return int(val)
