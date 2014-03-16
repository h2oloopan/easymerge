'''
Created on Mar 16, 2014

@author: h7qin
'''

class Merge:
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
        