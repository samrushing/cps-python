
from scheduler import schedule, run



def cps_print(k, v):
    print(v)
    schedule(k)

def cps_tak (k, x, y, z):
    v31 = y
    v32 = x
    v6 = v31 >= v32
    if v6:
        v7 = z
        schedule (k, v7)
    else:
        def kf2 (v8):
            schedule (k, v8)
        def kf5 (v9):
            def kf4 (v10):
                def kf3 (v11):
                    v12 = cps_tak
                    v12 (kf2, v9, v10, v11)
                v17 = z
                v18 = 1
                v13 = v17 - v18
                v14 = x
                v15 = y
                v16 = cps_tak
                v16 (kf3, v13, v14, v15)
            v23 = y
            v24 = 1
            v19 = v23 - v24
            v20 = z
            v21 = x
            v22 = cps_tak
            v22 (kf4, v19, v20, v21)
        v29 = x
        v30 = 1
        v25 = v29 - v30
        v26 = y
        v27 = z
        v28 = cps_tak
        v28 (kf5, v25, v26, v27)
def kf0 ():
    pass
def kf1 (v0):
    v1 = cps_print
    v1 (kf0, v0)
v2 = 18
v3 = 12
v4 = 6
v5 = cps_tak
v5 (kf1, v2, v3, v4)

run()
