import random

def share(secret, n):
    shares = [None, secret] + [None]*(n-1)
    for i in range(2, n+1):
        shares[i] = random.getrandbits(1)
        shares[1] = shares[1] ^ shares[i]
    return shares

def generate_triple(n):
    _a = random.getrandbits(1)
    _b = random.getrandbits(1)
    _c = _a & _b
    return list(zip(share(_a, n), share(_b, n), share(_c, n)))

def stage_one(x):
    x1 = random.getrandbits(1)
    x2 = x ^ x1
    return x1, x2

def stage_two(x1, y1, a1, b1):
    d1 = x1 ^ a1
    e1 = y1 ^ b1
    return d1, e1

def stage_three(x1, y1, d1, d2, e1, e2, c1, p1):
    d = d1 ^ d2
    e = e1 ^ e2
    z1 = c1 ^ (x1 & e) ^ (y1 & d)
    if p1:
        z1 = z1 ^ (d & e)
    return z1

def emulate_and(x, y, abc):
    ((a1, b1, c1), (a2, b2, c2)) = abc[1:]

    x1, x2 = stage_one(x)
    y1, y2 = stage_one(y)

    d1, e1 = stage_two(x1, y1, a1, b1)
    d2, e2 = stage_two(x2, y2, a2, b2)

    z1 = stage_three(x1, y1, d1, d2, e1, e2, c1, True)
    z2 = stage_three(x2, y2, d1, d2, e1, e2, c2, False)

    z = z1 ^ z2

    assert(x & y == z)

for _ in range(128):
    x = random.getrandbits(1)
    y = random.getrandbits(1)
    abc = generate_triple(2)
    emulate_and(x, y, abc)
