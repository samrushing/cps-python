
from scheduler import schedule, run



def double(x):
    return (x * 2)



def cps_print(k, v):
    print(v)
    k()

v24 = 9
y = v24
def cps_thing (k):
    v23 = 0
    x = v23
    def kf3 ():
        nonlocal x
        v4 = x
        v5 = 5
        v3 = v4 * v5
        k (v3)
    def wkf2 ():
        nonlocal x
        v21 = x
        v22 = 10
        v6 = v21 < v22
        if v6:
            def kf5 ():
                nonlocal x
                def kf4 ():
                    nonlocal x
                    pass
                    wkf2 ()
                v9 = x
                v10 = double
                v7 = v10 (v9)
                v8 = cps_print
                v8 (kf4, v7)
            v18 = x
            v19 = 3
            v11 = v18 < v19
            if v11:
                v13 = x
                v14 = 1
                v12 = v13 + v14
                x = v12
                kf5 ()
            else:
                v16 = x
                v17 = 2
                v15 = v16 + v17
                x = v15
                kf5 ()
        else:
            v20 = y
            x = v20
            kf3 ()
    wkf2 ()
def kf0 ():
    pass
def kf1 (v0):
    v1 = cps_print
    v1 (kf0, v0)
v2 = cps_thing
v2 (kf1)

run()
