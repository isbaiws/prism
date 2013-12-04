from subprocess import Popen, PIPE, STDOUT
from bson import Binary

def read(fcontent, fname):
    try:
        return _read(fcontent, fname)
    except Exception as e:
        # need a logger
        print e
        try:
            return unicode(fcontent)
        except Exception as e:
            print e
            return Binary(fcontent)

#TODO refine your shit
def _read(fcontent, fname):
    if fname.endswith(('doc', 'docx')):
        # Don't redirect stderr to a PIPE when you're not reading it.
        p = Popen('catdoc', stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        p.stdin.write(fcontent)
        p.stdin.close()
        return p.stdout.read()
    elif fname.endswith('pdf'):
        # Don't redirect stderr to a PIPE when you're not reading it.
        p = Popen(['pdftotext', '-', '-'], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        p.stdin.write(fcontent)
        p.stdin.close()
        return p.stdout.read()
    return fc

if __name__ == '__main__':
    fn = '/tmp/t.pdf'
    fc = open(fn, 'rb').read()
    print read(fc, fn)
