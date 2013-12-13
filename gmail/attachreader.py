import logging
from subprocess import Popen, PIPE, STDOUT, CalledProcessError

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

