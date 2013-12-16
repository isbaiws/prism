import logging
from subprocess import Popen, PIPE, STDOUT, CalledProcessError

from xlrd import open_workbook
from utils import decode_str

logger = logging.getLogger(__name__)

def read(fcontent, fname):
    if isinstance(fcontent, unicode):
        return fcontent
    try:
        return _read(fcontent, fname)
    except Exception as e:
        logger.info('Cannot read as doc, pdf, %s', e)
        try:
            return decode_str(fcontent)
        except UnicodeDecodeError:
            logger.info('Dunno whats inside the attachment')
            return ''

#TODO refine your shit
def _read(fcontent, fname):
    if fname.endswith(('doc', 'docx')):
        return pread('catdoc', fcontent)
    elif fname.endswith('pdf'):
        return pread(['pdftotext', '-', '-'], fcontent)
    elif fname.endswith(('xls', 'xlsx')):
        return read_xls(fcontent)
    raise Exception('Not any of them')

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
    wb = open_workbook(file_contents=fcontent, encoding_override='gbk')
    for sheet in wb.sheets():
        for irow in range(sheet.nrows):
            for icol in range(sheet.ncols):
                cell = sheet.cell(irow, icol)
                if cell.ctype:
                    values.append(unicode(cell.value))
    return '\t'.join(values)

