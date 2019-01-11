import iosystem as io
import filesystem as fs


def full_str(string):
    return string + " "*(4-len(string))


def is_int(i):
    try: 
        int(i)
        return True
    except ValueError:
        return False


def cr(out, fname):
    if (len(fname) > 4):
        out.write("error\n")
        return 1
    i = fs.create(full_str(fname))
    if (i == 0):
        out.write("{} created\n".format(fname))
    else:
        out.write("error\n")
        return 1
    return 0


def de(out, fname):
    if (len(fname) > 4):
        out.write("error\n")
        return 1
    i = fs.destroy(full_str(fname))
    if (i == 0):
        out.write("{} destroyed\n".format(fname))
    else:
        out.write("error\n")
        return 1
    return 0


def op(out, fname):
    if (len(fname) > 4):
        out.write("error\n")
        return 1
    index = fs.open_file(full_str(fname))
    if (index < 4):
        out.write("{} opened {}\n".format(fname, index))
    else:
        out.write("error\n")
        return 1
    return 0


def cl(out, index):
    if (not(is_int(index))):
        out.write("error\n")
        return 1
    index = int(index)
    i = fs.close_file(index)
    if (i == 0):
        out.write("{} closed\n".format(index))
    else:
        out.write("error\n")
        return 1
    return 0


def rd(out, index, count):
    if (not(is_int(index) and is_int(count))):
        out.write("error\n")
        return 1
    index = int(index)
    count = int(count)
    mem = bytearray(192)
    nread = fs.read(index, mem, count)
    if (nread < 193):
        out.write(mem[0:count].decode("ascii"))
        out.write("\n")
    else:
        out.write("error\n")
        return 1
    return 0


def wr(out, index, char, count):
    if (not(is_int(index) and is_int(count))):
        out.write("error\n")
        return 1
    index = int(index)
    count = int(count)
    mem = bytearray(192)
    for i in range(0, count):
        io.insert_str(char, mem, i)
    nwrite = fs.write(index, mem, count)
    if (nwrite < 193):
        out.write("{} bytes written\n".format(nwrite))
    else:
        out.write("error\n")
        return 1
    return 0


def sk(out, index, pos):
    if (not(is_int(index) and is_int(pos))):
        out.write("error\n")
        return 1
    index = int(index)
    pos = int(pos)
    i = fs.lseek(index, pos, False)
    if (i == 0):
        out.write("position is {}\n".format(pos))
    else:
        out.write("error\n")
        return 1
    return 0


def dr(out):
    files = fs.directory()
    for file in files:
        out.write("{} ".format(file))
    out.write("\n")
    return 0


def ind(out, disk=""):
    result = io.init(disk)
    if (result == 'i'):
        out.write("disk initialized\n")
    else:
        out.write("disk restored\n")
    return 0


def sv(out, disk):
    for i in range(0,4):
        fs.close_file(i)
    io.save(disk)
    out.write("disk saved\n") 
    return 0


def parse(out, l):
    if (len(l) == 0):
        out.write("\n")
    elif (l[0] == "cr" and len(l) == 2):
        cr(out, l[1])
    elif (l[0] == "de" and len(l) == 2):
        de(out, l[1])
    elif (l[0] == "op" and len(l) == 2):
        op(out, l[1])
    elif (l[0] == "cl" and len(l) == 2):
        cl(out, l[1])
    elif (l[0] == "rd" and len(l) == 3):
        rd(out, l[1], l[2])
    elif (l[0] == "wr" and len(l) == 4):
        wr(out, l[1], l[2], l[3])
    elif (l[0] == "sk" and len(l) == 3):
        sk(out, l[1], l[2])
    elif (l[0] == "dr" and len(l) == 1):
        dr(out)
    elif (l[0] == "in" and len(l) <= 2):
        ind(out) if len(l) == 1 else ind(out, l[1])
    elif (l[0] == "sv" and len(l) == 2):
        sv(out, l[1])
    else:
        out.write("error\n")
        return 1
    return 0

def get_file():
    while True:
        try:
            fpath = input()
            pindex = fpath.rfind('\\')
            infile = open(fpath, "r")
            break
        except:    
            print("error\n")
    return fpath, pindex, infile

def main():
    fpath, pindex, infile = get_file()
    if (pindex == -1):
        out = open("69139013.txt", "w")
    else:
        out = open("{}69139013.txt".format(fpath[0:pindex+1]), "w")
    for line in infile:
        parse(out, line.split())
    out.close()
    return 0


main()
