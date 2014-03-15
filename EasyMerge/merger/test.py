'''
Created on Mar 14, 2014

@author: h7qin
'''
from clonedigger.debug import AST
def getOriginalOffset(stmtSeq):
    offset = 0
    s = stmtSeq[0].getSourceLines()[0]
    while s.find(" ")==0:
        offset+=1
        s = s[1:]
    return offset

def generateCodeSnippet(stmtSeq, filename=None):
    if filename!=None:
        file = open(filename, 'w')
    else:
        s = ""
    offset = getOriginalOffset(stmtSeq)
    for i in stmtSeq:
        a = AST(i)
        #a.output("helper.out")
        for j in i.getSourceLines():
            if filename!=None:
                file.write(j[offset:]+"\n")
            else:
                s+=(j[offset:]+"\n")    
    if filename!=None:          
        file.close()
    else:
        return s

if __name__ == '__main__':
    pass