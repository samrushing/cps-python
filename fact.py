# -*- Mode: Python -*-

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
