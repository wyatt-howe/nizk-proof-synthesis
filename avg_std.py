from functools import reduce
from tqdm import tqdm
from parts import parts
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

#
# A high level combinator for iteration of bit arrays
#

def bit_combinator(xs, ys, f, z0, temp0, keep_temp_bit=False):
    from functools import reduce
    def combine(zs, xy):
        (x, y) = xy
        temp_in = zs.pop()
        [z, temp_out] = f(x, y, temp_in)
        return zs + [z] + [temp_out]
    zs = reduce(combine, zip(xs, ys), [temp0])
    if not keep_temp_bit: zs.pop()
    return [z0] + zs

#
# Primitive arithmetic functions.
#

def bit_adder(x, y, carry):
    _xor = xor_bit(x, y)

    # Save and update carry
    _sum = xor_bit(_xor, carry)
    carry = lor_bit(
        and_bit(x, y),
        and_bit(_xor, carry)
    )

    return [_sum, carry]

def bit_xadder(x, y, carry):
    xy = xor_bit(x, y)
    cx = xor_bit(x, carry)
    cy = xor_bit(y, carry)

    # Save sum and update carry
    _sum = xor_bit(carry, xy)
    carry = xor_bit(carry, and_bit(cx, cy))

    return [_sum, carry]

def bit_subtractor(x, y, borrow):
    _xor = xor_bit(x, y)

    # Save and update borrow
    diff = xor_bit(_xor, borrow)
    borrow = lor_bit(
        and_bit(~x, y),
        and_bit(~_xor, borrow)
    )

    return [diff, borrow]

def add(xs, ys, l, preserve_overflow_bit=False):
    check_lengths(xs, ys, l)
    (xs, ys) = (list(reversed(xs)), list(reversed(ys)))

    # Match head and tail
    (x0, xt) = (xs[0], xs[1:])
    (y0, yt) = (ys[0], ys[1:])

    # The first sum bit and carry bit are computed quicker as:
    (sum0, carry0) = (xor_bit(x0, y0), and_bit(x0, y0))

    # Create a ripple-carry adder and with it, sum the remaining bits
    zs = bit_combinator(xt, yt, bit_adder, sum0, carry0, keep_temp_bit=preserve_overflow_bit)

    return bits(list(reversed(zs)))

def long_div(xs, ys, l):
    check_lengths(xs, ys, l)
    (xs, ys) = (list(reversed(xs)), list(reversed(ys)))

    quotient = [None]*l
    remainder = constants([0]*(l-1))  # or constants([0])*(l-1) ?

    for i, x in reversed(list(enumerate(xs))):  # range(len(xs)-1,-1,-1); x = xs[i]

        # Add bit i to the head of remainder (least significant bit)
        remainder = [x] + remainder[0:l-1]

        # Get the next bit of the quotient
        # and conditionally subtract b from the
        # intermediate remainder to continue
        diff = rev(sub(rev(remainder), rev(ys), l, preserve_overflow_bit=True))
        noUnderflow = ~diff.pop()  # get the overflow bit, diff is now the result of subtraction

        # Get next bit of quotient
        quotient[i] = noUnderflow  # and_bit(noUnderflow, noUnderflow)

        # Update remainder
        for (j, _) in enumerate(remainder):
            # note, if noUnderflow, then |# bits in diff| <= |# bits in remainder|
            remainder[j] = if_else(noUnderflow, diff[j], remainder[j])

    return (rev(quotient), rev(remainder))

def div(xs, ys, l):
    (quotient, _) = long_div(xs, ys, l)
    return quotient

bit.hook_operation(bit_optimize)

def avg(xs, ys, zs):
    return div(add(xs, add(ys, zs)), [1, 1])

out_name = "./average.txt"
proof_circuit = synthesize(avg).circuit

in_int8s = [3, 4, 3, 4, 3, 4, 3, 4] + [8, 4, 3, 4, 3, 4, 3, 4]
in_bits = [b for i8 in in_int8s for b in bits.from_byte(i8, lambda b: b)]

print("Synthesized `" + out_name + "` with " + str(len(proof_circuit.gate)) + " gates:")
print(' * operation counts: ', {
    o.name(): proof_circuit.count(lambda g: g.operation == o)
    for o in [op.not_, op.and_, op.xor_, op.or_, op.nand_, op.nif_, op.id_, op.xnor_, op.nimp_]
})

to_bin = lambda xs : ''.join(map(str, list(xs)))
print(" * circuit to evaluate on input: ", to_bin(in_bits))
print(" * evaluated circuit got output: ", to_bin(reversed(bitlist(proof_circuit.evaluate(in_bits)).bits)), end='')

with open(out_path, 'w') as circuit_file:
    # Build and emit the Bristol Fashion circuit file.
    circuit_file.write(bristol_fashion(proof_circuit).emit(
        progress=lambda gs: tqdm(gs, desc=' * emitting circuit file')
    ))
