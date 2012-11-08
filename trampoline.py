# -*- Mode: Python -*-

import ast
import sys
from transform import *

class trampoline (transformer):

    def invoke_continuation (self, name, dead=False):
        if dead:
            return dead_cont (lambda: Call ('schedule', [name], NullCont))
        else:
            return make_cont (lambda var: Call ('schedule', [name, var], NullCont))

def dofile (path):
    import os
    cps = transform (path, trampoline)
    base, ext = os.path.splitext (path)
    fout = open (base + '.cps.py', 'wb')
    fout.write (b'\nfrom scheduler import schedule, run\n\n')
    w = writer (fout)
    cps.emit_all (w)
    fout.write (b'\nrun()\n')
    fout.close()

if __name__ == '__main__':
    for path in sys.argv[1:]:
        dofile (path)
