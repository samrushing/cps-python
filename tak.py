# -*- Mode: Python -*-

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
