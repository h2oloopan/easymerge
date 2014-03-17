'''
Created on Mar 12, 2014

@author: h7qin
'''
from optparse import OptionParser
import clonedigger.clonedigger as digger
import clonedigger.anti_unification as anti_unification
from clonedigger.abstract_syntax_tree import StatementSequence
from clonedigger.debug import AST
#import clonedigger.debug as debug

from Result import Result 
import type0_dealer
import type1_0_dealer as type1_dealer
import type3_dealer

mergeResults = []
stat ={"Merged":0, 
       "MergedIdentical":0, 
       "MergedDiff":0, 
       "MergedDist":0,
       "External": (0, 0), 
       "DiffDef":0, 
       "ErrorDef":0,
       "DiffStmt":0,
       "ErrorStmt":0,
       "DiffPak":0,
       "Reduction":[]}

def tagging(stmt_seq):
    tag = []
    tag.append(stmt_seq.getSourceFile().getFileName())
    tag.append(min(stmt_seq.getCoveredLineNumbers()))
    tag.append(max(stmt_seq.getCoveredLineNumbers()))
    return tuple(tag)

def tmpDistributor(dSet, dInfo, src_ast_list):
    for i in range(len(dSet)):
        print ""
        
        cluster = dSet[i]
        info = dInfo[i]
        
        for j in cluster:
            print tagging(j)
        
        print info, len(cluster)#, ":", tagging(cluster[0])
        if info[0]=="Def" and info[1]<=0:
            print "Type0"
            if processIdenticalDef(src_ast_list, cluster):
                print "Success"
                stat["Merged"]+=1
                stat["MergedIdentical"]+=1
            else:
                print "Error"
            #break   
        elif info[0]=="Stmt" and info[1]<=0:
            print "Type1"
            if processIdenticalStmt(src_ast_list, cluster, i):
                print "Success"
                stat["Merged"]+=1
                stat["MergedIdentical"]+=1
            else:
                print "Error"
                #break   
        elif info[0]=="Stmt" and info[1]>0:
            print "Type3"
            if processNonIdenticalStmt(src_ast_list, cluster, i):
                print "Success"
                stat["Merged"]+=1
                stat["MergedDiff"]+=1
                stat["MergedDist"]+=info[1]
            else:
                print "Error"
        else:
            stat["DiffDef"]+=1
    
    for m in mergeResults:
        
        if m.diff_pak:
            stat["DiffPak"]+=1
        
        stat["External"] = (stat["External"][0]+m.external[0], stat["External"][1]+m.external[1])
        
        oldLines = 0
        for i in m._caller:
            lines = i[2]-i[1]+1
            oldLines+=lines
        newLines = m.lines+len(m._caller)
        
        if newLines>oldLines:
            print "New Code:", m.lines
            print "Caller:", len(m._caller)
            old = []
            for i in m._caller:
                old.append(i[2]-i[1]+1)
            print "Old Code:", old
        
        stat["Reduction"].append(oldLines-newLines)
                 

def processIdenticalDef(src_ast_list, cluster):
    caller = {}
    merged_code = []
    unreach_num = []
    for i in cluster:
        filename = i.getSourceFile().getFileName()
        #src_ast_list[str(filename)].output("./sandbox/test.out")
        lines = tagging(i)[1:]
        code_snippet = generateCodeSnippet(i)
        merged = type0_dealer.generateNewCode(code_snippet, lines, src_ast_list[str(filename)], tagging(i))
        line_len = len(merged.code_lines)
        if merged.unreachable:
            unreach_num.append(len(merged.unreachable))
        else:
            unreach_num.append(0)
        merged_code.append(merged.get_code())
        caller[tagging(i)]=merged.caller
        
    for i in merged_code[1:]:
        if i!=merged_code[0]:
            stat["ErrorDef"]+=1
            return False

    code = merged_code[0]
    #print code
    m = Result()
    m.lines = line_len+len(caller)
    m.add_code(code)
    for s in cluster:
        tag = tagging(s)
        m.add_tag(tag)
        m.add_caller(tag, caller[tag])
    m.check_diff_pak()
    m.external = (max(unreach_num), 0)
    mergeResults.append(m)
    return True


def processIdenticalStmt(src_ast_list, cluster, id):
    caller = {}
    merged_list = []
    merged_code = []
    for i in cluster:     
        filename = i.getSourceFile().getFileName()
        #src_ast_list[str(filename)].output("./sandbox/test.out")
        lines = tagging(i)[1:]
        code_snippet = generateCodeSnippet(i)
        merged = type1_dealer.generateNewCode(id, code_snippet, lines, src_ast_list[str(filename)], tagging(i))
        merged_list.append(merged)
        merged_code.append(merged.get_code())
        caller[tagging(i)]=merged.caller
        merged.tag = tagging(i)
        
    for i in range(1,len(merged_list)):
        cur_merge = merged_list[i]
        cur_code = merged_code[i]
        if cur_code!=merged_code[0]:
            print "DIFFERENT!"
            if cur_merge.code_lines[1:-1]!=merged_list[0].code_lines[1:-1]:
                print "STILL_DIFF"
                stat["ErrorStmt"]+=1
                return False
            else:
                merged_list = type1_dealer.mergeDiffResults(merged_list)
    
    merged_code = []
    
    for i in merged_list:
        merged_code.append(i.get_code())
        line_len = len(i.code_lines)
        caller[i.tag] = i.caller
    for i in range(1,len(merged_list)):
        cur_merge = merged_list[i]
        cur_code = merged_code[i]
        if cur_code!=merged_code[0]:
            print "DIFFERENT AGAIN!"
            stat["ErrorStmt"]+=1
            return False             
            
        
    code = merged_code[0]
    m = Result()
    m.add_code(code)
    m.lines = line_len
    for s in cluster:
        tag = tagging(s)
        m.add_tag(tag)
        m.add_caller(tag, caller[tag])
    m.check_diff_pak()
    m.external = (len(merged_list[0].param), len(merged_list[0].return_vars))
    mergeResults.append(m)    
    return True

def processNonIdenticalStmt(src_ast_list, cluster, id):
    #raw_input()
    caller = {}
    merged_list = []
    merged_code = []
    for i in cluster:  
        filename = i.getSourceFile().getFileName()
        #src_ast_list[str(filename)].output("./sandbox/test.out")
        lines = tagging(i)[1:]
        code_snippet = generateCodeSnippet(i)
        merged = type3_dealer.generateNewCode(id, code_snippet, lines, src_ast_list[str(filename)], tagging(i))
        merged_list.append(merged)
        
    if type3_dealer.checkMergable(merged_list):
        type3_dealer.generateCommonCode(merged_list)
        for i in range(len(merged_list)):
            line_len = len(merged_list[i].code_lines)
            merged_code.append(merged_list[i].get_code())            
            caller[tagging(cluster[i])]=merged_list[i].caller
            merged_list[i].tag = tagging(cluster[i])
    else:
        print "NOT MERGABLE"
        stat["DiffStmt"]+=1
        return False

    for i in range(1,len(merged_list)):
        cur_code = merged_code[i]
        if cur_code!=merged_code[0]:
            print "UNMERGABLELY DIFFERENT!"
            stat["DiffStmt"]+=1
            #for m in merged_list:
            #    m.output()
            return False
    
    
           
    code = merged_code[0]
    m = Result()
    m.lines = line_len
    m.add_code(code)
    for s in cluster:
        tag = tagging(s)
        m.add_tag(tag)
        m.add_caller(tag, caller[tag])
    m.check_diff_pak()
    m.external = (len(merged_list[0].param), len(merged_list[0].return_vars))
    mergeResults.append(m)
    return True
            
            
def generateCodeSnippet(stmtSeq, filename=None):
    
    def getOriginalOffset(stmtSeq):
        offset = 0
        s = stmtSeq[0].getSourceLines()[0]
        while s.find(" ")==0:
            offset+=1
            s = s[1:]
        return offset
    
    if filename!=None:
        file = open(filename, 'w')
    else:
        s = ""
    offset = getOriginalOffset(stmtSeq)
    for i in stmtSeq:
        a = AST(i)
        '''print "ORIG CODE:"
        for j in i.getSourceLines():
            print j'''
        #a.output("helper.out")
        #print "\nNEW CODE"
        for j in i.getSourceLines():
            #print j[offset:]
            if filename!=None:
                file.write(j[offset:]+"\n")
            else:
                s+=(j[offset:]+"\n")    
    if filename!=None:          
        file.close()
    else:
        return s
        
def main(dir,distance_threshold, size_threshold):
    import clone_refiner
    src_ast_list, dSetInfoList, duplicate_set = clone_refiner.main(dir, distance_threshold, size_threshold)
    tmpDistributor(duplicate_set, dSetInfoList, src_ast_list)
    print "MERGED COUNT =",len(mergeResults)
    return mergeResults

if __name__ == '__main__':
    main("../tests/beets", 10, 4)
    
    for i in mergeResults:
        i.output()
        print ''       
     
    print stat
    print float(sum(stat["Reduction"]))/float(stat["Merged"])
    print float(stat["External"][0])/float(stat["Merged"]),
    print float(stat["External"][1])/float(stat["Merged"])
    
    
    
    