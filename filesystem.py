import iosystem as io


#FILE SYSTEM

#Finds free fd. Finds free dir entry. Verifies if file doesn't already exist.
#Else, return error. Enter fname and fd in dir entry. then return status

#A: Looks through fd's (except fd 0) to find free fd.
#B: Used to store free dir entry. Equals 24 because that is above max fd number
#C: Gets first dir block before we start searching
#D: Loops through directory slots
#E: Stores free dir entry.   #F: Checks to see if file already in directory
#G: After looping through all entries, check if free entry was found
#H: Changes dir pos to free entry pos   #I: Writes fname and fd to dir entry
#J: Inserts length = 0 to file descriptor on disk which occupies it
def create(fname):
    for fdn in range(1,24): #A
        if (io.read_fdc(fdn, 0) == 193):
            entry = 24 #B 
            lenlimit = False
            lseek(0, 0, True) #C
            slot = bytearray(8)
            n = 0
            for j in range(0,24):
                n = j
                if (io.bti(io.oft, 72) == 0):
                    entry = j
                    break
                if (lenlimit == False and read(0, slot, 8) == 0): #D
                    lenlimit = True
                if (entry == 24 and (io.bti(slot, 0) == 0)): #E
                    entry = j
                elif (io.bts(slot, 0) == fname): #F
                    return 1
                if (entry == 24 and j < 23 and lenlimit):
                    entry = j
                    break
            if (entry == 24): #G
                return 1
            lseek(0, entry*8, True) #H
            write(0, io.stb(fname)+io.itb(fdn), 8) #I
            io.write_fdc(0, fdn, 0) #J
            return 0
    return 1


#Assume file closed. Remove dir entry by going to directory searching for fname
#Go to that fd and free all its blocks n bitmap

#A: Check if file is in directory   #B: fd num of dir entry
#C: Frees fd by making length = 193   #D: Deallocates blocks in bitmap.
#E: Frees directory entry
def destroy(fname):
    lseek(0,0, False)
    slot = bytearray(8)
    for entry in range(0,24):
        read(0, slot, 8)
        if (io.bts(slot, 0) == fname): #A
            fdn = io.bti(slot, 4) #B
            io.write_fdc(193, fdn, 0) #C
            for bn in [4, 8, 12]:
                blockn = io.read_fdc(fdn, bn)
                if (blockn > 0):
                    io.deallocate_block(blockn, fdn, bn) #D
            lseek(0, entry*8, False)
            io.insert_int(0, io.oft, (entry%8)*8) #E
            io.insert_int(0, io.oft, (entry%8)*8+4) #E
            return 0
    return 1


#Search dir for fd. Allocate free oft entry, fill in curr. pos 0 and fd,
#Read block 0 of file to buffer. Return oft index

#A: Check directory for file   #B: Check if file already in oft
#C: Look through oft for free entry   #D: If no free oft entries, return error
#E: Insert pos = 0, fdn, and file length to last three slots of entry
#F: Read 1st block into oft entry and return entry number (if allocated)
def open_file(fname):
    lseek(0,0, False)
    slot = bytearray(8)
    for i in range(0,24):
        read(0, slot, 8)
        if (io.bts(slot, 0) == fname): #A
            fdn = io.bti(slot, 4) 
            index = 4
            for j in range(1,4):
                if (io.bti(io.oft, j*76+68) == fdn): #B
                    return 1
                elif (index == 4 and io.bti(io.oft, j*76+72) == 193): #C
                    index = j
            if (index == 4): #D
                return 4
            io.insert_int(0, io.oft, index*76+64) #E
            io.insert_int(fdn, io.oft, index*76+68) #E
            io.insert_int(io.read_fdc(fdn, 0), io.oft, index*76+72) #E
            blockn = io.read_fdc(fdn, 4)
            if (blockn > 0):
                io.read_block(blockn, index) #F
            return index
    return 4


#Write buffer to disk. Update length in fd. Free oft entry. Return status

#A: Check to see if entry in range and if entry not already closed
#B: Get fdn and position from entry
#C: Find which block to write to using position   #D: Write block to disk
#E: Update length in fd    #F free oft entry
def close_file(index):
    if (index > 3 or io.bti(io.oft, index*76+72) == 193): #A
        return 1
    fdn = io.bti(io.oft, index*76+68) #B
    pos = io.bti(io.oft, index*76+64) #B
    bn = 4 if int(pos/64) == 0 else 8 if int(pos/64) == 1 else 12 #C
    blockn =  io.read_fdc(fdn, bn)
    io.write_block(blockn, io.ofte_buff(index)) #D
    io.write_fdc(io.bti(io.oft, index*76+72), fdn, 0) #E
    if (index > 0):
        io.insert_int(0, io.oft, index*76+68) #F
        io.insert_int(193, io.oft, index*76+72) #F
    return 0


#index = fd num, mem_area = oft entry to read from/write to
#count = number of bytes to read from/write to
#Compute position of buffer using position of file
#Copy bytes from mem_area to buffer until something happens:
#If the desired count or eof has been reached, update position
#If end of buffer is reached, write buffer and get next block to continue

#A: Checks if file is open   #B: Get file length - pos (0 if negative)
#C: Stop when count is reached or the file length is reached.
#D: Transfer from buffer to mem_area byte by byte
#E: If the buffer is reached, get the next disk
def read(index, mem_area, count):
    if (io.bti(io.oft, index*76+72) == 193): #A
        return 193
    pos = io.bti(io.oft, index*76+64)
    bn = 4 if int(pos/64) == 0 else 8 if int(pos/64) == 1 else 12
    readmax = io.bti(io.oft, index*76+72)-pos #B
    nread = min(count, readmax)
    for j in range(0, nread): #C
        mem_area[j] = io.oft[index*76+pos%64] #D
        pos += 1
        lseek(index, pos, False) #E
    return nread


#copy bytes from main memory to buffer
#if end of buffer is reached, allocate new block
#file desc and bitmap must be updated because new block was allocated

#A: Stop when count or max length is reached
#B: Transfer from mem_area to buffer byte by byte
#C file length in oft (if length > 192, cut it off)
def write(index, mem_area, count):
    flen = io.bti(io.oft, index*76+72)
    if (flen == 193):
        return 193
    pos = io.bti(io.oft, index*76+64)
    bn = 4 if int(pos/64) == 0 else 8 if int(pos/64) == 1 else 12
    nwrite = min(count, 192-pos)
    for j in range(0, nwrite): #A
        io.oft[index*76+pos%64] = mem_area[j] #B
        pos += 1
        lseek(index, pos, True)
    io.insert_int(min(flen+nwrite, 192), io.oft, index*76+72) #C
    return nwrite


#index = fd num. pos = position of file to move to
#If new position is not in buffer, write to current block and allocate desired
#block. Either way, change current position to new positon

#A: If 1st block is unallocated, alllocate it
#B: Check if position of current block and new block are the same
#C: Get the current block number. Then write to it.
#D: Get next block number   #E: Check if next block is unallocated
#F: Go through bitmap to find a free block to allocate
#G: If next block is already allocated, retrieve it.   #H: Update position
def lseek(index, pos, overlim):
    flen = io.bti(io.oft, index*76+72)
    if ((not overlim and pos > flen) or flen == 193):
        return 1
    curr = io.bti(io.oft, index*76+64)
    cbn = 4 if int(curr/64) == 0 else 8 if int(curr/64) == 1 else 12
    fdn = io.bti(io.oft, index*76+68)
    if (io.read_fdc(fdn, cbn) == 0): #A
        io.allocate_block(fdn, 4)
    else:
        if (int(pos/64) != int(curr/64)): #B
            io.write_block(io.read_fdc(fdn, cbn), io.ofte_buff(index)) #C
            bn = 4 if int(pos/64) == 0 else 8 if int(pos/64) == 1 else 12
            blockn = io.read_fdc(fdn, bn) #D
            if (blockn == 0): #E
                c = io.allocate_block(fdn, bn) #F
                if (c[0] == 0 and overlim == True):
                    io.read_block(c[1], index)
            else:
                io.read_block(blockn, index) #G
    io.insert_int(pos, io.oft, index*76+64) #H
    return 0


#List all file names
def directory():
    lseek(0,0, False)
    slot = bytearray(8)
    files = []
    for i in range(0, 24):
        read(0, slot, 8)
        fname = io.bts(slot, 0)
        if (fname in files):
            break
        if (io.bti(slot, 0) != 0):
            files.append(fname)
    return files

