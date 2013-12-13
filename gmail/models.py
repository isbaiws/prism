#coding: utf-8
import monkey
import logging
import pdb
import re
from itertools import ifilter
from email import message_from_file, message_from_string
from email.header import decode_header

from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
import HTMLParser

from structures import AttrDict
import attachreader

logger = logging.getLogger(__name__)

# document_class is default class to use for documents returned from this client.
client = MongoClient(settings.DB_HOST, settings.DB_PORT, document_class=AttrDict)
db = client.prism
#TODO
db.fs.chunks.ensure_index('files_id')
gfs = gridfs.GridFS(db)

logger = logging.getLogger(__name__)
# Match encoded-word strings in the form =?charset?q?Hello_World?=
# Some will surrend it by " or end by , or by fucking \r
ecre = re.compile(r"""=\?([^?]*?)\?([qb])\?(.*?)\?=(?=\W|$)""",
        re.VERBOSE | re.IGNORECASE | re.MULTILINE)
# To remove line feeds in header
lfre = re.compile(r'\s*?[\r\n]+\s*', re.MULTILINE)

strip_html_entities = HTMLParser.HTMLParser().unescape

def to_unicode(s):
    if isinstance(s, unicode):
        return s
    try:
        return s.decode('gbk')
    except UnicodeDecodeError:
        return s.decode('utf-8')

def decode_str(str_enc):
    """Decode strings like =?charset?q?Hello_World?="""
    def decode_match(field):
        str_dec, charset = decode_header(field.group(0))[0]
        if charset:
            str_dec = str_dec.decode(charset, 'replace')
        return str_dec
    # if '\n' in str_enc:
    #     pdb.set_trace()
    return lfre.sub(' ', ecre.sub(decode_match, str_enc))

def analyze_header(msg):
    """Make keys lower case, filter out unneeded, etc.
    msg must be a email.message type"""
    vanilla_hdr = {}
    meta = {}

    for k, v in msg.items():
        k = k.lower()
        # Filter out those added by other gateways
        # if not k.startswith('x'):
        vanilla_hdr[k] = to_unicode(decode_str(v))
    #TODO
    # from, to, subject, date
    
    # Ensure there is a content-type key
    # if 'content-type' not in vanilla_hdr:
    # get_content_type() will return a default one, all in lower-case
    # used in multipart to choose the best alternative
    meta['content-type'] = msg.get_content_type()
    
    # if msg.get_filename():
    #     # for that default message handler
        # vanilla_hdr['filename'] = msg.get_filename()
    meta['filename'] = msg.get_filename(u'未命名.'+msg.get_content_subtype())

    vanilla_hdr.pop('content-disposition', None)
    #TODO not everyone need it
    # if 'content-disposition' not in vanilla_hdr and msg.get_filename():
    #     vanilla_hdr['content-disposition'] = msg.get_filename()
    # if 'content-disposition' in vanilla_hdr:
    #     print '+'*20, vanilla_hdr['content-disposition'] 
    return vanilla_hdr, meta

class MessageParse(object):
    multipart_alternatives = ['text/html', 'text/richtext', 'text/plain', 'message/rfc822']
    img_tmpl =  '<img border="0" hspace="0" align="baseline" src="%s" />'

    def parse(self, msg):
        maintype = msg.get_content_maintype()
        logger.debug('Got a %s to parse', msg.get_content_type())
        parser = getattr(self, 'parse_'+maintype, self.parse_other)
        return parser(msg)

    def prepare_email(self, msg):
        e = Email()
        e.header, e.meta = analyze_header(msg)
        return e

    def parse_text(self, msg):
        # assert msg.get_content_maintype() == 'text'
        e = self.prepare_email(msg)
        charset = msg.get_content_charset('gbk')  # gbk will be the default one
        e.body = msg.get_payload(decode=True).decode(charset, 'replace')
        return e

    def parse_image(self, msg):
        assert msg.get_content_maintype() == 'image'
        e = self.prepare_email(msg)
        img_id = gfs.put(msg.get_payload(decode=True), header=e.header)
        e.resources.append(img_id)
        e.body = self.img_tmpl % reverse('resource', args=(img_id, ))
        return e

    def parse_application(self, msg):
        assert msg.get_content_maintype() == 'application'
        e = self.prepare_email(msg)
        content = msg.get_payload(decode=True)
        app_id = gfs.put(content, header=e.header)
        e.resources.append(app_id)
        # e.body = ''
        e.attachments = [{'filename':e.meta['filename'],
            'url': reverse('resource', args=(app_id,))}]
        e.attach_txt = attachreader.read(content, e.meta['filename'])
        return e

    def parse_multipart(self, msg):
        assert msg.get_content_maintype() == 'multipart'
        outer_email = self.prepare_email(msg)
        sub_emails = map(self.parse, msg.get_payload())

        # Each of the parts is an "alternative" version of the same information.
        if msg.get_content_subtype() == 'alternative':
            for ct in self.multipart_alternatives:
                # There must be a content-type, just in case
                best = next(ifilter(lambda e: e.meta.get \
                    ('content-type', '').startswith(ct), sub_emails), None)
                if best:
                    break
            else:
                # the last one means the richest, but maybe I donnot know
                # how to interpret, so just get the first one
                best = sub_emails[0]
            # We still need your header, but donot overwrite headers I already have
            best.header.update({k: v for k, v in outer_email.header.items()
                if k not in best.header})
            best.meta.update({k: v for k, v in outer_email.meta.items()
                if k not in best.meta})
            return best
        else:
            bodies = []
            attach_txts = []
            for sub_email in sub_emails:
                bodies.append(sub_email.body)
                outer_email.attachments.extend(sub_email.attachments)
                attach_txts.append(sub_email.attach_txt)
                outer_email.resources.extend(sub_email.resources)

            outer_email.body = '<br />'.join(bodies)
            outer_email.attach_txt = ' '.join(attach_txts)
            return outer_email

    def parse_other(self, msg):
        # assert msg.get_content_maintype() == 'application'
        e = self.prepare_email(msg)
        content = msg.get_payload(decode=True)
        app_id = gfs.put(content, header=e.header)
        e.resources.append(app_id)
        # e.body = ''
        e.attachments = [{'filename':e.meta['filename'],
            'url': reverse('resource', args=(app_id,))}]
        e.attach_txt = attachreader.read(content, e.meta['filename'])
        return e

mp = MessageParse()


emails = db.email
class Email(object):
    id = None
    header = {}
    meta = {}
    body = ''
    body_txt = ''
    attachments = []
    attach_txt = ''
    resources = []  # to find resources when deleting this doc

    @classmethod
    def from_fp(cls, fp):
        # id = ObjectId(id)  # fetch one if not exist
        # May raise MessageParseError, I catch it in the view
        msg = message_from_file(fp)
        return mp.parse(msg)

    def to_dict(self):
        # Just return things that is set on this INSTANCE
        d = self.__dict__
        # return {k: v for k, v in d.items() if v}
        return {'header': self.header, 'meta': self.meta,
                'body': self.body, 'body_txt': self.body_txt,
                'attachments': self.attachments, 'attach_txt': self.attach_txt,
                'resources': self.resources}

    def save(self):
        self.id = emails.insert(self.to_dict())
        return self.id

    @classmethod
    def find(cls, **selector):
        # return map(from_dict, emails.find(selector))
        # Just return raw data, no need to wrap them
        return emails.find(selector)

    @classmethod
    def remove(cls, id_str):
        if ObjectId.is_valid(id_str):
            e_dict = cls.find_one({'_id': ObjectId(id_str)})
            for rid_str in e_dict.get('resources', []):
                gfs.delete(ObjectId(rid_str))
            return emails.remove(ObjectId(id_str))
        return None

    @classmethod
    def find_one(cls, selector):
        return emails.find_one(selector)

