import argparse
import re
numerical = "0123456789abcdefABCDEFxX"
def compilation_table():
    compfile = open("lookup.ctable","r")
    lines = compfile.readlines()
    tb = {}
    for line in lines:
        tb["".join(line.split("=")[1:]).strip()] = line.split("=")[0].strip()
    return tb
def decompilation_table():
    compfile = open("lookup.ctable","r")
    lines = compfile.readlines()
    tb = {}
    for line in lines:
        tb[line.split("=")[0].strip()] = "".join(line.split("=")[1:]).strip()
    return tb
def conv_number(num):
    num = num.lower()
    if num.startswith("$"):
        return int(num[1:],16)
    elif num.startswith("0x"):
        return int(num[2:],16)
    elif num.startswith("0b"):
        return int(num[2:],2)
    elif num.startswith("0"):
        return int(num[1:],8)
    else:
        return int(num,10)
def hexify_number(num):
    return hex(num)[2:].rjust(2,"0").upper()
def sanitize_asm(line):
    return line.split(";")[0].strip()
def compile(infile, outfile, environment=None):
    file_in = open(infile)
    comptab = compilation_table()
    number_grabber = re.compile(r"(0[xX][0-9a-fA-F]+)|(\$[0-9a-fA-F]+)|(0[\d]+)|(0[bB][01]+)|([1-9]\d?)|0")
    string_grabber = re.compile(r"((?:[^\\^\[ ,]?)('[^\0]*?[^\\]')|(?:[^\\^\[ ,]?)(\"[^\0]*?[^\\]\"))|((0[xX][0-9a-fA-F]+)|(\$[0-9a-fA-F]+)|(0[\d]+)|(0[bB][01]+)|([1-9]\d?)|0)")
    preprocessor_grabber = re.compile(r"#\w*")
    linenum = 0
    output = []
    if environment:
        if not "constants" in environment:
            environment["constants"] = {}
        if not "delayedconstants" in environment:
            environment["delayedconstants"] = {}
    else:
        environment = {"constants":{},"delayedconstants":{}}
    lines = file_in.readlines()
    for pureline in lines:
        line = sanitize_asm(pureline)
        linenum += 1
        if line == '':
            continue
        if line.startswith("#"): # Preprocessor instruction
            preinstr = line.upper()[1:]
            if preinstr.startswith("LABEL") or preinstr.startswith("LBL"):
                lblname = preinstr.split(" ")[1]
                if lblname in environment["constants"]:
                    offset = preinstr.index(" ")+1
                    raise SyntaxError("Label already created", (infile,linenum+1,offset+1,line,linenum+1,offset+len(lblname)+1))
                else:
                    environment["constants"][lblname] = len(output)
            elif preinstr.startswith("DEFINE") or preinstr.startswith("DEF"):
                varname = preinstr.split(" ")[1]
                if varname in environment["constants"]:
                    offset = preinstr.index(" ")+1
                    raise SyntaxError("Label already created", (infile,linenum+1,offset+1,line,linenum+1,offset+len(varname)+1))
                else:
                    environment["constants"][varname] = conv_number(preinstr.split(" ")[2])
            elif preinstr.startswith("INCLUDE") or preinstr.startswith("INC"):
                filename = line.split(" ")[1]
                splitfile = filename.split(".")
                if splitfile[len(splitfile)-1].lower() == "z20asm":
                    compiled_file = compile(filename, None,environment)
                    output += compiled_file
        elif line.startswith('[') and line.endswith(']'):
            for res in string_grabber.finditer(line):
                res = line[res.start():res.end()]
                if (res.startswith("'") and res.endswith("'")) or (res.startswith('"') and res.endswith('"')):
                    for ch in res[1:-1]:
                        output.append(ord(ch))
                    output.append(0)
                else:
                    output.append(conv_number(res))
        elif line in comptab:
            output.append(conv_number("0x" + comptab[line]))
        else:
            num_data = number_grabber.search(line)
            if num_data == None:
                output.append(conv_number("0x"+comptab[preprocessor_grabber.sub("I",line)]))
                matcher = preprocessor_grabber.search(line)
                label = line[matcher.start()+1:matcher.end()].upper()
                print(label)
                if label in environment["constants"]:
                    output.append(environment["constants"][label])
                else:
                    if label in environment["delayedconstants"]:
                        environment["delayedconstants"][label].append(len(output))
                    else:
                        environment["delayedconstants"][label] = [len(output)]
                    output.append(0)
            else:
                output.append(conv_number("0x"+comptab[number_grabber.sub("I",line)]))
                output.append(conv_number(line[num_data.start():num_data.end()].lower()))
    for label in environment["delayedconstants"]:
        for replaceidx in environment["delayedconstants"][label]:
            output[replaceidx] = environment["constants"][label]
    if outfile:
        outstr = "["
        for byte in output:
            outstr += "0x" + hex(byte)[2:].rjust(2,"0") + ","
        outstr = outstr[:-1] + "]"
        print(outstr)
        file_out = open(outfile,"wb")
        file_out.write(bytes(output))
        file_out.close()
    else:
        return output
def decompile(infile, outfile):
    file_in = open(infile,"rb")
    comptab = decompilation_table()
    data = file_in.read(1)
    imm = False
    pfx = False
    instr = ""
    imm_finder = re.compile(r"\bI\b")
    output = ""
    while data != b'':
        if not imm:
            if pfx:
                instr = comptab["88" + data.hex().upper()]
                output += instr + "\n"
                pfx = False
            else:
                if data.hex == "88":
                    pfx = True
                else:
                    instr = comptab[data.hex().upper()]
                if imm_finder.search(instr):
                    imm = True
                else:
                    output += instr + "\n"
        else:
            output += imm_finder.sub("$" + data.hex().upper(),instr) + "\n"
            imm = False
        data = file_in.read(1)
    file_out = open(outfile,"w")
    file_out.write(output)
    file_out.close()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Z20ASM assembly/decompilation tool.")
    parser.add_argument("infile",metavar="in",type=str,help="Input file")
    parser.add_argument("outfile",metavar="out",type=str,help="Output file")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("-c", "--compile", "-a", "--assemble", dest="operate", action="store_const", const=compile, default=compile)
    operation.add_argument("-d", "--decompile", "--disassemble", dest="operate", action="store_const", const=decompile, default=compile)
    args = parser.parse_args()
    args.operate(args.infile, args.outfile)