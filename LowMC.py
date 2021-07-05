# Python port of LowMC.cpp found at
# https://github.com/LowMC/lowmc/blob/master/LowMC.cpp

def xor_block(block1, block2):
    return [b1 ^ b2 for b1, b2 in zip(block1, block2)]

state = None  # Keeps the 80 bit LSFR state

def init_encrypt(_constant, _constants):
    #
    # Python polyfills for C++ std::bitset
    #

    bitset = lambda n, b : list([b])*n


    #
    # LowMC public data
    #

    numofboxes = 1  # Number of S-boxes
    blocksize = 128  # Block size in bits
    keysize = 40  # Key size in bits
    rounds = 1  # Number of rounds

    block = lambda : bitset(blocksize, 0)  # Stores messages
    keyblock = lambda : bitset(keysize, 0)  # Stores states


    #
    # LowMC private data members
    #

    # 3-bit binary bit arrays (in little-endian)
    bin0 = _constants([0,0,0])
    bin1 = _constants([1,0,0])
    bin2 = _constants([0,1,0])
    bin3 = _constants([1,1,0])
    bin4 = _constants([0,0,1])
    bin5 = _constants([1,0,1])
    bin6 = _constants([0,1,1])
    bin7 = _constants([1,1,1])

    # The S-box and its inverse
    Sbox = [bin0, bin1, bin3, bin6, bin7, bin4, bin5, bin2]  # vector<unsigned>

    LinMatrices = [[block() for _ in range(blocksize)] for _ in range(rounds)]  # Stores the binary matrices for each round
    roundconstants = [block() for _ in range(rounds)]  # Stores the round constants
    key = None  # Stores the master key
    KeyMatrices = [[keyblock() for _ in range(blocksize)] for _ in range(rounds+1)]  # Stores the matrices that generate the round keys
    roundkeys = [keyblock() for _ in range(rounds+1)]  # Stores the round keys

    default_key = list(reversed([
        1, 0, 0, 1, 0, 0, 1, 0, 0, 1,
        0, 1, 1, 0, 1, 1, 0, 1, 1, 0,
        0, 1, 1, 0, 1, 1, 0, 1, 1, 0,
        1, 0, 0, 1, 0, 0, 1, 0, 0, 1
    ]))
    key = default_key

    #
    # LowMC functions
    #

    def encrypt(message: block):#, k=None: keyblock):  # -> block
        c = xor_block(message, _constants(roundkeys[0]))
        for r in range(rounds):
            c = Substitution(c)
            c = MultiplyWithGF2Matrix(LinMatrices[r], c)
            c = xor_block(c, _constants(roundconstants[r]))
            c = xor_block(c, _constants(roundkeys[r+1]))

        return c


    #
    # LowMC private functions
    #

    def Substitution(message: block):  # -> block

        # Get the identity part of the message
        j = 3*numofboxes
        temp = message[j:] + _constants([0 for _ in range(j)])

        # Get the rest through the S-boxes
        for i in range(numofboxes):
            temp = _constants([0, 0, 0]) + temp[:-3]
            j = 3*(numofboxes-i-1)
            idx_bits = (message[j:] + _constants([0 for _ in range(j)]))

            a, b, c = idx_bits[0:3]
            inv = lambda t : ~t
            eqt = lambda x,y,z : (inv(a^x)) & (inv(b^y)) & (inv(c^z))
            ife = lambda x,y,z,cmp : [x&cmp, y&cmp, z&cmp]
            add = lambda x,y,z,u,v,w : [x^u, y^v, z^w]

            sb = add(
                *add(
                    *add(
                        *ife(*Sbox[0], eqt(*bin0)),
                        *ife(*Sbox[1], eqt(*bin1))
                    ),
                    *add(
                        *ife(*Sbox[2], eqt(*bin2)),
                        *ife(*Sbox[3], eqt(*bin3))
                    )
                ),
                *add(
                    *add(
                        *ife(*Sbox[4], eqt(*bin4)),
                        *ife(*Sbox[5], eqt(*bin5))
                    ),
                    *add(
                        *ife(*Sbox[6], eqt(*bin6)),
                        *ife(*Sbox[7], eqt(*bin7))
                    )
                )
            )

            sblock = _constants(block())
            sblock[0:3] = sb[0:3]
            temp = xor_block(temp, sblock)

        return temp


    def MultiplyWithGF2Matrix(matrix, message):  # -> block
        temp = block()
        for i in range(blocksize):
            temp[i] = _constant(0)
            for mb, b in zip(message, _constants(matrix[i])):
                temp[i] = temp[i] ^ (mb & b)
        return temp


    def MultiplyWithGF2Matrix_Key(matrix, k, isc=True):  # -> block
        temp = block()
        for i in range(blocksize):
            temp[i] = _constant(0) if isc else _constant(0)
            for kb, b in zip(k, _constants(matrix[i]) if isc else matrix[i]):
                temp[i] = temp[i] ^ (kb & b)
        return temp


    def keyschedule():  # -> void
        roundkeys.clear()
        for r in range(rounds+1):
            roundkeys.append(
                MultiplyWithGF2Matrix_Key(KeyMatrices[r], key, False)
            )

        return


    def instantiate_LowMC():  # -> void
        # Create LinMatrices
        LinMatrices.clear()
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


    instantiate_LowMC()
    keyschedule()

    return encrypt
