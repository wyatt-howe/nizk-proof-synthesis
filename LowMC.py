# Python port of LowMC.cpp found at
# https://github.com/LowMC/lowmc/blob/master/LowMC.cpp

#
# Python polyfills for C++ std::bitset
#

bitset = lambda n, b : list([b])*n

def xor_block(block1, block2):
    return [b1 ^ b2 for b1, b2 in zip(block1, block2)]


#
# LowMC public data
#

numofboxes = 49  # Number of Sboxes
blocksize = 256  # Block size in bits
keysize = 80  # Key size in bits
rounds = 8  # Number of rounds

identitysize = blocksize - (3 * numofboxes)  # Size of the identity part in the Sbox layer

block = lambda : bitset(blocksize, 0)  # Stores messages
keyblock = lambda : bitset(keysize, 0)  # Stores states


#
# LowMC private data members
#

# The Sbox and its inverse
Sbox = [0x00, 0x01, 0x03, 0x06, 0x07, 0x04, 0x05, 0x02]  # vector<unsigned>
invSbox = [0x00, 0x01, 0x07, 0x02, 0x05, 0x06, 0x03, 0x04]  # vector<unsigned>

LinMatrices = [[block() for _ in range(blocksize)] for _ in range(rounds)]  # Stores the binary matrices for each round
invLinMatrices = [[block() for _ in range(blocksize)] for _ in range(rounds)]  # Stores the inverses of LinMatrices
roundconstants = [block() for _ in range(rounds)]  # Stores the round constants
key = 0  # Stores the master key
KeyMatrices = [[keyblock() for _ in range(blocksize)] for _ in range(rounds+1)]  # Stores the matrices that generate the round keys
roundkeys = [keyblock() for _ in range(rounds+1)]  # Stores the round keys
state = None  # Keeps the 80 bit LSFR state

#
# LowMC functions
#

def encrypt(message: block):  # -> block
    c = xor_block(message, roundkeys[0])
    for r in range(rounds):
        c = Substitution(c)
        c = MultiplyWithGF2Matrix(LinMatrices[r], c)
        c = xor_block(message, roundconstants[r])
        c = xor_block(message, roundkeys[r+1])

    return c


def decrypt(message: block):  # -> block
    c = message
    for r in reversed(range(rounds)):
        c = xor_block(message, roundkeys[r+1])
        c = xor_block(message, roundconstants[r])
        c = MultiplyWithGF2Matrix(invLinMatrices[r], c)
        c = invSubstitution(c)
    c = xor_block(message, roundkeys[0])

    return c


def set_key (k: keyblock):  # -> void
    key = k
    keyschedule()


#
# LowMC private functions
#

def Substitution(message: block):  # -> block
    temp = block()

    # Get the identity part of the message
    j = 3*numofboxes
    temp = xor_block(temp, message[j:] + [0 for _ in range(j)])

    # Get the rest through the S-boxes
    for i in range(numofboxes):
        temp = [0, 0, 0] + temp[:-3]
        j = 3*(numofboxes-i-1)
        idx_bits = (message[j:] + [0 for _ in range(j)])[0:3]
        idx = idx_bits[0] + 2*idx_bits[1] + 4*idx_bits[2]
        sb = Sbox[idx]
        sblock = block()
        sblock[0] = sb % 2
        sblock[1] = (sb//2) % 2
        sblock[2] = (sb//4) % 2
        # temp = [sb ^ tb for tb in temp]
        temp = xor_block(temp, sblock)

    return temp


def invSubstitution(message: block):  # -> block
    temp = block()

    # Get the identity part of the message
    j = 3*numofboxes
    temp = xor_block(temp, message[j:] + [0 for _ in range(j)])

    # Get the rest through the inverted S-boxes
    for i in range(numofboxes):
        temp = [0, 0, 0] + temp[:-3]
        j = 3*(numofboxes-i-1)
        idx_bits = (message[j:] + [0 for _ in range(j)])[0:3]
        idx = idx_bits[0] + 2*idx_bits[1] + 4*idx_bits[2]
        sb = Sbox[idx]
        sblock = block()
        sblock[0] = sb % 2
        sblock[1] = (sb//2) % 2
        sblock[2] = (sb//4) % 2
        # temp = [sb ^ tb for tb in temp]
        temp = xor_block(temp, sblock)

    return temp


def MultiplyWithGF2Matrix(matrix, message):  # -> block
    temp = block()
    for i in range(blocksize):
        temp[i] = sum([mb & b for mb, b in zip(message, matrix[i])]) % 2
    return temp


def MultiplyWithGF2Matrix_Key(matrix, k):  # -> block
    temp = block()
    for i in range(blocksize):
        temp[i] = sum([kb & b for kb, b in zip(k, matrix[i])]) % 2
    return temp


def keyschedule():  # -> void
    roundkeys.clear()
    for r in range(rounds+1):
        roundkeys.append(
            MultiplyWithGF2Matrix_Key(KeyMatrices[r], key)
        )

    return


def instantiate_LowMC():  # -> void
    # Create LinMatrices and invLinMatrices
    LinMatrices.clear()
    invLinMatrices.clear()
    for r in range(rounds):
        # Create matrix
        mat = [block() for _ in range(blocksize)]

        # Fill matrix with random bits
        while True:
            mat.clear()
            for i in range(blocksize):
                mat.append(
                    getrandblock()
                )

            # Done if matrix is invertible
            if rank_of_Matrix(mat) == blocksize:
                break

        LinMatrices.append(mat)
        invLinMatrices.append(invert_Matrix(LinMatrices[-1]))

    # Create roundconstants
    roundconstants.clear()
    for r in range(rounds):
        roundconstants.append(
            getrandblock()
        )

    # Create KeyMatrices
    KeyMatrices.clear()
    for r in range(rounds+1):
        # Create matrix
        mat = [keyblock() for _ in range(keysize)]

        # Fill matrix with random bits
        while True:
            mat.clear()
            for i in range(blocksize):
                mat.append(
                    getrandkeyblock()
                )

            # Repeat unless matrix is of maximal rank
            if rank_of_Matrix_Key(mat) >= min(blocksize, keysize):
                break

        KeyMatrices.append(mat)


#
# Binary matrix functions
#

def rank_of_Matrix(matrix):   # -> unsigned
    # Copy of the matrix
    mat = [block() for _ in range(blocksize)]
    for i in range(blocksize):
        for j in range(blocksize):
            mat[i][j] = matrix[i][j]

    size = len(mat[0])

    # Transform to upper triangular matrix
    row = 0
    for col in reversed(range(size)):
        if not mat[row][col]:
            r = row
            while r < len(mat) and not mat[r][col]:
                r = r + 1

            if r >= len(mat):
                continue
            else:
                temp = mat[row]
                mat[row] = mat[r]
                mat[r] = temp

        for i in range(row+1, len(mat)):
            if mat[i][col]:
                mat[i] = xor_block(mat[i], mat[row])

        row = row + 1
        if row == size:
            break

    return row


def rank_of_Matrix_Key(matrix):  # -> unsigned
    # Copy of the matrix
    # BUG from actual LowMC cpp code (?)  Should the below instead be `keysize`?
    mat = [keyblock() for _ in range(blocksize)]
    for i in range(blocksize):
        for j in range(keysize):
            mat[i][j] = matrix[i][j]

    size = len(mat[0])

    # Transform to upper triangular matrix
    row = 0
    for col in range(1, size+1):
        if not mat[row][size-col]:
            r = row
            while r < len(mat) and (0 == mat[r][size-col]):
                r = r + 1

            if r >= len(mat):
                continue
            else:
                temp = mat[row]
                mat[row] = mat[r]
                mat[r] = temp

        for i in range(row+1, len(mat)):
            if mat[i][size-col]:
                mat[i] = xor_block(mat[i], mat[row])

        row = row + 1
        if row == size:
            break

    return row


def invert_Matrix(matrix):  # -> vector<block>
    # Copy of the matrix
    mat = [block() for _ in range(blocksize)]
    for i in range(blocksize):
        for j in range(blocksize):
            mat[i][j] = matrix[i][j]

    # Initialize to hold the inverted matrix
    invmat = [block() for _ in range(blocksize)]
    for i in range(blocksize):
        invmat[i][i] = 1

    size = len(mat[0])

    # Transform to upper triangular matrix
    row = 0
    for col in range(size):
        if not mat[row][col]:
            r = row + 1
            while r < len(mat) and not mat[r][col]:
                r = r + 1

            if r >= len(mat):
                continue
            else:
                temp = mat[row]
                mat[row] = mat[r]
                mat[r] = temp
                temp = invmat[row]
                invmat[row] = invmat[r]
                invmat[r] = temp

        for i in range(row + 1, len(mat)):
            if mat[i][col]:
                mat[i] = xor_block(mat[i], mat[row])
                invmat[i] = xor_block(invmat[i], invmat[row])

        row = row + 1


    # Transform to identity matrix
    for col in reversed(range(size)):
            for r in range(col):
                if mat[r][col]:
                    mat[r] = xor_block(mat[r], mat[col])
                    invmat[r] = xor_block(invmat[r], invmat[col])

    return invmat


#
# Pseudorandom bits
#

def getrandblock():  # -> block
    return [getrandbit() for i in range(blocksize)]


def getrandkeyblock():  # -> keyblock
    return [getrandbit() for i in range(keysize)]


# Uses the Grain LSFR as self-shrinking generator to create pseudorandom bits
# Is initialized with the all 1s state
# The first 160 bits are thrown away
def getrandbit():  # -> bool
    global state
    tmp = 0

    # If state has not been initialized yet
    if state is None:
        state = bitset(80, 1)  # Initialize with all bits set

        # Throw the first 160 bits away
        for _ in range(160):
            # Update the state
            tmp = state[0] ^ state[13] ^ state[23] ^ state[38] ^ state[51] ^ state[62]
            state = state[1:] + [0]
            state[79] = tmp

    # Choice records whether the first bit is 1 or 0.
    # The second bit is produced if the first bit is 1.
    while True:
        # Update the state
        tmp = state[0] ^ state[13] ^ state[23] ^ state[38] ^ state[51] ^ state[62]
        state = state[1:] + [0]
        state[79] = tmp
        choice = tmp
        tmp = state[0] ^ state[13] ^ state[23] ^ state[38] ^ state[51] ^ state[62]
        state = state[1:] + [0]
        state[79] = tmp

        if choice:
            break

    return tmp


#
# Setup and test
#

if __name__ == '__main__':
    key = keyblock()
    key[0:1] = [1]
    instantiate_LowMC()
    keyschedule()

    m = block()
    m[0:16] = [1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    print("Plaintext:")
    print(''.join(map(str, reversed(m))))

    m = encrypt(m)
    print("Ciphertext:")
    print(''.join(map(str, reversed(m))))

    m = decrypt(m)
    print("Encryption followed by decryption of plaintext:")
    print(''.join(map(str, reversed(m))))

