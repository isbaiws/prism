import logging
from subprocess import Popen, PIPE, STDOUT, CalledProcessError

logger = logging.getLogger(__name__)

def read(fcontent, fname):
    if isinstance(fcontent, unicode):
        return fcontent
    try:
        return _read(fcontent, fname)
    except Exception as e:
        logger.info('Cannot read as doc, pdf, %s', e)
        try:
            # if left off, ascii will be the default encoding
            return unicode(fcontent, 'gbk') 
        except UnicodeDecodeError:
            logger.info('Not encoded in gbk')
            try:
                return unicode(fcontent, 'utf-8')
            except UnicodeDecodeError:
                logger.info('Not encoded in utf-8')
                logger.info('Return the raw binary')
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

