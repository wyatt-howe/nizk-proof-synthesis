from functools import reduce
from parts import parts
from bitlist import bitlist
from circuitry import *

def add(xs: bits(8), ys: bits(8)) -> bits(8):
    """Addition of bit vectors."""
    (xs, ys) = (list(reversed(xs)), list(reversed(ys)))
    (x0, xt, y0, yt) = (xs[0], xs[1:], ys[0], ys[1:])
    (s, c) = (x0 ^ y0, x0 & y0)
    def combine(zs_, xy):
        c = zs_.pop()
        (_xor, _and) = (xy[0] ^ xy[1], xy[0] & xy[1])
        return zs_ + [_xor ^ c, _and | (_xor & c)]
    zs = [s] + list(reduce(combine, zip(xt, yt), [c]))[:-1]
    return bits(list(reversed(zs)))

def mpc_emulate(circ):
    # return sha256
    # circ.evaluate
    return add









