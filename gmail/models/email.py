#coding: utf-8
# import monkey
from __future__ import absolute_import
import logging
import ipdb
import re
from json import dumps
from datetime import datetime
from time import mktime
from itertools import ifilter
from email import message_from_file, message, message_from_string
from email.header import decode_header
from email.utils import mktime_tz, parsedate
from email import _parseaddr
from bson.objectid import ObjectId

from django.core.urlresolvers import reverse
from mongoengine import (
        Document, StringField, ListField, FileField, DateTimeField,
        GridFSProxy, ReferenceField, NULLIFY, QuerySet, Q,
        EmbeddedDocument, EmbeddedDocumentField,
    )
# from jieba import cut_for_search

from gmail.errors import MessageParseError
from gmail.HTMLtoText import html2text
from gmail.utils import decode_str, parse_input_datetime, build_content_disposition
from gmail import attachreader
from gmail.utils import MyJsonEncoder
from .user import User
from .group import Group

logger = logging.getLogger(__name__)

# Match encoded-word strings in the form =?charset?q?Hello_World?=
# Some will surrend it by " or end by , or by fucking \r
ecpatt = re.compile(r"""=\?([^?]*?)\?([qb])\?(.*?)\?=(?=\W|$)""",
        re.VERBOSE | re.IGNORECASE | re.MULTILINE)
# To remove line feeds in header
lfpatt = re.compile(r';\s*?[\r\n]+\s*')
# There are some bad guys who just split headers
lfpatt_bad = re.compile(r'\s*?[\r\n]+\s*')

ip_patt = re.compile(r'\b(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\b')
datetime_patt = re.compile(r'\b(:?%s), \d{2} (?:%s) \d{4} \d{2}:\d{2}:\d{2} (?:\+|-)\d{4}\b' % 
        ('|'.join(_parseaddr._daynames), '|'.join(_parseaddr._monthnames)), re.I)

def decode_rfc2047(str_enc):
    """Decode strings like =?charset?q?Hello_World?="""
    def decode_match(field):
        str_dec, charset = decode_header(field.group(0))[0]
        if charset:
            str_dec = str_dec.decode(charset, 'replace')
        return str_dec
    one_line = lfpatt_bad.sub('', lfpatt.sub('; ', str_enc))
    ret_str = ecpatt.sub(decode_match, one_line)
    return decode_str(ret_str, E=MessageParseError)  # ensure unicode

def get_email_info(msg):
    """Make keys lower case, filter out unneeded, etc.
    msg must be a email.message type"""
    ip = []
    possible_date = []
    info = {}
    find_all_ips = lambda s: map(lambda m: m.group(), ip_patt.finditer(s))
    # Not now
    # parse_datetime = lambda s: datetime.utcfromtimestamp(mktime_tz(parsedate_tz(s)))
    parse_datetime = lambda s: datetime.utcfromtimestamp(mktime(parsedate(s)))
    listlize_addresses = lambda ads:[ad.strip() for ad in ads.split(',')]

    if not isinstance(msg, message.Message):
        raise TypeError('How dare you to pass me a %s, I want a message instance!'
                % msg.__class__.__name__)

    for k, v in msg.items():
        k = k.lower().replace('-', '_')  # to be a valid identifier
        # Make sure to be unicode, or die with MessageParseError
        # some agents send header with non-ascii chars
        v = decode_rfc2047(v)

        ip.extend(find_all_ips(v))
        datetime_mat = datetime_patt.search(v)
        if datetime_mat:
            possible_date.append(datetime_mat.group())

        info[k] = v
    # from is a keyword in python, escape it to from_
    info['ip'] = ip

    # I pop date to be filled later or by other function(when missing)
    datetime_mat = datetime_patt.search(info.pop('date', ''))
    # In some cases, date is in the form of 2009-04-02 04:52:08
    if not datetime_mat:
        if possible_date:
            info['date'] = min(map(parse_datetime, possible_date))
    else:
        info['date'] = parse_datetime(datetime_mat.group())

    if 'from' in info:
        info['from_'] = info['from']

    for ad in ('from_', 'to'):
        if ad in info:
            info[ad] = listlize_addresses(info[ad])
    
    # Ensure there is a content-type key, if 'content-type' not in vanilla_hdr
    # get_content_type() will return a default one, all in lower-case
    # used in multipart to choose the best alternative
    info['content_type'] = msg.get_content_type()
    
    if msg.get_filename():
        info['filename'] = decode_rfc2047(msg.get_filename())
        if 'content_disposition' in info:
            # Override with the standard one
            info['content_disposition'] = build_content_disposition(info['filename'])

    return info

class MessageParse(object):
    multipart_alternatives = [ 'message/rfc822', 'text/html', 'text/richtext', 'text/plain',]
    img_tmpl =  '<img border="0" hspace="0" align="baseline" src="%s" />'

    def parse(self, msg):
        if msg.defects:  # when a defect is found
            raise MessageParseError(' '.join(
                defect.__doc__ for defect in msg.defects))
        # message/rfc822 is an multipart
        if msg.is_multipart():
            return self.parse_multipart(msg)
        maintype = msg.get_content_maintype()
        logger.debug('Get a %s to parse', msg.get_content_type())
        parser = getattr(self, 'parse_'+maintype, self.parse_other)
        return parser(msg)

    def prepare_email(self, msg):
        e = Email()
        info = get_email_info(msg)
        e.update(info)
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
        img = store_resoure(msg.get_payload(decode=True), **e.to_dict())
        #TODO, strip out filename, otherwise it will be searched as attachment
        e.resources.append(img)
        e.body = self.img_tmpl % img.url
        return e

    def parse_application(self, msg):
        # assert msg.get_content_maintype() == 'application'
        e = self.prepare_email(msg)
        content = msg.get_payload(decode=True)
        app = store_resoure(content, **e.to_dict())
        e.resources.append(app)
        # e.body = ''
        e.attachments.append(app)
        e.attach_txt = attachreader.read(content, e.filename)
        return e

    def parse_multipart(self, msg):
        # assert msg.get_content_maintype() == 'multipart'
        outer_email = self.prepare_email(msg)
        sub_emails = map(self.parse, msg.get_payload())

        # Each of the parts is an "alternative" version of the same information.
        if msg.get_content_subtype() == 'alternative':
            for ct in self.multipart_alternatives:
                # There must be a content-type, just in case
                best = next(ifilter(lambda e: e.content_type and
                    e.content_type.startswith(ct), sub_emails), None)
                if best:
                    break
            else:
                # the last one means the richest, but maybe I donnot know
                # how to interpret, so just get the first one
                best = sub_emails[0]
            # We still need your header, but donot overwrite headers I already have
            best.update({k: v for k, v in outer_email.to_dict().items()
                if v and not best[k]})
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
            outer_email.attach_txt = '\n'.join(attach_txts)
            return outer_email

    def parse_other(self, msg):
        logger.warning('Get an unknown msg type: %s', msg.get_content_type())
        return self.parse_application(msg)

mp = MessageParse()

class WhoseQuerySet(QuerySet):
    def owned_by(self, user):
        if user.is_superuser:
            return self
        groups_in_charge = Group.objects(managers=user.id)
        users_in_charge = User.objects(groups__in=groups_in_charge)
        return self.filter(owner__in=[user]+list(users_in_charge))

    def under(self, folder):
        return self.filter(folder=folder)

class Resource(EmbeddedDocument):
    gridfs = FileField()
    # Store filename outside, so it can be searched
    filename = StringField(default='')

    # DONOT store things in __init__, it will be called when constructing
    # Document, thus leads to endless storing in GridFS
    # def __init__(self, content, filename=None, content_type=None, 
    #         content_disposition=None, **kwargs):
    #     http_meta = {}
    #     if content_type:
    #         http_meta['content_type'] = content_type
    #     if content_disposition:
    #         http_meta['content_disposition'] = content_disposition
    #     resc = GridFSProxy()
    #     # Store there for resource view
    #     resc.put(content, **http_meta)
    #     return super(Resource, self).__init__(gridfs=resc,
    #             filename=filename, **kwargs)
    #
    @property
    def id(self):
        return self.gridfs.grid_id

    @property
    def url(self):
        return reverse('resource', args=(self.gridfs.grid_id, ))

    def delete(self):
        return self.gridfs.delete()

    def __unicode__(self):
        return self.filename

def store_resoure(content, filename=None, content_type=None, 
        content_disposition=None, **kwargs):
    """A helper to create Resource instance"""
    http_meta = {}
    if content_type:
        http_meta['content_type'] = content_type
    if content_disposition:
        http_meta['content_disposition'] = content_disposition
    resc = GridFSProxy()
    # Store there for resource view
    resc.put(content, **http_meta)
    return Resource(gridfs=resc,
            filename=filename, **kwargs)

class Email(Document):
    # Every attr is present
    subject = StringField(default='')
    from_ = ListField(StringField(), default=list)
    to = ListField(StringField(), default=list)
    cc = StringField(default='')
    bcc = StringField(default='')
    ip = ListField(StringField(), default=list)
    content_type = StringField(default='')
    filename = StringField(default='')
    content_disposition = StringField(default='')
    date = DateTimeField()

    body = StringField(default='')
    body_txt = StringField(default='')
    # Pitty I cannot customize FileField
    attachments = ListField(EmbeddedDocumentField(Resource), default=list)
    attach_txt = StringField(default='')
    # to find resources when deleting this doc
    resources = ListField(EmbeddedDocumentField(Resource), default=list)

    owner = ReferenceField(User, reverse_delete_rule=NULLIFY)
    folder = StringField(default='')
    source = EmbeddedDocumentField(Resource)

    meta = {
        'indexes': ['owner', 'folder', 'date'],
        'ordering': ['-date'],
        'queryset_class': WhoseQuerySet,
    }

    def update(self, d):
        # self._data.update(d)
        for k, v in d.items():
            setattr(self, k, v)

    def to_dict(self):
        # I donot wanna store empty fields
        return {k: v for k, v in self._data.items() if v}

    @classmethod
    def from_fp(cls, fp):
        # id = ObjectId(id)  # fetch one if not exist
        # May raise MessageParseError, I catch it in the view
        msg = message_from_file(fp)
        return mp.parse(msg)

    @classmethod
    def from_string(cls, s):
        msg = message_from_string(s)
        e_mei_er =  mp.parse(msg)
        e_mei_er.source = store_resoure(s, 
                content_disposition=build_content_disposition(e_mei_er.subject+'.eml'),
                content_type='message/rfc822',
                filename=e_mei_er.subject+'.eml')
        return e_mei_er

    def clean(self):
        # I cannot set as a default in field definition,
        # because it ONLY exist in the outer email
        if not self.date:
            self.date = datetime.utcnow()
        self._data = self.to_dict()
        #TODO, what a good idea to use None as default!
        #FIXME, I cannot pass a None to HTMLParser
        self.body_txt = html2text(self.body or '')

    def save(self):
        super(Email, self).save(write_concern={'w': 0})
    
    # @classmethod
    # def owned_by(cls, user):
    #     return cls.objects.filter(owner=user)

    @classmethod
    def find(cls, query_dict):
        equal_queries = ('ip',)
        string_queries = ('from_', 'to', 'subject', 'body_txt', 'attach_txt', 'bcc', 'cc')
        query = Q()
        q_str = query_dict.get('q', '')

        for k in string_queries:
            if query_dict.get(k):
                # No need to re.escape, mongoengine escape it for us
                query |= Q(**{'%s__contains' % k: q_str})

        for k in equal_queries:
            if query_dict.get(k):
                query |= Q(**{k: q_str})

        if query_dict.get('folder'):
            query &= Q(folder=query_dict['folder'])

        if query_dict.get('attach_filename'):
            query |= Q(attachments__filename__contains=q_str)

        if query_dict.get('start'):
            query &= Q(date__gte=query_dict['start'])
        if query_dict.get('end'):
            query &= Q(date__lte=query_dict['end'])
        logger.info('Query: %s', dumps(query.to_query(cls), cls=MyJsonEncoder))
        return cls.objects(query)

    def delete(self):
        # Won't raise anything if not found?
        super(Email, self).delete()
        # attachments will be converted to None not []
        for atta in self.attachments or []:
            atta.delete()
        # if self.resources:
        for resc in self.resources or []:
            resc.delete()
        self.source.delete()

    def has_perm(self, user, whatever):
        if user.is_superuser or self.owner.id == user.id:
            return True
        for group in self.owner.groups:
            if user in group.managers:
                return True
        return False

    @classmethod
    def get_by_id(cls, eid):
        if not eid:  # None is a valid objectid?
            return False
        if ObjectId.is_valid(eid):
            return cls.objects(id=eid).first()
        return False
