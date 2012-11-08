

def cps_print(k, v):
    print(v)
    k()

def cps_fact (k, n):
    v13 = n
    v14 = 1
    v4 = v13 == v14
    if v4:
        v5 = 1
        k (v5)
    else:
        v7 = n
        def kf2 (v8):
            v6 = v7 * v8
            k (v6)
        v11 = n
        v12 = 1
        v9 = v11 - v12
        v10 = cps_fact
        v10 (kf2, v9)
def kf0 ():
    pass
def kf1 (v0):
    v1 = cps_print
    v1 (kf0, v0)
v2 = 5
v3 = cps_fact
v3 (kf1, v2)
