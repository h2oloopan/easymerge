'''
Created on Mar 17, 2014

@author: h7qin
'''

from optparse import OptionParser
import clonedigger.clonedigger as digger
import clonedigger.anti_unification as anti_unification
from clonedigger.abstract_syntax_tree import StatementSequence
from clonedigger.debug import AST
import os

stat = []

def getTotalSourceLineNumbers(dir):
    def walk(dirname):
        for dirpath, dirs, files in os.walk(dir):
            dirs[:] = [d for d in dirs]
            files[:] = [f for f in files]
            yield (dirpath, dirs, files)
    def getLineNumber(filename):
        f = open(filename, "r")
        lines = f.readlines()
        return len(lines)
    
    total_num = 0
    total_file = 0
    for dirpath, dirnames, filenames in walk(dir):
        #print dirpath, dirnames, filenames
        for f in filenames:
            if f[-3:]!=".py":
                continue
            filename = os.path.join(dirpath, f)
            total_file+=1
            linenum = getLineNumber(filename)
            total_num += linenum
    return (total_num, total_file)

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

def getInfoFromSet(dSet, pair = False):
    numOfSet = len(dSet)
    if pair:
        dupInCluster = 2
        
        indepLine = {}
        for i in dSet:
            for j in (0,1):
                dup = i[j]
                srcName = dup.getSourceFile().getFileName()
                for n in dup.getCoveredLineNumbers():
                    tag = srcName+"@"+str(n)
                    if tag in indepLine:
                        indepLine[tag] += 1
                    else:
                        indepLine[tag] = 1
        
        lineCovered = len(indepLine)
        lineAvgRep = float(sum(indepLine.values()))/float(len(indepLine))
                    
    else:
        totalDup = 0
        for i in dSet:
            totalDup+= len(i)
        dupInCluster = float(totalDup)/float(numOfSet)
        
        indepLine = {}
        for i in dSet:
            for dup in i: 
                #print dup
                srcName = dup.getSourceFile().getFileName()
                for n in dup.getCoveredLineNumbers():
                    tag = srcName+"@"+str(n)
                    if tag in indepLine:
                        indepLine[tag] += 1
                    else:
                        indepLine[tag] = 1
        
        lineCovered = len(indepLine)
        lineAvgRep = float(sum(indepLine.values()))/float(len(indepLine))
        
    return numOfSet, dupInCluster, lineCovered, lineAvgRep

def mergeStmtSeqs(duplicates):
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
    print "Found", len(duplicate_set), "Pairs"
    filter = ["Class", "Import", "From","Return"]
    rm_cluster = []
    info = {0:[]}
    for cluster in duplicate_set:
        for id in (0,1):
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
    
    
    print "Filtered into", len(duplicate_set),"Pairs"
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
    
    print len(duplicate_set),"Independent Sets Left"

def getCloneStmt(dir,distance_threshold, size_threshold):
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
    (src_ast_list, orig_duplicates) = digger.main(cmdline, dir, distance_threshold, size_threshold)
    sortDuplicates(orig_duplicates)
    stat.append(getInfoFromSet(orig_duplicates,True))
    
    duplicate_set = dup_class_fliter(orig_duplicates)    
    stat.append(getInfoFromSet(duplicate_set,True))
    
    duplicate_set = mergeStmtSeqs(duplicate_set)
    stat.append(getInfoFromSet(duplicate_set))
    
    removeOverlappedSeqs(duplicate_set)
    stat.append(getInfoFromSet(duplicate_set))
    
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
        print t1,t2
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
        if type=="Def" and len(cluster[0])>1:
            new_insert = []
            for i in range(len(cluster[0])):
                new_set = []
                for d in cluster:
                    new_set.append(StatementSequence([d[i]]))
                new_insert.append(new_set)
            dSet[dSet.index(cluster)] = new_insert
        if isinstance(type,tuple):
            new_clusters = type[1]
            new_insert = []
            for i in range(len(new_clusters[0])):
                new_set = []
                for d in new_clusters:
                    new_set.append(StatementSequence(d[i]))
                if tagging(new_set[0])[2] - tagging(new_set[0])[1]>=3:                    
                    new_insert.append(new_set)
            dSet[dSet.index(cluster)] = new_insert
            
    i = 0
    while True:
        cluster = dSet[i]     
        if len(cluster)>0 and isinstance(cluster[0],list):
            dSet = dSet[:i]+cluster+dSet[i+1:]
            type_list = type_list[:i]+checkSetType(cluster)+type_list[i+1:]
        elif len(cluster)==0:
            dSet = dSet[:i]+dSet[i+1:]
            type_list = type_list[:i]+type_list[i+1:]
            i-=1

        i+=1
        if i>=len(dSet):
            break 
    return (dSet, type_list)
    
def refineDuplicateSet(dSet):
    type_list = checkSetType(dSet)
    (dSet,type_list) = spreadMixSet(dSet,type_list)
    print "Spread to",len(dSet),"Sets"
    stat.append(getInfoFromSet(dSet))
    
    for i in dSet:
        if len(i)==0:
            print "ERROR"
    
    (diff_content_list, diff_file_list) = checkSetDiff(dSet)

    dSetInfoList = []           
    for i in range(len(dSet)):
        dSetInfoList.append([type_list[i],diff_content_list[i],diff_file_list[i]])     
        
    stmt_count = 0
    def_count = 0
    idtc_count = 0
    n_idtc_count = 0
    samefile_count = 0
    difffile_count = 0
    for i in dSetInfoList:
        if i[0]=="Stmt":
            stmt_count+=1
        else:
            def_count+=1
        if i[1]>0:
            n_idtc_count+=1
        else:
            idtc_count+=1
        if i[2]:
            samefile_count+=1
        else:
            difffile_count+=1
    stat.append(((stmt_count,def_count), (idtc_count,n_idtc_count), (samefile_count,difffile_count)))
    
    return (dSetInfoList, dSet)
    #test.generateCodeSnippet(dSet[0][0],"helper.py")
    
def main(dir,distance_threshold, size_threshold):
    stat.append(getTotalSourceLineNumbers(dir))
    (src_ast_list, duplicate_set) = getCloneStmt(dir,distance_threshold, size_threshold)
    (dSetInfoList, duplicate_set) = refineDuplicateSet(duplicate_set)
    
    return (src_ast_list, dSetInfoList, duplicate_set,stat)
    
if __name__ == '__main__':
    main("../tests/beets", 10, 4)