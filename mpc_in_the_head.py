from functools import reduce
from circuit import *
from circuitry import *
from secrets import randbits
from LowMC import init_encrypt, xor_block


#
# MPC primitives
#

def share(secret, n):
    shares = [None, secret] + [None]*(n-1)
    for i in range(2, n+1):
        shares[i] = constant(randbits(1))
        shares[1] = shares[1] ^ shares[i]
    return shares

def reconstruct(shares, n):
    secret = shares[1]
    for i in range(2, n+1):
        secret = secret ^ shares[i]
    return secret

def generate_triple(n, _a=None, _b=None):
    _a = constant(randbits(1)) if not _a else _a
    _b = constant(randbits(1)) if not _b else _b
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

    (as_, bs, cs) = list(zip(*abc))

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

def emulate_not(xs, n):
    zs = [None]*(n+1)
    for i in range(1, n+1):
        zs[i] = ~xs[i]
    return zs, []

def emulate_id(xs, _n):
    return xs, []

#
# Circuit emulation
#

def garbled_size(circ):
    gates = circuit()
    gates.gate = circ.gate
    return gates.count(
        lambda g: \
            g.operation == op.and_ \
            or g.operation == op.or_
    )


state = None  # Keeps the 80 bit LSFR state

def mpc_emulate(circ, n):
    share_n = lambda x : share(x, n)
    reconstruct_n = lambda xs : reconstruct(xs, n)

    proof_size = garbled_size(circ) * (2*n+5) * (n-1) + 128

    # , rand_bits
    def emulate(in_bits: bits(circ.wire_in_count)) -> bits(circ.wire_out_count + proof_size):
        encrypt = init_encrypt(constant, constants)
        all_views = [bits([])]
        bitqueue = bits([])
        chosen_indices = [0]*128
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
            if len(views) > 1:
                all_views.extend(views[1:])
                for j in range(n):
                    bitqueue.extend(views[1+j])

            if len(bitqueue) >= 128:# > (128-(2*n+5)):
                preimage = bitqueue[0:128]
                bitqueue = bitqueue[128:]
                # Update random bits to use later in a Fiat-Shamir transformation
                chosen_indices = xor_block(chosen_indices, encrypt(preimage))

        # Cut and choose views for the proof
        # chosen_views = [views[2*i+j] for i, j in zip(chosen_indices[:80], chosen_indices[80:])]
        chosen_views = reduce(lambda v, sl: v.extend(sl) or v, [all_views[1::n],all_views[2::n]])

        output = list(map(reconstruct_n, RAM[-circ.wire_out_count:]))
        o = ~(in_bits[0]|~in_bits[0])  # hack to prevent optimize the output while testing natively
        proof = [o^b for b in reduce(lambda v, sl: v.extend(sl) or v, chosen_views) + chosen_indices]
        print(proof_size, len(proof))
        return bits(output + proof)

    return emulate
