def decode_str(s, encodings=('gbk', 'utf-8'), errors='strict', E=UnicodeDecodeError):
    """Try to decode a string in different ways(encodings), 
    raise a specific error(E) when decoding fails
    """
    if isinstance(s, unicode):
        return s
    for encoding in encodings:
        try:
            return s.decode(encoding, errors)
        except UnicodeDecodeError:
            pass
    raise E("'%s' cannot be decoded by any of %s" % (s, encodings))

