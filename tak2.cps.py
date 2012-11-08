
# tak.cps.py, unvariablized by hand.

from scheduler import schedule, run

def cps_print(k, v):
    print(v)
    schedule(k)

def cps_tak (k, x, y, z):
    if y >= x:
        schedule (k, z)
    else:
        def kf2 (v8):
            schedule (k, v8)
        def kf5 (v9):
            def kf4 (v10):
                def kf3 (v11):
                    cps_tak (kf2, v9, v10, v11)
                cps_tak (kf3, z-1, x, y)
            cps_tak (kf4, y-1, z, x)
        cps_tak (kf5, x-1, y, z)
def kf0 ():
    pass
def kf1 (v0):
    cps_print (kf0, v0)
cps_tak (kf1, 18, 12, 6)

run()
