from subprocess import Popen, PIPE

#TODO refine your shit
def read(fc, fname):
    if fname.endswith(('doc', 'docx')):
        # stderr?
        p = Popen('catdoc', stdin=PIPE, stdout=PIPE, stderr=PIPE)
        p.stdin.write(fc)
        p.stdin.close()
        return p.stdout.read()
    return fc

if __name__ == '__main__':
    fn = '/tmp/test.doc'
    fc = open(fn, 'rb').read()
    print read(fc, fn)
