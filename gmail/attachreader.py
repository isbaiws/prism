from subprocess import Popen, PIPE, STDOUT, CalledProcessError
from bson import Binary

def read(fcontent, fname):
    if isinstance(fcontent, unicode):
        return fcontent
    try:
        return _read(fcontent, fname)
    except Exception as e:
        # need a logger
        print '+'*20, e
        try:
            # if left off, ascii will be the default encoding
            return unicode(fcontent, 'gbk') 
        except UnicodeDecodeError:
            try:
                return unicode(fcontent, 'utf-8')
            except Exception as e:
                print e
                return Binary(fcontent)

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

if __name__ == '__main__':
    fn = '/tmp/goo.txt'
    fc = open(fn, 'rb').read()
    print read(fc, fn)
