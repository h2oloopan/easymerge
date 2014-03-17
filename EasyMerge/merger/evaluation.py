'''
Created on Mar 17, 2014

@author: h7qin
'''
import os

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
    return total_num, total_file



def getOtherStats(dir, distance_threshold, size_threshold):
    import clone_refiner
    stat = clone_refiner.main(dir, distance_threshold, size_threshold, True)
    for i in stat:
        print i
    
if __name__ == '__main__':
    dir_name = "../tests/fig"
    total_num, total_file = getTotalSourceLineNumbers(dir_name)
    getOtherStats(dir_name, 10, 4)
    print total_num,"lines in total"
    print total_file,"files in total"