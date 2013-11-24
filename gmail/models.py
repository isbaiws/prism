import re
from email import message_from_file
from email.iterators import _structure
from email.header import decode_header

from pymongo import MongoClient
from bson.objectid import ObjectId
from prism import settings

client = MongoClient(settings.DB_HOST, settings.DB_PORT)
db = client.prism
email_db = db.email


# Match encoded-word strings in the form =?charset?q?Hello_World?=
# Some will surrend it by " or end by , or by fucking \r
ecre = re.compile(r"""=\?([^?]*?)\?([qb])\?(.*?)\?=(?=\W|$)""",
        re.VERBOSE | re.IGNORECASE | re.MULTILINE)

class Email(object):

    def __init__(self, fp):
        self.msg = message_from_file(fp)
        headers_undec = dict(self.msg.items())
        self.headers = self.flatten_header(headers_undec)
        self.body, self.txt_body = self.get_body()

    def flatten_header(self, hdr):
        for k, v in hdr.items():
            hdr[k] = ecre.sub(self.decode_match, v)
        return hdr

    def decode_match(self, field):
        dec_str, charset = decode_header(field.group(0))[0]
        if charset:
            dec_str = dec_str.decode(charset, 'replace')
        return dec_str

    def get_body(self):
        parts = []
        texts = []
        for part in self.msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get_content_maintype() == 'text':
                charset = part.get_content_charset('gbk')
                txt = part.get_payload(decode=True).decode(charset, 'replace')

                ct = '%s; charset=%s' % (part.get_content_type(), 'utf-8')
                parts.append({'content': txt, 'content-type': ct})
                texts.append(txt)
            else:
                part_dict = dict(part.items())
                part_dict['content'] = part.get_payload()
                parts.append(part_dict)
        return parts, texts

    def _structure(self):
        '''debugging tool'''
        print _structure(self.msg)

    def to_dict(self):
        '''can only used once'''
        self.headers.update({'body': self.body, 'txt_body': self.txt_body})
        return self.headers

    @classmethod
    def all(cls):
        return email_db.find()

    @classmethod
    def get(cls, _id):
        return email_db.find_one({'_id': ObjectId(_id)})

    def save(self):
        self._id = email_db.insert(self.to_dict())

