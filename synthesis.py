import sys

from tqdm import tqdm
from bitlist import bitlist
from circuit import *
from circuitry import *
from bfcl import circuit as bristol_fashion
from mpc_in_the_head import mpc_emulate

def bit_optimize(o, v, *args):
    """Collapses gates when they have constants as inputs."""
    if o == op.not_:
        return constant(v) if type(args[0]) is constant else None

    ((x, y), (tx, ty)) = (args, map(type, args))
    if (tx, ty) == (constant, constant):
        return constant(v)
    elif o == op.and_:
        if tx is constant:
            return y if x.value == 1 else constant(0)
        elif ty is constant:
            return x if y.value == 1 else constant(0)
    elif o == op.or_:
        if tx is constant:
            return constant(1) if x.value == 1 else y
        elif ty is constant:
            return constant(1) if y.value == 1 else x
    elif o == op.xor_:
        if x.gate.index == y.gate.index:
            return constant(0)
        elif tx is constant:
            return y if x.value == 0 else bit(1-y.value, bit.gate(op.not_, [y.gate]))
        elif ty is constant:
            return x if y.value == 0 else bit(1-x.value, bit.gate(op.not_, [x.gate]))

bit.hook_operation(bit_optimize)

in_path = sys.argv[1]
in_name = in_path.split("/")[-1]
out_name = "nizk_"+in_path.split("/")[-1]
out_path = './' + out_name #''.join(in_path.split("/")[:-1])+"/"+out_name # sys.argv[2]
plain_circuit = bristol_fashion(open(in_path).read())
proof_circuit = synthesize(mpc_emulate(plain_circuit, n=3)).circuit

in_int8s = [3, 4, 3, 4] + \
           [5, 4, 3, 4]
in_bits = [b for i8 in in_int8s for b in bits.from_byte(i8, lambda b: b)]

print("Synthesized `" + out_name + "` with " + str(len(proof_circuit.gate)) + " gates:")
print(' * operation counts: ', {
    o.name(): proof_circuit.count(lambda g: g.operation == o)
    for o in [op.not_, op.and_, op.xor_, op.or_, op.nand_, op.nif_, op.id_, op.xnor_, op.nimp_]
})

to_bin = lambda xs : ''.join(map(str, list(xs)))
print(" * circuit to evaluate on input: ", to_bin(in_bits))
print(" * evaluated circuit got output: ", to_bin(reversed(bitlist(proof_circuit.evaluate(in_bits)).bits)))

with open(out_path, 'w') as circuit_file:
    # Build and emit the Bristol Fashion circuit file.
    circuit_file.write(bristol_fashion(proof_circuit).emit(
        progress=lambda gs: tqdm(gs, desc=' * emitting circuit file')
    ))
