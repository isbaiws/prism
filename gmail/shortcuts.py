from bson.objectid import ObjectId
from errors import ObjectDoesNotExist
from models import Email, gfs

def get_email_or_404(id_str):
    if not ObjectId.is_valid(id_str):
        raise ObjectDoesNotExist()
    email = Email.find_one({'_id': ObjectId(id_str)})
    if not email:
        raise ObjectDoesNotExist()
    return email

def get_resource_or_404(id_str):
    if not ObjectId.is_valid(id_str):
        raise ObjectDoesNotExist()
    id = ObjectId(id_str)
    if not gfs.exists(id):
        raise ObjectDoesNotExist()
    return gfs.get(id)

