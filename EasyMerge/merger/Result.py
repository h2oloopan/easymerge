'''
Created on Mar 16, 2014

@author: h7qin
'''

class Result:
    def __init__(self):
        self._tag = []
        self._code = ""
        self._caller = {}
    def add_code(self, code):
        self._code = code
    def add_tag(self, tag):
        self._tag.append(tag)
    def add_caller(self, tag, caller):
        self._caller[tag] = caller

    def check_diff_pak(self):
        
        def in_diff_pak(s1,s2):
            s1 = s1.split("/")[:-1]
            s2 = s2.split("/")[:-1]
            if len(s1)<len(s2):
                s2 = s2[:len(s1)]
            elif len(s1)>len(s2):
                s1 = s1[:len(s2)]                
            return not s1==s2
        
        tags = self._caller.keys()
        fn1 = tags[0][0]
        self.diff_pak = False
        for i in tags[1:]:
            if in_diff_pak(fn1, i[0]):
                self.diff_pak = True
                break

    def get_code(self):
        return self._code
    def get_caller(self):
        def get_pak(s):
            s = s.split("\\")[:-1]
            print s
            return str(s)
        self._new_caller = {}
        for i in self._caller:
            new_key = (i[0],i[1],i[2],get_pak(i[0]))
            self._new_caller[new_key] = self._caller[i]
        return self._new_caller
    def output(self):
        print "Code:"
        print self._code.strip()
        print "Caller:"
        for i in self._caller:
            print i,":"
            print self._caller[i]
        print "External:", self.external

