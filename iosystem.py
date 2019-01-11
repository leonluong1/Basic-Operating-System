import struct


#FILE DESCRIPTORS: contained in first k disk blocks(ldisk[1:k])
#Each contains: length (bytes) and a list of 3 blocks (stores 192 bytes max)
#Represents a free fd by making length = 193 (or 1 + max length)
#fd contains four integers. fd 0 is reserved for directory

#BLOCK: contained in ldisk[k:64](exclusive) contains data

#OFT: Fixed length byte array where each entry has following form:
#Read/write buffer, current position of open file, fd index on disk, length
#OFT entry = 0 is always directory
#Each entry has length (64 + 4 + 4 + 4) = 76 bytes

#DIRECTORY: Implement as reg. file so we can read(), write(), lseek()
#Never explicitly created or destroyed. When no files initially, directory is
#length 0 with no blocks allocated. Internally implemented as an unsorted array
#of fixed-sized slots. each slot contains fname and fd


def bts(data_struct, index):
    return data_struct[index:index+4].decode("ascii")

def bti(data_struct, index):
    return int.from_bytes(data_struct[index:index+4], "big")

def stb(string):
    return string[0:4].encode("ascii")

def itb(integer):
    return struct.pack(">I", integer)

def insert_str(string, data_struct, index):
    data_struct[index:index+4] = stb(string)
    return 0

def insert_int(integer, data_struct, index):
    data_struct[index:index+4] = itb(integer)
    return 0


#I/O SYSTEM

#L(first number) = number of logical blocks
#B(second number) = block length (in bytes)
#L = 64   #B = 64   #K = 7
#First block(byte 0-63) is bitmap, next 6(byte 64-383) are fd's

ldisk = bytearray(4096)
oft = bytearray(304)
bm = bytearray(64)
fdc = bytearray(68)

def bitmap():
    BM0 = bin(bti(bm, 0))[2:][::-1]
    BM1 = bin(bti(bm, 4))[2:][::-1]
    BM0 = str(BM0) + "0"*(32-len(BM0))
    BM1 = str(BM1) + "0"*(32-len(BM1))
    return BM0+BM1


def print_block(index):
    print("Block {}(LDISK)".format(index), ldisk[64*index:64*index+64])

def print_fd():
    print("FILE DESCRIPTORS(LDISK)", ldisk[64:384])

def print_ofte(i):
    print("OFT Entry {}(OFT)".format(i), oft[i*76:i*76+76])

def print_fdc():
    print("FD CACHE(FDC)", fdc[0:68])


#Restore ldisk from file or create new (if no file)

#A: Wipe ldisk and oft
#B: Go through all the fd's and makes length = 193 to show its free
#(except fd 0 because thats the directory)
#C: Allocate the first k blocks for bitmap and file descriptors
#D: Read file byte by byte to create the file
#E: Allocate bitmap from disk   #F: Make oft entries (except entry 0)
#length = 193 to free them   #G: Set up fd cache
def init(disk = ""):
    result = 'r'
    if (disk == ""):
        for i in range(0, 4096): #A
            ldisk[i] = 0
        for i in range(0, 304): #A
            oft[i] = 0
        result = 'i'
        for i in range(1,24): #B
            insert_int(193, ldisk, 64+i*16)
        for i in range(0,7): #C
            allocate_block(24, 0)
        write_block(0, bm)
    else:
        n = 0
        file = open(disk, "r") #D
        for line in file:
            ldisk[n] = int(line)
            n+=1
        read_block(0, bm) #E
            
    for j in range(1,4): #F
        insert_int(193, oft, j*76+72)
    read_block(1, fdc) #G
    insert_int(1, fdc, 64)
    return result


#Save disk to file
def save(disk):
    write_block(bti(fdc, 64), fdc)
    write_block(0, bm)
    file = open(disk, "w")
    for byte in ldisk:
        file.write("{}\n".format(str(int(byte))))       
    return 0


#i = block number, p = position
#Reads a block from ldisk to an OFT entry. write_block() does the opposite
def read_block(i, p):
    n = 0
    if (type(p) == int):
        while (n < 64):
            oft[p*76+n] = ldisk[i*64+n]
            n +=1
    else:
        p[0:64] = ldisk[i*64:i*64+64]
    return 0


def write_block(i, p):
    n = 0
    while (n < 64):
        ldisk[i*64+n] = p[n]
        n+=1
    return 0


def read_fdc(fdn, index):
    if (int(fdn/4)+1 != bti(fdc, 64)):
        write_block(bti(fdc, 64), fdc)
        read_block(int(fdn/4)+1, fdc)
        insert_int(int(fdn/4)+1, fdc, 64)
        
    return bti(fdc, (fdn%4)*16+index)

    
def write_fdc(integer, fdn, index):
    if (int(fdn/4)+1 != bti(fdc, 64)):
        write_block(bti(fdc, 64), fdc)
        read_block(int(fdn/4)+1, fdc)
        insert_int(int(fdn/4)+1, fdc, 64)
        
    insert_int(integer, fdc, (fdn%4)*16+index)
    return 0


def ofte_buff(index):
    return oft[index*76:index*76+64]


#Adds lowest free block number to the bitmap. deallocate_block() deallocates i

#A: Goes through bitmap bit by bit   #B: Checks which half of bitmap to choose
#C: Indicates whether to write the block number to fd
def allocate_block(fdn, index):
    full=True
    for i,b in enumerate(bitmap()): #A
        if (b == '0'):
            full=False
            if (int(i/32) == 0): #B
                insert_int(bti(bm, 0)|int(1 << int(i%32)), bm, 0)
            else:
                insert_int(bti(bm, 4)|int(1 << int(i%32)), bm, 4)
            if (fdn < 24): #C
                write_fdc(i, fdn, index)
            return 0, i
    if (full):
        return 1, 0
    

def deallocate_block(i, fdn, index):
    if (i > 63):
        return 1
    if (int(i/32) == 0):
        insert_int(bti(bm, 0)&~int(1 << int(i%32)), bm, 0)
    else:
        insert_int(bti(bm, 4)&~int(1 << int(i%32)), bm, 4)
    if (fdn < 24): 
        write_fdc(0, fdn, index)
    return 0

