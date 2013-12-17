import logging
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
from SimpleHTTPServer import SimpleHTTPRequestHandler

from xlrd import open_workbook
from utils import decode_str

logger = logging.getLogger(__name__)

class Guesser(SimpleHTTPRequestHandler):
    def __init__(self):
        pass # We only need the instance, never care about others

    def __call__(self, fname):
        return self.guess_type(fname)

guess_type = Guesser()

def read(fcontent, fname):
    if isinstance(fcontent, unicode):
        return fcontent

    elif guess_type(fname).startswith('text'):  # is text
        try:
            return decode_str(fcontent)
        except UnicodeDecodeError:
            logger.info('This attachment "%s" claims to be a text, but I cannot decode it', fname)

    else:
        try:
            if fname.endswith(('doc', 'docx')):
                return pread('catdoc', fcontent)
            elif fname.endswith('pdf'):
                return pread(['pdftotext', '-', '-'], fcontent)
            elif fname.endswith(('xls', 'xlsx')):
                return read_xls(fcontent)
            logger.info('Have no idea whats inside %s', fname)
        except Exception as e:
            logger.info(e)
    return ''

def pread(cmd, input):
        # Don't redirect stderr to a PIPE when you're not reading it.
        proc = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        # proc.stdin.write(fcontent)
        # proc.stdin.close()
        # return proc.stdout.read()
        output, unused_err = proc.communicate(input)
        retcode = proc.returncode
        if retcode:
            raise CalledProcessError(retcode, cmd, output)
        return output

def read_xls(fcontent):
    values = []
    # encoding_override
    # Used to overcome missing or bad codepage information in older-version files.
    # From Excel 97 onwards, unicode is default, no worries
    # Doc: http://www.lexicon.net/sjmachin/xlrd.html
    wb = open_workbook(file_contents=fcontent, encoding_override='gbk')
    for sheet in wb.sheets():
        for irow in range(sheet.nrows):
            for icol in range(sheet.ncols):
                cell = sheet.cell(irow, icol)
                # 0 means XL_CELL_EMPTY
                if cell.ctype and unicode(cell.value).strip():
                    values.append(unicode(cell.value))
    return '\t'.join(values)

