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
    def get_code(self):
        return self._code
    def get_caller(self):
        return self._caller
    def output(self):
        print self._code
        for i in self._caller:
            print i,":"
            print self._caller[i]

