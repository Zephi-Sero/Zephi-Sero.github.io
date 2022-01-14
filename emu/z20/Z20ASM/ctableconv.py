import argparse
hexchars = "0123456789ABCDEF"
def hex_from_idx(idx):
    return hexchars[idx // 16] + hexchars[idx % 16]
def to_csv(infile, outfile):
    pass
def to_ctable(infile,outfile):
    file_in = open(infile)
    file_out = open(outfile,"w")
    line = file_in.readline().strip()
    pfx = {}
    nonpfx = []
    curr_pfx = None
    while line != '':
        split = line.split(",")
        if line[0] not in "0123456789ABCDEFabcdef" and not split[0].startswith("Preceded:"):
            line = file_in.readline()
            continue
        elif split[0].startswith("Preceded:"):
            curr_pfx = split[0][10:]
            line = file_in.readline()
            continue
        if curr_pfx:
            if curr_pfx in pfx:
                pfx[curr_pfx] += split[1:]
            else:
                pfx[curr_pfx] = split[1:]
        else:
            nonpfx += split[1:]
        line = file_in.readline().strip()
    for i in range(len(nonpfx)):
        byte = hex_from_idx(i)
        if byte in pfx:
            nonpfx[i] = ""
    for i in pfx:
        for j in range(len(pfx[i])):
            file_out.write(i + hex_from_idx(j) + "=" + pfx[i][j].strip() + "\n")
    for i in range(len(nonpfx)):
        if nonpfx[i] == "":
            continue
        file_out.write(hex_from_idx(i) + "=" + nonpfx[i].strip() + "\n")
    file_out.close()
    file_in.close()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compilation table + CSV conversion tool.")
    parser.add_argument("infile",metavar="in",type=str,help="Input file")
    parser.add_argument("outfile",metavar="out",type=str,help="Output file")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--to-csv", dest="operate", action="store_const", const=to_csv)
    operation.add_argument("--to-ctable", dest="operate", action="store_const", const=to_ctable)
    args = parser.parse_args()
    args.operate(args.infile, args.outfile)