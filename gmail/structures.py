import collections
import pdb

class AttrDict(dict):
    """A wrapper of mongo doc, from minimongo"""

    def __init__(self, initial=None, **kwargs):
        # Make sure that during initialization, that we recursively apply
        # AttrDict.  Maybe this could be better done with the builtin
        # defaultdict?
        if initial:
            for key, value in initial.iteritems():
                # Can't just say self[k] = v here b/c of recursion.
                self.__setitem__(key, value)

        # Process the other arguments (assume they are also default values).
        # This is the same behavior as the regular dict constructor.
        for key, value in kwargs.iteritems():
            self.__setitem__(key, value)

        super(AttrDict, self).__init__()

    # These lines make this object behave both like a dict (x['y']) and like
    # an object (x.y).  We have to translate from KeyError to AttributeError
    # since model.undefined raises a KeyError and model['undefined'] raises
    # a KeyError.  we don't ever want __getattr__ to raise a KeyError, so we
    # 'translate' them below:
    def __getattr__(self, attr):
        try:
            return super(AttrDict, self).__getitem__(attr)
        except KeyError as excn:
            raise AttributeError(excn)

    def __setattr__(self, attr, value):
        try:
            # Okay to set directly here, because we're not recursing.
            self[attr] = value
        except KeyError as excn:
            raise AttributeError(excn)

    def __delattr__(self, key):
        try:
            return super(AttrDict, self).__delitem__(key)
        except KeyError as excn:
            raise AttributeError(excn)

    def __setitem__(self, key, value):
        # Coerce all nested dict-valued fields into AttrDicts
        new_value = value
        if isinstance(value, dict):
            new_value = AttrDict(value)
        return super(AttrDict, self).__setitem__(key, new_value)

class CaseInsensitiveDict(collections.MutableMapping):
    """
    A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``collections.MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive:

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.

    """
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        if isinstance(other, collections.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
         return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, dict(self.items()))

