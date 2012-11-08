
from scheduler import schedule



def cps_print(k, v):
    print(v)
    k()

def cps_fib (k, n):
    v17 = n
    v18 = 2
    v4 = v17 < v18
    if v4:
        v5 = n
        schedule (k, v5)
    else:
        def kf3 (v7):
            def kf2 (v8):
                v6 = v7 + v8
                schedule (k, v6)
            v11 = n
            v12 = 2
            v9 = v11 - v12
            v10 = cps_fib
            v10 (kf2, v9)
        v15 = n
        v16 = 1
        v13 = v15 - v16
        v14 = cps_fib
        v14 (kf3, v13)
def kf0 ():
    pass
def kf1 (v0):
    v1 = cps_print
    v1 (kf0, v0)
v2 = 10
v3 = cps_fib
v3 (kf1, v2)
