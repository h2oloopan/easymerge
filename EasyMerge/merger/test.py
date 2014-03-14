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

def generateCodeSnippet(stmtSeq, filename):
    file = open(filename, 'w')
    offset = getOriginalOffset(stmtSeq)
    for i in stmtSeq:
        a = AST(i)
        a.output("helper.out")
        for j in i.getSourceLines():
            file.write(j[offset:]+"\n")
    file.close()

if __name__ == '__main__':
    pass