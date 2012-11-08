# -*- Mode: Python -*-

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
