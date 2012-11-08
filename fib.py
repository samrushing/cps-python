# -*- Mode: Python -*-

@cps_manual
def cps_print (k, v):
    print (v)
    k()

def cps_fib (n):
    if n < 2:
        return n
    else:
        return cps_fib (n-1) + cps_fib (n-2)

cps_print (cps_fib (10))
