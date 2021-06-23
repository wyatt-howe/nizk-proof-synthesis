#
# LowMC functions
#

def encrypt(message: block):  # -> block
    c = message ^ roundkeys[0]
    for r in range(rounds):
        c =  Substitution(c)
        c =  MultiplyWithGF2Matrix(LinMatrices[r], c)
        c = c ^ roundconstants[r]
        c = c ^ roundkeys[r+1]

    return c


def decrypt(message: block):  # -> block
    c = message
    for r in reversed(range(rounds)):
        c = c ^ roundkeys[r+1]
        c = c ^ roundconstants[r]
        c = MultiplyWithGF2Matrix(invLinMatrices[r], c)
        c = invSubstitution(c)
    c = c ^ roundkeys[0]

    return c


def set_key (k: keyblock):  # -> void
    key = k
    keyschedule()


#
# LowMC private functions
#


def Substitution(message: block):  # -> block
    temp = 0

    # Get the identity part of the message
    temp = temp ^ (message >> 3*numofboxes)

    # Get the rest through the Sboxes
    for i in range(numofboxes):
        temp = temp << 3
        idx = (message >> 3*(numofboxes-i-1)) & block(0x7)
        temp = temp ^ Sbox[idx]

    return temp


def invSubstitution(message: block):  # -> block
    temp = 0

    # Get the identity part of the message
    temp = temp ^ (message >> 3*numofboxes)

    # Get the rest through the invSboxes
    for i in range(numofboxes):
        temp = temp << 3
        idx = (message >> 3*(numofboxes-i-1)) & block(0x7)
        temp = temp ^ invSbox[idx]

    return temp


def MultiplyWithGF2Matrix(matrix, message):  # -> block
    temp = 0
    for i in range(blocksize):
        temp[i] = (message & matrix[i]).count() % 2
    return temp


def MultiplyWithGF2Matrix_Key(matrix, k):  # -> block
    temp = 0
    for i in range(blocksize):
        temp[i] = (k & matrix[i]).count() % 2
    return temp


def keyschedule():  # -> void
    roundkeys.clear()
    for r in range(rounds):
        roundkeys.push_back(
            MultiplyWithGF2Matrix_Key(KeyMatrices[r], key)
        )

    return


def instantiate_LowMC():  # -> void
    # Create LinMatrices and invLinMatrices
    LinMatrices.clear()
    invLinMatrices.clear()
    for r in range(rounds):
        # Create matrix
        mat = std.vector<block>

        # Fill matrix with random bits
        while True:
            mat.clear()
            for i in range(blocksize):
                mat.push_back(
                    getrandblock()
                )

            # Done if matrix is invertible
            if rank_of_Matrix(mat) == blocksize:
                break

        LinMatrices.push_back(mat)
        invLinMatrices.push_back(invert_Matrix (LinMatrices.back()))

    # Create roundconstants
    roundconstants.clear()
    for r in range(rounds):
        roundconstants.push_back(
            getrandblock()
        )

    # Create KeyMatrices
    KeyMatrices.clear()
    for r in range(rounds+1):
        # Create matrix
        mat = std.vector<keyblock>

        # Fill matrix with random bits
        while True:
            mat.clear()
            for i in range(blocksize):
                mat.push_back(
                    getrandkeyblock()
                )

            # Repeat unless matrix is of maximal rank
            if rank_of_Matrix_Key(mat) >= std.min(blocksize, keysize):
                break

        KeyMatrices.push_back(mat)

    
    return


#
# Binary matrix functions
#


def rank_of_Matrix(matrix):   # -> unsigned
    # Copy of the matrix
    mat = std.vector<keyblock>
    for u in matrix:
        mat.push_back(u)

    size = mat[0].size()

    # Transform to upper triangular matrix
    row = 0
    for col in range(size):
        if not mat[row][size-col-1]:
            r = row
            while r < mat.size() and not mat[r][size-col-1]:
                r = r + 1

            if r >= mat.size():
                continue
            else:
                temp = mat[row]
                mat[row] = mat[r]
                mat[r] = temp

        for i in range(row+1, mat.size()):
            if mat[i][size-col-1]:
                mat[i] = mat[i] ^ mat[row]

        row = row + 1
        if row == size:
            break

    return row


def rank_of_Matrix_Key(matrix):  # -> unsigned
    # Copy of the matrix
    mat = std.vector<keyblock>
    for u in matrix:
        mat.push_back(u)

    size = mat[0].size()

    # Transform to upper triangular matrix
    row = 0
    for col in range(size):
        if not mat[row][size-col-1]:
            r = row
            while r < mat.size() and not mat[r][size-col-1]:
                r = r + 1

            if r >= mat.size():
                continue
            else:
                temp = mat[row]
                mat[row] = mat[r]
                mat[r] = temp

        for i in range(row+1, mat.size()):
            if mat[i][size-col-1]:
                mat[i] = mat[i] ^ mat[row]

        row = row + 1
        if row == size:
            break

    return row


def invert_Matrix(matrix):  # -> std.vector<block>
    # Copy of the matrix
    mat = std.vector<keyblock>
    for u in matrix:
        mat.push_back(u)

    # Initialize to hold the inverted matrix
    invmat = std.vector<block>(blocksize, 0)
    for i in range(blocksize):
        invmat[i][i] = 1

    size = mat[0].size()

    # Transform to upper triangular matrix
    row = 0
    for col in range(size):
        if not mat[row][col]:
            r = row + 1
            while r < mat.size() and not mat[r][col]:
                r = r + 1

            if r >= mat.size():
                continue
            else:
                temp = mat[row]
                mat[row] = mat[r]
                mat[r] = temp
                temp = invmat[row]
                invmat[row] = invmat[r]
                invmat[r] = temp

        for i in range(row + 1, mat.size()):
            if mat[i][col]:
                mat[i] = mat[i] ^ mat[row]
            invmat[i] = invmat[i] ^ invmat[row]

        row = row + 1


    # Transform to identity matrix
    for col in reversed(range(size)):
            for r in range(col):
                if mat[r][col]:
                    mat[r] = mat[r] ^ mat[col]
                invmat[r] = invmat[r] ^ invmat[col]

    return invmat


#
# Pseudorandom bits
#


def getrandblock()  # -> block
    tmp = 0
    for i in range(blocksize):
        tmp[i] = getrandbit()
    return tmp


def getrandkeyblock()# -> block
    tmp = 0
    for i in range(keysize):
        tmp[i] = getrandbit()
    return tmp


# Uses the Grain LSFR as self-shrinking generator to create pseudorandom bits
# Is initialized with the all 1s state
# The first 160 bits are thrown away
def getrandbit():  # -> bool
    # Keeps the 80 bit LSFR state
    state = std.bitset<80>;

    tmp = 0

    # If state has not been initialized yet
    if state.none():
        state.set() # Initialize with all bits set

        # Throw the first 160 bits away
        for _ in range(160):
            # Update the state
            tmp = state[0] ^ state[13] ^ state[23] ^ state[38] ^ state[51] ^ state[62]
            state = state >> 1
            state[79] = tmp

    # Choice records whether the first bit is 1 or 0.
    # The second bit is produced if the first bit is 1.
    choice = False
    while True:
        # Update the state
        tmp = state[0] ^ state[13] ^ state[23] ^ state[38] ^ state[51] ^ state[62]
        state = state >> 1
        state[79] = tmp
        choice = tmp
        tmp = state[0] ^ state[13] ^ state[23] ^ state[38] ^ state[51] ^ state[62]
        state = state >> 1
        state[79] = tmp

        if choice:
            break

    return tmp


