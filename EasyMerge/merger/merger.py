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
import type1_dealer
import type3_dealer

mergeResults = []

def sortDuplicates(duplicates):
    def f(a,b):
        return cmp(b.getMaxCoveredLineNumbersCount(), a.getMaxCoveredLineNumbersCount())
    duplicates.sort(f)

def tagging(stmt_seq):
    tag = []
    tag.append(stmt_seq.getSourceFile().getFileName())
    tag.append(min(stmt_seq.getCoveredLineNumbers()))
    tag.append(max(stmt_seq.getCoveredLineNumbers()))
    return tuple(tag)

def mergeStmtSeqs(duplicates):
    print "Found", len(duplicates), "Pairs"
    tag_dict = {}
    duplicate_set = []
    for i in duplicates:
        clone_id = len(duplicate_set)
        tag = [(),()]
        for j in [0,1]:
            tag[j] = tagging(i[j])
        if not tag[0] in tag_dict and not tag[1] in tag_dict:
            duplicate_set.append([i[0],i[1]])
            tag_dict[tag[0]] = clone_id
            tag_dict[tag[1]] = clone_id
        elif tag[0] in tag_dict and not tag[1] in tag_dict:
            duplicate_set[tag_dict[tag[0]]].append(i[1])
            tag_dict[tag[1]] = tag_dict[tag[0]]
        elif tag[1] in tag_dict and not tag[0] in tag_dict:
            duplicate_set[tag_dict[tag[1]]].append(i[0])
            tag_dict[tag[0]] = tag_dict[tag[1]]
        else:
            pass
    print "Merged into",len(duplicate_set),"Sets"
    return duplicate_set

def dup_class_fliter(duplicate_set):
    filter = ["Class", "Import", "From","Return"]
    rm_cluster = []
    info = {0:[]}
    for cluster in duplicate_set:
        for id in range(len(cluster)):
            seq = cluster[id]
            rm_stmt = []
            for ast in seq:
                if ast.getName() in filter:
                    rm_stmt.append(ast)
            if len(rm_stmt)>0:
                stmtSeq = []
                orig_len = len(seq._sequence)
                for stmt in rm_stmt:
                    seq._sequence.remove(stmt)
                if len(seq._sequence)==0:
                    info[0].append(duplicate_set.index(cluster))                    
                    rm_cluster.append(cluster)
                    break
                else:                    
                    for stmt in seq:
                        stmtSeq.append(stmt)
                    stmtSeq = StatementSequence(stmtSeq)
                    seq = stmtSeq
                    reduction = (orig_len,len(seq._sequence))
                    if reduction in info:
                        if not duplicate_set.index(cluster) in info[reduction]:
                            info[reduction].append(duplicate_set.index(cluster))
                    else:
                        info[reduction] = [duplicate_set.index(cluster)]
                    
    
    for cluster in rm_cluster:
        duplicate_set.remove(cluster) 
    
    print "cluster", info[0], "is full of invalid stmt"
    for i in info:
        if i==0:
            continue
        print "cluster", info[i],": Reduce",i[0],"stmt to",i[1],"stmt"
    
    
    print "Filtered into", len(duplicate_set),"Sets"
    return duplicate_set              

def removeOverlappedSeqs(duplicate_set):
    def check_overlap_conflict(start_line, end_line):
        if start_line[0]!=end_line[0]:
            return False
        if end_line[1] <= start_line[2] and start_line[1] <= end_line[2]:
            return True
        else:
            return False  
        
    effective_set = []
    rm_set = []
    for s in duplicate_set:
        rmlist = []
        for i in s:
            tag = tagging(i)
            conflict = False
            for j in effective_set:
                if check_overlap_conflict(tag,j):
                    rmlist.append(i)
                    print "Removing Sequence:",tag
                    conflict = True
                    break
            if not conflict:
                effective_set.append(tag)
        for i in rmlist:
            s.remove(i)
        if len(s)<2:
            rm_set.append(s)
            if len(s)==0:
                print "Removing Set: []"
            else:
                print "Removing Set:["+str(tagging(s[0]))+"]"
    
    for s in rm_set:
        duplicate_set.remove(s)
    
    print len(duplicate_set),"sets left"

def getCloneStmt(dir,distance_threshold):
    print "========================================"
    print "Using Clonedigger to detect duplicate codes"
    print "========================================"
    cmdline = OptionParser(usage="""To run Clone Digger type:
python clonedigger.py [OPTION]... [SOURCE FILE OR DIRECTORY]...

The typical usage is:
python clonedigger.py source_file_1 source_file_2 ...
  or
python clonedigger.py path_to_source_tree
Don't forget to remove automatically generated sources, tests and third party libraries from the source tree.

Notice:
The semantics of threshold options is discussed in the paper "Duplicate code detection using anti-unification", which can be downloaded from the site http://clonedigger.sourceforge.net . All arguments are optional. Supported options are: 
""")
    (src_ast_list, orig_duplicates) = digger.main(cmdline, dir, distance_threshold)
    sortDuplicates(orig_duplicates)
    duplicate_set = mergeStmtSeqs(orig_duplicates)
    duplicate_set = dup_class_fliter(duplicate_set) 
    removeOverlappedSeqs(duplicate_set)
    return (src_ast_list,duplicate_set)

def checkSetType(dSet):
    
    def checkSeqType(seq):
        threshold = 0
        type = "Unknown"
        type_set = []
        for i in range(len(seq)):
            id = i
            i = seq[i]
            if type=="Unknown":
                #TODO:CLASS_TYPE
                if i.getName()=="Function":
                    type = "Def"
                else:
                    type = "Stmt"
                type_set.append(([0],type,len(i.getSourceLines())))
            else:
                if i.getName()=="Function":
                    type = "Def"
                else:
                    type = "Stmt"
                if type!=type_set[-1][1]:
                    type_set.append(([id], type,len(i.getSourceLines())))
                else:
                    li = list(type_set[-1][0])
                    li.append(id)
                    type_set[-1]=(li,type,type_set[-1][2]+len(i.getSourceLines()))
        if len(type_set)==1:
            return type_set[0][1]
        else:
            new_set = []
            for i in type_set:
                if i[2]>=threshold:
                    new_seq = []
                    for j in i[0]:
                        new_seq.append(seq[j])
                    new_set.append(new_seq)
            return ("Mix",new_set)
        
    def same_type(t1,t2):
        if t1==t2 or (isinstance(t1,tuple) and isinstance(t2,tuple)):
            return True
        else:
            return False
        
    type_list = []
    for cluster in dSet:
        type = "Unknown"
        for seq in cluster:
            cur_type = checkSeqType(seq)
            if type!="Unknown" and not same_type(type,cur_type):
                print "Mixed in this Set"
                type = "Error"
                break
            elif type=="Unknown":            
                if isinstance(cur_type,tuple):
                    type = (cur_type[0],[cur_type[1]])
                else:
                    type = cur_type
            elif isinstance(cur_type,tuple) and isinstance(type,tuple):
                seqs = type[1]
                seqs.append(cur_type[1])
                type = (type[0],seqs) 
        type_list.append(type)
    return type_list     


def checkSetDiff(dSet):
    
    def checkPairDiff(pair):
        diff_rec = []
        for i in range(len(pair[0])):
            statements = [pair[j][i] for j in [0,1]]
            u = anti_unification.Unifier(statements[0], statements[1])
            #print u.getSize()
            for s in u.getSubstitutions():
                for fv in s.getMap():
                    a = s.getMap()[fv]
                    #print str(a)
                    for sa in a.getAncestors():
                        if len(sa.getLineNumbers())>0:
                            #print str(sa.getLineNumbers())
                            break
                #print ""
            diff_rec.append(u.getSize())
        #print sum(diff_rec)
        return diff_rec 
    
    def checkFileDiff(cluster):
        filename = cluster[0].getSourceFile()
        for i in cluster[1:]:
            if i.getSourceFile()!=filename:
                return False
        return True
    
    diff_file_list = []
    diff_content_list = []
    for cluster in dSet:
        diff_sum = []
        for i in cluster[1:]:
            diff = checkPairDiff([cluster[0],i])
            diff_sum.append(sum(diff))
        diff_content_list.append(sum(diff_sum)) 
        diff_file_list.append(checkFileDiff(cluster)) 
    return (diff_content_list, diff_file_list)
        

def spreadMixSet(dSet, type_list):
    
    for cluster in dSet:
        type = type_list[dSet.index(cluster)]
        if isinstance(type,tuple):
            new_clusters = type[1]
            new_insert = []
            for i in range(len(new_clusters[0])):
                new_set = []
                for d in new_clusters:
                    new_set.append(StatementSequence(d[i]))
                new_insert.append(new_set)
            dSet[dSet.index(cluster)] = new_insert
            
    i = 0
    while True:
        cluster = dSet[i]     
        if isinstance(cluster[0],list):
            dSet = dSet[:i]+cluster+dSet[i+1:]
            type_list = type_list[:i]+checkSetType(cluster)+type_list[i+1:]
        i+=1
        if i>=len(dSet):
            break 
    return (dSet, type_list)
    
def refineDuplicateSet(dSet):
    type_list = checkSetType(dSet)
    (dSet,type_list) = spreadMixSet(dSet,type_list)
    (diff_content_list, diff_file_list) = checkSetDiff(dSet)

    dSetInfoList = []           
    for i in range(len(dSet)):
        dSetInfoList.append([type_list[i],diff_content_list[i],diff_file_list[i]])     
        
    return (dSetInfoList, dSet)
    #test.generateCodeSnippet(dSet[0][0],"helper.py")

def tmpDistributor(dSet, dInfo, src_ast_list):
    for i in range(len(dSet)):
        cluster = dSet[i]
        info = dInfo[i]
        print info, len(cluster)#, ":", tagging(cluster[0])
        if info[0]=="Def" and info[1]<=0:
            #print "Type0"
            if processIdenticalDef(src_ast_list, cluster):
                #print "Success"
                pass
            else:
                #print "Error"
                pass
            #break   
        '''if info[0]=="Stmt" and info[1]<=0:
            #print "Type1"
            if processIdenticalStmt(src_ast_list, cluster, i):
                #print "Success"
                pass
            else:
                #print "Error"
                pass
                #break   '''
        if info[0]=="Stmt" and info[1]>=0:
            processNonIdenticalStmt(src_ast_list, cluster, i)
                 

def processIdenticalDef(src_ast_list, cluster):
    caller = {}
    merged_code = []
    for i in cluster:
        filename = i.getSourceFile().getFileName()
        #src_ast_list[str(filename)].output("./sandbox/test.out")
        lines = tagging(i)[1:]
        code_snippet = generateCodeSnippet(i)
        merged = type0_dealer.generateNewCode(code_snippet, lines, src_ast_list[str(filename)])
        merged_code.append(merged.get_code())
        caller[tagging(i)]=merged.caller
        
    for i in merged_code[1:]:
        if i!=merged_code[0]:
            return False
        
    code = merged_code[0]
    #print code
    m = Result()
    m.add_code(code)
    for s in cluster:
        tag = tagging(s)
        m.add_tag(tag)
        m.add_caller(tag, caller[tag])
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
        merged = type1_dealer.generateNewCode(id, code_snippet, lines, src_ast_list[str(filename)])
        merged_list.append(merged)
        merged_code.append(merged.get_code())
        caller[tagging(i)]=merged.caller
        merged.tag = tagging(i)
        
    for i in range(1,len(merged_list)):
        cur_merge = merged_list[i]
        cur_code = merged_code[i]
        if cur_code!=merged_code[0]:
            #print "DIFFERENT!"
            if cur_merge.code_lines[1:-1]!=merged_list[0].code_lines[1:-1]:
                print "STILL_DIFF"
                return False
            else:
                merged_list = type1_dealer.mergeDiffResults(merged_list)
    
    merged_code = []
    for i in merged_list:
        merged_code.append(i.get_code())
        caller[i.tag] = i.caller
    for i in range(1,len(merged_list)):
        cur_merge = merged_list[i]
        cur_code = merged_code[i]
        if cur_code!=merged_code[0]:
            print "DIFFERENT AGAIN!"
            return False             
            
        
    code = merged_code[0]
    m = Result()
    m.add_code(code)
    for s in cluster:
        tag = tagging(s)
        m.add_tag(tag)
        m.add_caller(tag, caller[tag])
    mergeResults.append(m)
    return True

def processNonIdenticalStmt(src_ast_list, cluster, id):
    #raw_input()
    caller = {}
    merged_list = []
    merged_code = []
    for i in cluster:  
        print tagging(i)   
        filename = i.getSourceFile().getFileName()
        #src_ast_list[str(filename)].output("./sandbox/test.out")
        lines = tagging(i)[1:]
        code_snippet = generateCodeSnippet(i)
        type3_dealer.generateNewCode(id, code_snippet, lines, src_ast_list[str(filename)])
        break
        '''merged_list.append(merged)
        merged_code.append(merged.get_code())
        caller[tagging(i)]=merged.caller
        merged.tag = tagging(i)
        
    for i in range(1,len(merged_list)):
        cur_merge = merged_list[i]
        cur_code = merged_code[i]
        if cur_code!=merged_code[0]:
            #print "DIFFERENT!"
            if cur_merge.code_lines[1:-1]!=merged_list[0].code_lines[1:-1]:
                print "STILL_DIFF"
                return False
            else:
                merged_list = type1_dealer.mergeDiffResults(merged_list)
    
    merged_code = []
    for i in merged_list:
        merged_code.append(i.get_code())
        caller[i.tag] = i.caller
    for i in range(1,len(merged_list)):
        cur_merge = merged_list[i]
        cur_code = merged_code[i]
        if cur_code!=merged_code[0]:
            print "DIFFERENT AGAIN!"
            return False             
            
        
    code = merged_code[0]
    m = Result()
    m.add_code(code)
    for s in cluster:
        tag = tagging(s)
        m.add_tag(tag)
        m.add_caller(tag, caller[tag])
    mergeResults.append(m)
    return True'''
            
            
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
        
def main(dir,distance_threshold):
    (src_ast_list, duplicate_set) = getCloneStmt(dir,distance_threshold)
    (dSetInfoList, duplicate_set) = refineDuplicateSet(duplicate_set)
    tmpDistributor(duplicate_set, dSetInfoList, src_ast_list)
    return mergeResults

if __name__ == '__main__':
    main("../tests/beets", 5)
    #for i in mergeResults:
        #i.output()
        #print ''
    
    
    
    
    
    