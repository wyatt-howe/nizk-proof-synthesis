import random

def share(secret, n):
    shares = [None, secret] + [None]*(n-1)
    for i in range(2, n+1):
        shares[i] = random.getrandbits(1)
        shares[1] = shares[1] ^ shares[i]
    return shares

def reconstruct(shares, n):
    secret = shares[1]
    for i in range(2, n+1):
        secret = secret ^ shares[i]
    return secret

def generate_triple(n):
    _a = random.getrandbits(1)
    _b = random.getrandbits(1)
    _c = _a & _b
    return list(zip(share(_a, n), share(_b, n), share(_c, n)))

def stage_two(xi, yi, ai, bi):
    di = xi ^ ai
    ei = yi ^ bi
    return di, ei

def stage_three(xi, yi, ds, es, ci, i1):
    d = reconstruct(ds, n)
    e = reconstruct(es, n)
    zi = ci ^ (xi & e) ^ (yi & d)
    if i1:
        zi = zi ^ (d & e)
    return zi

def emulate_and(xs, ys, abc, n):
    (as_, bs, cs) = list(zip(*abc))

    ds = [None]*(n+1)
    es = [None]*(n+1)
    for i in range(1, n+1):
        ds[i], es[i] = stage_two(xs[i], ys[i], as_[i], bs[i])

    zs = [None]*(n+1)
    for i in range(1, n+1):
        zs[i] = stage_three(xs[i], ys[i], ds, es, cs[i], i == 1)

    views = [None]*(n+1)
    for i in range(1, n+1):
        views[i] = [as_[i], bs[i], cs[i], xs[i], ys[i]] + ds[1:] + es[1:]

    return zs, views

n = 5
for _ in range(128):
    x = random.getrandbits(1)
    y = random.getrandbits(1)

    xs = share(x, n)
    ys = share(y, n)

    abc = generate_triple(n)

    zs, views = emulate_and(xs, ys, abc, n)

    z = reconstruct(zs, n)

    assert(x & y == z)

# from bitlist import bitlist
# print([bitlist(view).hex() for view in random.sample(views, k=n-1)])
