from functools import reduce
from parts import parts
from bitlist import bitlist
from circuit import op
from circuitry import *

# def add(xs: bits(8), ys: bits(8)) -> bits(8):
#     """Addition of bit vectors."""
#     (xs, ys) = (list(reversed(xs)), list(reversed(ys)))
#     (x0, xt, y0, yt) = (xs[0], xs[1:], ys[0], ys[1:])
#     (s, c) = (x0 ^ y0, x0 & y0)
#     def combine(zs_, xy):
#         c = zs_.pop()
#         (_xor, _and) = (xy[0] ^ xy[1], xy[0] & xy[1])
#         return zs_ + [_xor ^ c, _and | (_xor & c)]
#     zs = [s] + list(reduce(combine, zip(xt, yt), [c]))[:-1]
#     return bits(list(reversed(zs)))

def mpc_emulate(circ):
    def emulate(in_bits: bits(circ.wire_in_count)) -> bits(circ.wire_out_count):
        RAM = [None]*circ.wire_count  # [None]*sum(circ.gate_count)
        RAM[0:circ.wire_in_count] = in_bits

        for gate in circ.gate:
            in1, in2 = gate.wire_in_index
            out = gate.wire_out_index[0]
            if gate.operation == op.and_:
                RAM[out] = RAM[in1] & RAM[in2]
            if gate.operation == op.or_:
                RAM[out] = RAM[in1] | RAM[in2]
            if gate.operation == op.xor_:
                RAM[out] = ~(RAM[in1] ^ RAM[in2])  # Modified to demonstrate emulation
            if gate.operation == op.not_:
                RAM[out] = ~RAM[in1]
            if gate.operation == op.id_:
                RAM[out] = RAM[in1]

        return bits(RAM[-circ.wire_out_count:])

    # return sha256
    return emulate





