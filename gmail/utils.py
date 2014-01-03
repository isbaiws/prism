def decode_str(s, encodings=('utf-8', 'gbk'), E=UnicodeDecodeError):
    """Try to decode a string in different ways(encodings), 
    raise a specific error(E) when decoding fails
    """
    if s is None:
        return u''
    if isinstance(s, unicode):
        return s
    # As test turns out, utf-8 is a stricter encoding than gbk
    # gbk can decode what is encoded by utf-8, versa not
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
            raise E("'%s' cannot be decoded by %s" % (s, encodings))

