from functools import reduce
from parts import parts
from bitlist import bitlist
from circuit import op
from circuitry import *
from secrets import randbits
from LowMC import encrypt, xor_block

#
# MPC primitives
#

def share(secret, n):
    shares = [None, secret] + [None]*(n-1)
    for i in range(2, n+1):
        shares[i] = randbits(1)
        shares[1] = shares[1] ^ shares[i]
    return shares

def reconstruct(shares, n):
    secret = shares[1]
    for i in range(2, n+1):
        secret = secret ^ shares[i]
    return secret

def generate_triple(n):
    _a = randbits(1)
    _b = randbits(1)
    _c = _a & _b
    return list(zip(share(_a, n), share(_b, n), share(_c, n)))

#
# Emulated gates
#

def emulate_and(xs, ys, abc, n):
    def stage_one(xi, yi, ai, bi):
        di = xi ^ ai
        ei = yi ^ bi
        return di, ei

    def stage_two(xi, yi, ds, es, ci, i1):
        d = reconstruct(ds, n)
        e = reconstruct(es, n)
        zi = ci ^ (xi & e) ^ (yi & d)
        if i1:
            zi = zi ^ (d & e)
        return zi

    (as_, bs, cs) = list(map(bits, zip(*abc)))

    ds = [None]*(n+1)
    es = [None]*(n+1)
    for i in range(1, n+1):
        ds[i], es[i] = stage_one(xs[i], ys[i], as_[i], bs[i])

    zs = [None]*(n+1)
    for i in range(1, n+1):
        zs[i] = stage_two(xs[i], ys[i], ds, es, cs[i], i == 1)

    views = [None]*(n+1)
    for i in range(1, n+1):
        views[i] = [as_[i], bs[i], cs[i], xs[i], ys[i]] + ds[1:] + es[1:]

    return zs, views

def emulate_xor(xs, ys, n):
    zs = [None]*(n+1)
    for i in range(1, n+1):
        zs[i] = xs[i] ^ ys[i]
    return zs, []

def emulate_or(xs, ys, abc, n):
    xys, views = emulate_and(xs, ys, abc, n)
    ws, _views = emulate_xor(ys, xys, n)
    zs, _views = emulate_xor(xs, ws, n)
    return zs, views

def emulate_not(xs, ys, n):
    zs = [None]*(n+1)
    for i in range(1, n+1):
        zs[i] = ~xs[i]
    return zs, []

def emulate_id(xs, _n):
    return xs, []

#
# Circuit emulation
#

def mpc_emulate(circ, n):
    share_n = lambda x : share(x, n)
    reconstruct_n = lambda xs : reconstruct(xs, n)

    proof_size = 0#circ.gate_count *

    def emulate(in_bits: bits(circ.wire_in_count)) -> bits(circ.wire_out_count + proof_size):
        all_views = []
        for k in range(80):
            pass
            choicen_indices = [0]*256
            RAM = [[None]*(n+1)]*circ.wire_count
            RAM[0:circ.wire_in_count] = list(map(share_n, in_bits))

            for gate in circ.gate:
                in1, in2 = gate.wire_in_index
                out = gate.wire_out_index[0]
                if gate.operation == op.and_:
                    RAM[out], views = emulate_and(RAM[in1], RAM[in2], generate_triple(n), n)
                if gate.operation == op.or_:
                    RAM[out], views = emulate_or(RAM[in1], RAM[in2], generate_triple(n), n)
                if gate.operation == op.xor_:
                    RAM[out], views = emulate_xor(RAM[in1], RAM[in2], n)
                if gate.operation == op.not_:
                    RAM[out], views = emulate_not(RAM[in1], n)
                if gate.operation == op.id_:
                    RAM[out], views = emulate_id(RAM[in1], n)
                all_views.extend(views)

                # Update random bits to use later in a Fiat-Shamir transformation
                choicen_indices = xor_block(choicen_indices, encrypt(views))

        # Cut and choose views for the proof
        chosen_views = [views[2*i+j] for i, j in zip(choicen_indices[:80], choicen_indices[80:])]

        return bits(list(map(reconstruct_n, RAM[-circ.wire_out_count:])) + list(chosen_views))

    return emulate
