#Convert Pydis opcode to python script
#Author : Chim
#Mail: trichimtrich@gmail.com
#Date : 08/05/2014
#Script ver: 1.0

############################################

#THIS IS IMPORTANT, please do not change name or contents of this file. In that case, I'm not sure if it doesn't workout!
op_file = "Oops.txt"
def Load_OP(fn):
    try:
        f = open(fn,'r').read().split('\n')
        op_table = []
        for line in f:
            if line=='': continue
            if line[0] not in ['0','1','2']: continue
            op_tmp = line.split('||')
            op_table.append(op_tmp)

        print "[+] Loading Opcode Table ---- OK!\n"
        return op_table
    except:
        print "[-] Error while loading Opcode Table"
        exit()

###### Nothing to write here :(
def Parse_Input(fn):
    try:
        f = open(fn,'r').read().split('\n')
    except:
        print "[-] Error while reading input file!"
        exit()

    inp = []
    for line in f:
        tmp = line.split()
        s_tmp = len(tmp)
        ind = 0

        #search index for offset and opcode name
        while ind<s_tmp-1 and \
                (not tmp[ind].isdigit() or tmp[ind+1].isdigit() or tmp[ind+1]==">>"): ind+=1
        if ind>=s_tmp-1: continue   #not found, move to next line

        #check in opcode table
        flag = False
        for op in op_table:
            if tmp[ind+1]==op[1]:
                flag = True
                break
        if flag == False:
            print line
            print "[-] Error: Input Opcode not found! Please check out or report to my mail: trichimtrich@gmail.com"
            exit()

        #append first two elements
        inp_add = []
        inp_add.append(tmp[ind])
        inp_add.append(tmp[ind+1])

        #search for the next elements
        if ind < s_tmp-2:
            inp_add.append(tmp[ind+2])
            ind += 3
            s = ""
            while ind<s_tmp:
                if tmp[ind]!="(to":
                    s += tmp[ind] + ' '
                ind += 1
            s = s.strip('( )')
            if s!="":
                inp_add.append(s)


        #seem everything okey, add parsed line to input table
        inp.append(inp_add)
        print inp_add

    print "[+] Parsing Input ---- OK!\n"
    return inp

#Pop value from stack and replace in format-string
def popStack(stack, text, op):
    text_tmp = text.split('%s')

    num_s = len(text_tmp)-1
    text = text_tmp[num_s]
    while num_s>0:
        num_s-=1
        stack_tmp = stack.pop()
        if stack_tmp[1]!='99' and op[2]<stack_tmp[1]:
            text = text_tmp[num_s] + '(' + stack_tmp[0] + ')' + text
        else:
            text = text_tmp[num_s] + stack_tmp[0] + text

    return stack, text

def Decode(op_table, inp, stack, tab):
    line = 0
    out = ""
    print_tmp = ""
    tab_tmp = []
    else_tmp = []
    start_loop = False
    while line<len(inp):
        cmd = inp[line]
        line+=1

        if cmd[0] in tab_tmp:
            tab = tab - tab_tmp.count(cmd[0])
            tab_tmp.remove(cmd[0])
        if cmd[0] in else_tmp:
            out += '\t'*(tab-1) + "else:\n"
            else_tmp.remove(cmd[0])

        for op in op_table:
            if op[1] == cmd[1]: break
        if (op[1]!=cmd[1]): continue

        #Informal operation code, need to process manual
        if op[0]=='2':
            if op[1] in ["CALL_FUNCTION","BUILD_LIST","BUILD_TUPLE"]:
                if cmd[2]=='0': text = ""
                else: text = '%s' + ',%s'*(int(cmd[2])-1)
                if op[1] == "BUILD_LIST": text = '[' + text + ']'
                elif op[1] == "BUILD_TUPLE": text = '(' + text + ')'
                elif op[1] == "CALL_FUNCTION": text = '%s(' + text + ')'
                stack, text = popStack(stack, text, op)
                stack.append( (text, op[2]) )

            if op[1] == "POP_TOP":
                stack.pop()

            if op[1] == "PRINT_ITEM":
                if print_tmp=='': print_tmp = stack.pop()[0]
                else: print_tmp = stack.pop()[0] + ', ' + print_tmp
            if op[1] == "PRINT_NEWLINE":
                out += '\t'*tab + "print " + print_tmp + '\n'
                print_tmp = ""

            if op[1] == "POP_JUMP_IF_FALSE":
                text = stack.pop()[0]
                if start_loop:
                    out += '\t'*tab + "while " + text + ':\n'
                    start_loop = False
                else:
                    out += '\t'*tab + "if " + text + ':\n'
                    if cmd[2] not in tab_tmp: else_tmp.append(cmd[2])
                tab = tab + 1

            if op[1] in ["JUMP_FORWARD","SETUP_LOOP"]:
                addr = cmd[3]
                if addr in else_tmp: else_tmp.remove(addr)
                tab_tmp.append(addr)
                start_loop = op[1]=="SETUP_LOOP"

            if op[1] == "FOR_ITER":
                next_store = inp[line]
                line +=1
                if next_store[2]==next_store[3]:
                    out += '\t'*tab + "for v" + next_store[2] + " in " + stack.pop()[0] + ":\n"
                else:
                    out += '\t'*tab + "for " + next_store[3] + " in " + stack.pop()[0] + ":\n"
                tab += 1
                start_loop = False

            if op[1] == "BREAK_LOOP":
                out += '\t'*tab + "break\n"

        else:
            #Formal code, using opcode table string to auto-process
            text = op[3]

            #Check for alternative name of variable, const or func
            if len(cmd)>=4 and cmd[3]!=cmd[2]:
                text = op[4]

            if text.find('%d')>=0:
                text = text.replace('%d', cmd[2])
            if text.find('%e')>=0:
                text = text.replace('%e', cmd[3])

            #Get stack from format string
            stack, text = popStack(stack, text, op)
            if op[0]=='0':
                stack.append( (text, op[2]) )
            elif op[0]=='1':
                out += '\t'*tab + text + '\n'

    print out
    return out

if __name__=="__main__":
    import sys
    if len(sys.argv)<3:
        print "Usage: pydis2py.py <input> <output>"
        sys.exit()
        
    inp_f = sys.argv[1]     #input
    out_f = sys.argv[2]     #output

    op_table = Load_OP(op_file)
    inp = Parse_Input(inp_f)
    out = Decode(op_table, inp, [], 0)
    open(out_f,'w').write(out)
