from pymongo.cursor import Cursor

# Cursor object now have a len method 
# used in pagination
# Cursor.__len__ = lambda self: self.count(with_limit_and_skip=True)

_next = Cursor.next
def normalize_id(self):
    doc = _next(self)
    # Sometimes it may query otherthings such as db info
    if '_id' in doc:
        doc['id'] = doc['_id']
    return doc

Cursor.next = normalize_id

_get_item = Cursor.__getitem__
def get_item(self, index):
    if isinstance(index, slice):
        return [self[i] for i in range(index.start, index.stop)]
    return _get_item(self, index)
Cursor.__getitem__ = get_item

