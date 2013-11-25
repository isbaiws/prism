import re
from itertools import ifilter
from email import message_from_file
from email.iterators import _structure
from email.header import decode_header

from pymongo import MongoClient
from bson.objectid import ObjectId
from django.conf import settings

client = MongoClient(settings.DB_HOST, settings.DB_PORT)
db = client.prism
email_db = db.email


# Match encoded-word strings in the form =?charset?q?Hello_World?=
# Some will surrend it by " or end by , or by fucking \r
ecre = re.compile(r"""=\?([^?]*?)\?([qb])\?(.*?)\?=(?=\W|$)""",
        re.VERBOSE | re.IGNORECASE | re.MULTILINE)

class Email(object):
    headers = body = txt_body = None

    def __init__(self, fp):
        msg = message_from_file(fp)
        headers_undec = dict(msg.items())
        self.headers = self.flatten_header(headers_undec)
        self.body = self.route_handler(msg)

    def flatten_header(self, hdr):
        def decode_match(field):
            dec_str, charset = decode_header(field.group(0))[0]
            if charset:
                dec_str = dec_str.decode(charset, 'replace')
            return dec_str

        for k, v in hdr.items():
            hdr[k] = ecre.sub(decode_match, v)
        return hdr

    def route_handler(self, msg):
        handler = 'handle_' + msg.get_content_maintype()
        if hasattr(self, handler):
            return getattr(self, handler)(msg)
        else:
            return self.handle_default(msg)

    def handle_multipart(self, msg):
        assert msg.is_multipart(), "Who send you here while you ain't multipart?"
        # Look for text/html first and then text/plain, best comes first
        options = ['text/html', 'text/plain', 'message/rfc822']

        sub_msg_dicts = []
        for sub_msg in msg.get_payload():
            sub_msg_dicts.extend(self.route_handler(sub_msg))

        # Each of the parts is an "alternative" version of the same information.
        if msg.get_content_subtype() == 'alternative':
            for ct in options:
                best = next(ifilter(lambda d: 
                    d['content-type'].startswith(ct), sub_msg_dicts), None)
                if best:
                    sub_msg_dicts = [best]
                    break
            else:
                # Choose the first one
                sub_msg_dicts = sub_msg_dicts[0:1]

        return sub_msg_dicts
    
    def handle_text(self, msg):
        # assert msg.get_content_maintype() == 'text'
        charset = msg.get_content_charset('gbk')  # gbk will be the default one
        txt = msg.get_payload(decode=True).decode(charset, 'replace')

        # Actually it's useless, but we need a unified way to express body-structure
        ct = '%s; charset=%s' % (msg.get_content_type(), 'utf-8')
        # All lower case
        return [{'content': txt, 'content-type': ct}]
    # In multipart/digest the default Content-Type value for a body part 
    # is changed from "text/plain" to "message/rfc822".
    handle_message = handle_text

    def handle_default(self, msg):
        assert not msg.is_multipart()
        part = dict(msg.items())
        part['body'] = msg.get_payload()
        return [part]

    def _structure(self):
        '''debugging tool'''
        print _structure(self.msg)

    def to_dict(self):
        '''can only used once'''
        self.headers.update({'body': self.body, '_txt_body': self.txt_body})
        return self.headers

    @classmethod
    def all(cls):
        return email_db.find()

    @classmethod
    def get(cls, _id):
        return email_db.find_one({'_id': ObjectId(_id)})

    @classmethod
    def remove(cls, _id):
        return email_db.remove({'_id': ObjectId(_id)})

    def save(self):
        self._id = email_db.insert(self.to_dict())

