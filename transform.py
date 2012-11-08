# -*- Mode: Python -*-

import ast
# this is the unparse module from Python/Tools/parser/unparse.py
import unparse

# what: continuation-passing style (CPS) transform for Python AST.
# why: might be useful to code against event-driven frameworks (e.g., asyncore, Twisted)
#    by automatically generating callbacks.

# so the basic idea behind the CPS transform is that there are *no* complex args to anything.
# by requiring complex args to be computed and placed into a variable, all primitives,
# function calls, etc... are applied only to variables.  [This is why CPS is often described as
# 'making order of evaluation specific']

# The output from this looks more like SSA than normal python code.
# The obvious correction to this is to have a cps 'target' be the stack, rather than a
#   new variable, and then the bytecode ops will act very similarly, rather than taking
#   a series of variable arguments they'll assume the arguments are on the stack.  This will
#   require making this a source->bytecode transform rather than source->source.
#
# XXX ok the idea of targetting the stack might not work - what happens if we leave stuff on
#   the stack when we call a continuation function?  [maybe this isn't really an issue since
#   anything 'live' over the call will have to be an argument?]

# TODO:
#  * some kind of importy or decoratory magic to automatically run this at load time.
#  * exceptions (think about exception-passing style)
#  * for loops
#  * ability to trampoline

import sys

W = sys.stdout.write

operators = {
    'Add' : '+',
    'Sub' : '-',
    'Mult' : '*',
    'Div' : '/',
    'Mod' : '%',
    'Pow' : '**',
    'LShift' : '<<',
    'RShift' : '>>',
    'BitOr' : '|',
    'BitXor' : '~',
    'BitAnd' : '&',
    'FloorDiv' : '//',
    }
    
comparisons = {
    'Eq' : '==',
    'NotEq' : '!=',
    'Lt' : '<',
    'LtE' : '<=',
    'Gt' : '>',
    'GtE' : '>=',
    'Is' : 'is',
    'IsNot' : 'is not',
    'In' : 'in',
    'NotIn' : 'not in',
    }

class Node:

    def __init__ (self, subs, k, vars=(), params=None):
        assert (k is None or isinstance (k, Cont))
        self.subs = subs
        self.k = k
        self.vars = vars
        self.params = params

    def pprint (self, indent=0):
        W ('%s%s%s %r %r\n' % ('  ' * indent, self.prefix(), self.__class__.__name__, self.vars, self.params))
        for sub in self.subs:
            sub.pprint (indent+1)
        if self.k.exp:
            self.k.exp.pprint (indent)

    def prefix (self):
        if self.k.name:
            return '%s = ' % (self.k.name,)
        else:
            return ''

    def emit_all (self, out):
        n = self
        while 1:
            n.emit (out)
            if not n.k.name:
                break
            else:
                n = n.k.exp

def walk (node):
    while 1:
        yield node
        if not node.k.name:
            break
        else:
            node = node.k.exp

# we need two passes to identify 'nonlocal' variables:
#   1) pass to identify 'local' variables (assigned without a global)
#   2) pass to identify 'nonlocal' variables (assigned with no global or local)

def search_lenv0 (name, lenv):
    # XXX later we'll make this work by supporting 'global'
    return False
    
# identify all 'local' variables in the CPS tree, by searching
#   for Assign nodes [XXX that do not refer to globals].
def find_locals (root, lenv):
    for node in walk (root):
        if isinstance (node, FunctionDef):
            # only extend the env with *real* functions, not continuation funs
            if not node.kfunp:
                lenv = (node, lenv)
        elif isinstance (node, Assign):
            if lenv and not search_lenv0 (node.name, lenv):
                #print 'found local %r for function %r' % (node.name, lenv[0].name)
                lenv[0].yeslocals.add (node.name)
        for sub in node.subs:
            find_locals (sub, lenv)

def search_lenv1 (name, lenv):
    while lenv:
        fun, lenv = lenv
        if name in fun.yeslocals:
            return True
    return False

def find_nonlocals (root, lenv):
    for node in walk (root):
        if isinstance (node, FunctionDef):
            lenv = (node, lenv)
        elif isinstance (node, Name):
            if search_lenv1 (node.name, lenv):
                #print 'adding nonlocal decl for %r to %r' % (node.name, lenv[0].name)
                lenv[0].nonlocals.add (node.name)
        for sub in node.subs:
            find_nonlocals (sub, lenv)

class Sequence (Node):
    def __init__ (self, exp, k):
        Node.__init__ (self, [exp], k)

class Module (Node):
    def __init__ (self, body, k):
        Node.__init__ (self, [body], k)
    def emit (self, out):
        self.subs[0].emit_all (out)

class Expression (Node):
    def __init__ (self, body, k):
        Node.__init__ (self, [body], k)
    def emit (self, out):
        self.subs[0].emit (out)

class FunctionDef (Node):
    def __init__ (self, name, kfunp, args, decorator_list, body, k):
        nonlocals = set()
        yeslocals = set()
        Node.__init__ (self, [body], k, params=(name, kfunp, decorator_list, nonlocals, yeslocals, args))
    @property
    def name (self):
        return self.params[0]
    @property
    def kfunp (self):
        return self.params[1]
    @property
    def nonlocals (self):
        return self.params[3]
    @property
    def yeslocals (self):
        return self.params[4]
    @property
    def formals (self):
        return self.params[5]
    def emit (self, out):
        name, kfunp, decs, nonlocals, yeslocals, formals = self.params
        #formals = ', '.join ([ x.id for x in formals.args ])
        formals0 = ', '.join ([ x.arg for x in formals.args ])
        out ('def %s (%s):' % (name, formals0,))
        out.indent()
        if nonlocals:
            out ('nonlocal %s' % (', '.join (nonlocals),))
        self.subs[0].emit_all (out)
        out.dedent()
        
class If (Node):
    def __init__ (self, test_var, body, orelse):
        Node.__init__ (self, [body, orelse], NullCont, [test_var])
    def emit (self, out):
        out ('if %s:' % (self.vars[0],))
        out.indent()
        self.subs[0].emit_all (out)
        out.dedent()
        if self.subs[1]:
            out ('else:')
            out.indent()
            self.subs[1].emit_all (out)
            out.dedent()

class Return (Node):
    def __init__ (self, var):
        Node.__init__ (self, [], NullCont, [var])
    def emit (self, out):
        out ('return %s' % (self.vars[0],))
    
class BinOp (Node):
    def __init__ (self, vars, op, k):
        Node.__init__ (self, [], k, vars, params=op)
    def emit (self, out):
        op = operators[self.params.__class__.__name__]
        out ('%s%s %s %s' % (self.prefix(), self.vars[0], op, self.vars[1]))

class BoolOp (Node):
    def __init__ (self, vars, op, k):
        Node.__init__ (self, [], k, vars, params=op)
    def emit (self, out):
        op = ' %s ' % self.params.__class__.__name__.lower()
        out ('%s%s' % (self.prefix(), op.join (self.vars,)))

class Assign (Node):
    def __init__ (self, vars, name, k):
        Node.__init__ (self, [], k, vars, params=name)
    @property
    def name (self):
        return self.params.id
    def emit (self, out):
        targ = self.params
        path = []
        while isinstance (targ, ast.Attribute):
            path.append (targ.attr)
            targ = targ.value
        # XXX handle other assignment types later...
        assert (isinstance (targ, ast.Name))
        path.append (targ.id)
        path.reverse()
        out ('%s = %s' % ('.'.join (path), self.vars[0]))

class Call (Node):
    def __init__ (self, fun_var, vars, k):
        Node.__init__ (self, [], k, [fun_var] + vars)
    def emit (self, out):
        out ('%s%s (%s)' % (self.prefix(), self.vars[0], ', '.join (self.vars[1:])))

class Num (Node):
    def __init__ (self, value, k):
        Node.__init__ (self, [], k, params=value)
    def emit (self, out):
        out ('%s%r' % (self.prefix(), self.params.n,))

class Name (Node):
    def __init__ (self, name, k):
        Node.__init__ (self, [], k, params=name)
    @property
    def name (self):
        return self.params.id
    def emit (self, out):
        out ('%s%s' % (self.prefix(), self.params.id,))

class Compare (Node):
    def __init__ (self, vars, ops, k):
        Node.__init__ (self, [], k, vars, params=ops)
    def emit (self, out):
        r = []
        for i in range (len (self.vars) - 1):
            r.append (self.vars[i])
            r.append (comparisons[self.params[i].__class__.__name__])
        r.append (self.vars[-1])
        out ('%s%s' % (self.prefix(), ' '.join (r)))

class Print (Node):
    def __init__ (self, vars, k):
        Node.__init__ (self, [], k, vars)
    def emit (self, out):
        #out ('print %s' % (', '.join (self.vars)))        
        out ('print (%s)' % (', '.join (self.vars)))

class Attribute (Node):
    def __init__ (self, var, name, ctx, k):
        Node.__init__ (self, [], k, [var], params=(name, ctx))
    def emit (self, out):
        name, ctx = self.params
        # XXX assert something about ctx?
        out ('%s%s.%s' % (self.prefix(), self.vars[0], name))

# I think the Expr node is wrapped around an expression
#   that is in statement context, and thus represents a
#   dead continuation [and a noop emit]
class Expr (Node):
    def __init__ (self, k):
        Node.__init__ (self, [], k,)
    def emit (self, out):
        out ('pass')

class Verbatim (Node):
    def __init__ (self, exp, k):
        Node.__init__ (self, [], k, params=exp)
    def emit (self, out):
        import io
        f = io.StringIO()
        unparse.Unparser (self.params, f)
        src = f.getvalue()
        for line in src.split ('\n'):
            out (line)

class Cont:
    def __init__ (self, name, exp):
        self.name = name
        self.exp = exp

cont_counter = 0

def make_cont (genk):
    global cont_counter
    name = 'v%d' % (cont_counter,)
    cont_counter += 1
    return Cont (name, genk (name))

def dead_cont (genk):
    return Cont ('_', genk())


NullCont = Cont ('', None)

class transformer:

    def __init__ (self, cps_prefix='cps_'):
        self.cps_prefix = cps_prefix
        self.env = []

    def t_exp (self, node, k):
        if isinstance (node, list):
            # implied sequence
            return self.t_sequence (node, k)
        else:
            name = 't_%s' % (node.__class__.__name__,)
            probe = getattr (self, name)
            if not probe:
                raise ValueError (name)
            else:
                return probe (node, k)

    def t_Expression (self, node, k):
        return Expression (self.t_exp (node.body, k), k)

    def t_sequence (self, exps, k):
        if len(exps) == 0:
            raise ValueError ('empty sequence')
        elif len(exps) == 1:
            return self.t_exp (exps[0], k)
        else:
            return self.t_exp (
                exps[0],
                dead_cont (lambda: self.t_sequence (exps[1:], k))
                )

    def t_Module (self, node, k):
        return Module (self.t_sequence (node.body, k), k)

    def t_Assign (self, node, k):
        # for now
        assert (len(node.targets) == 1)
        return self.t_exp (
            node.value,
            make_cont (lambda var: Assign ([var], node.targets[0], k))
            )

    def t_Num (self, node, k):
        return Num (node, k)

    def t_Name (self, node, k):
        return Name (node, k)

    def t_rands (self, vars, rands, ck):
        if not rands:
            return ck (vars)
        else:
            return self.t_exp (
                rands[0],
                make_cont (lambda var: self.t_rands (vars+[var], rands[1:], ck))
                )

    def t_BinOp (self, node, k):
        return self.t_rands ([], [node.left, node.right], lambda vars: BinOp (vars, node.op, k))

    def t_BoolOp (self, node, k):
        return self.t_rands ([], node.values, lambda vars: BoolOp (vars, node.op, k))

    def t_If_tail (self, node, k):
        return self.t_exp (
            node.test,
            make_cont (
                lambda tvar: If (
                    tvar,
                    self.t_exp (node.body, NullCont),
                    self.t_exp (node.orelse, NullCont)
                    )
                )
            )

    def t_If (self, node, k):
        if k.exp is None:
            # tail position, no need for a continuation function
            return self.t_If_tail (node, k)
        else:
            name = 'kf%d' % (self.kf_counter,)
            self.kf_counter += 1
            call_kf = dead_cont (lambda: Call (name, [], NullCont))
            def make_if():
                return self.t_exp (
                    node.test,
                    make_cont (
                        lambda tvar: If (
                            tvar,
                            self.t_exp (node.body, call_kf),
                            self.t_exp (node.orelse, call_kf)
                            )
                        )
                    )
            return self.cont_as_function (name, k, make_if)

    def t_Return (self, node, k):
        # 'return' == 'feed the result to the continuation'
        return self.t_exp (
            node.value,
            make_cont (lambda var: Call ('k', [var], NullCont))
            )

    def t_Attribute (self, node, k):
        return self.t_exp (node.value, make_cont (lambda var: Attribute (var, node.attr, node.ctx, k)))

    def name_is_cps (self, name):
        return name.startswith (self.cps_prefix)

    def fun_is_cps (self, node):
        return ((isinstance (node, ast.Name) and self.name_is_cps (node.id))
                or (isinstance (node, ast.Attribute) and self.name_is_cps (node.attr)))

    def cont_as_function (self, name, k, ck):
        formals = ast.arguments()
        if k.name and k.name != '_':
            #formals.args = [ast.Name (k.name, ast.Param())]
            formals.args = [ast.arg (k.name, ast.Param())]
        else:
            formals.args = []
        return FunctionDef (
            name,
            True,
            formals,
            [],
            k.exp,
            dead_cont (ck)
            )

    kf_counter = 0

    def t_Call (self, node, k):
        # an async call will require:
        # 1) packaging up the continuation in a local function
        # 2) invoking with the extra continuation argument [and eventually an exception continuation]
        if self.fun_is_cps (node.func):
            kfname = 'kf%d' % (self.kf_counter,)
            self.kf_counter += 1
            formal = k.name
            def make_Call (vars):
                return self.t_exp (
                    node.func,
                    make_cont (lambda fun_var: Call (fun_var, vars, NullCont))
                    )
            return self.cont_as_function (
                kfname,
                k,
                lambda: self.t_rands ([kfname], node.args, make_Call)
                )
        else:
            def make_Call (vars):
                return self.t_exp (
                    node.func,
                    make_cont (lambda fun_var: Call (fun_var, vars, k))
                    )
            return self.t_rands ([], node.args, make_Call)

    def t_FunctionDef (self, node, k):
        if not self.name_is_cps (node.name):
            return Verbatim (node, k)
        for dec in node.decorator_list:
            if dec.id == 'cps_manual':
                node.decorator_list.remove (dec)
                return Verbatim (node, k)
        #karg = ast.Name ('k', ast.Param())
        karg = ast.arg ('k', ast.Param())
        formals = node.args
        formals.args = [karg] + formals.args
        return FunctionDef (
            node.name,
            False,
            formals,
            node.decorator_list,
            self.t_exp (node.body, NullCont),
            k
            )

    def t_Print (self, node, k):
        return self.t_rands ([], node.values, lambda vars: Print (vars, k))

    def t_Compare (self, node, k):
        return self.t_rands ([], [node.left] + node.comparators, lambda vars: Compare (vars, node.ops, k))

    def t_Expr (self, node, k):
        return self.t_exp (node.value, dead_cont (lambda: Expr (k)))

    def t_While (self, node, k):
        # fields: test, body, orelse
        #
        # while test:
        #   <body>
        # else:
        #   <orelse>
        # <k>
        # =>
        # def kf():
        #   <k>
        # def wf():
        #   if <test>:
        #     <body>
        #     wf()
        #   else:
        #     <orelse>
        #     kf()
        # wf()
        name0 = 'wkf%d' % (self.kf_counter,)
        self.kf_counter += 1
        name1 = 'kf%d' % (self.kf_counter,)
        self.kf_counter += 1
        call_wkf = dead_cont (lambda: Call (name0, [], NullCont))
        call_kf = dead_cont (lambda: Call (name1, [], NullCont))
        def make_while():
            def make_test (tvar):
                return If (
                    tvar,
                    self.t_exp (node.body, call_wkf),
                    self.t_exp (node.orelse, call_kf)
                    )
            return self.cont_as_function (
                name0, 
                Cont ('_', self.t_exp (node.test, make_cont (make_test),)),
                lambda: call_wkf.exp
                )
        return self.cont_as_function (name1, k, make_while)

    def t_Import (self, node, k):
        return Verbatim (node, k)

class writer:
    indent_string = '    '
    def __init__ (self, fout):
        self.level = 0
        self.fout = fout
    def indent (self):
        self.level += 1
    def dedent (self):
        self.level -= 1
    def __call__ (self, s):
        self.fout.write (
            bytes (
                '%s%s\n' % (self.indent_string * self.level, s),
                'utf-8'
                )
            )

s0 = """\
@cps_manual
def cps_print (k, v):
    print (v)
    k()
def cps_fact (n):
    if n == 1:
        return 1
    else:
        return n * cps_fact (n-1)
cps_print (cps_fact (5))
"""

s1 = """\
def double (x):
    return x * 2
@cps_manual
def cps_print (k, v):
    print (v)
    k()
y=9
def cps_thing():
    x = 0
    while x < 10:
        if x < 3:
            x = x + 1
        else:
            x = x + 2
        cps_print (double (x))
    else:
        x = y
    return x * 5
cps_print (cps_thing())
"""

# this blows out the recursion limit, but it seems to transform correctly.
#  might make a good demo of a trampoline...
s2 = """\
@cps_manual
def cps_print (k, v):
    print (v)
    k()
def cps_tak (x, y, z):
    if y >= x:
        return z
    else:
        return cps_tak (
            cps_tak (x-1, y, z),
            cps_tak (y-1, z, x),
            cps_tak (z-1, x, y)
            )
cps_print (cps_tak (18, 12, 6))
"""

def t0():
    exp = ast.parse (s1)
    t = transformer()
    cps = t.t_exp (exp, NullCont)
    find_locals (cps, None)
    find_nonlocals (cps, None)
    #cps.pprint()
    w = writer (sys.stdout)
    cps.emit_all (w)

def dofile (path):
    import os
    base, ext = os.path.splitext (path)
    src = open (path).read()
    exp = ast.parse (src, path, 'exec')
    t = transformer()
    cps = t.t_exp (exp, NullCont)
    find_locals (cps, None)
    find_nonlocals (cps, None)
    fout = open (base + '.cps.py', 'wb')
    w = writer (fout)
    cps.emit_all (w)
    fout.close()

if __name__ == '__main__':
    for path in sys.argv[1:]:
        dofile (path)
