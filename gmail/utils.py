def decode_str(s, encodings=('gbk', 'utf-8'), E=UnicodeDecodeError):
    """Try to decode a string in different ways(encodings), 
    raise a specific error(E) when decoding fails
    """
    if s is None:
        return u''
    if isinstance(s, unicode):
        return s
    if isinstance(encodings, tuple):
        for encoding in encodings:
            try:
                return s.decode(encoding)
            except UnicodeDecodeError:
                pass
        raise E("'%s' cannot be decoded by any of %s" % (s, encodings))
    else:
        try:
            return s.decode(encodings)
        except UnicodeDecodeError:
            pass
        raise E("'%s' cannot be decoded by %s" % (s, encodings))

