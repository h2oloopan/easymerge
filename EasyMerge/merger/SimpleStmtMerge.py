'''
Created on Mar 12, 2014

@author: h7qin
'''
from optparse import OptionParser
import clonedigger.clonedigger as digger
import clonedigger.anti_unification as anti_unification

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

def getCloneStmt():
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
    orig_duplicates = digger.main(cmdline)
    sortDuplicates(orig_duplicates)
    duplicate_set = mergeStmtSeqs(orig_duplicates) 
    removeOverlappedSeqs(duplicate_set)
    return duplicate_set


def checkSeqType(seq):
    type = "Unknown"
    type_set = []
    for i in range(len(seq)):
        id = i
        i = seq[i]
        if type=="Unknown":
            if i.getName()=="Function":
                type = "Def"
            else:
                type = "Stmt"
            type_set.append((0,type))
        else:
            if i.getName()=="Function":
                type = "Def"
            else:
                type = "Stmt"
            if type!=type_set[-1][1]:
                type_set.append((id, type))
            else:
                type_set[-1]=(id,type)
    if len(type_set)==1:
        return type_set[0][1]
    else:
        return type_set

def checkSetType(cluster):
    type = "Unknown"
    for seq in cluster:
        cur_type = checkSeqType(seq)
        if type!="Unknown" and type!=cur_type:
            print "Mixed in this Set"
            type = "Error"
            break
        elif type=="Unknown":
            type = cur_type
    
    return type 

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
        if i.getSourceFile!=filename:
            return False
    return True

def checkSetDiff(cluster):
    diff_sum = []
    for i in cluster[1:]:
        diff = checkPairDiff([cluster[0],i])
        diff_sum.append(sum(diff))
        
    diff_file = checkFileDiff(cluster) 
    return (diff_file, sum(diff_sum))    
    
def showSeq(dSet):
    for cluster in dSet:
        print len(cluster),
        print checkSetType(cluster),
        print checkSetDiff(cluster)
        #raw_input()
        #if checkSetType(cluster)=="Stmt":
            #process_stmt(cluster)
          
    
if __name__ == '__main__':
    duplicate_set = getCloneStmt()
    showSeq(duplicate_set)
    
    