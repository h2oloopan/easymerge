def print_clone(clone):
    print 0, clone[0]
    for i in clone[0]:
        print i,"\n"
    print 1, clone[1]
    for i in clone[1]:
        print i,"\n"


class AST:
    def __init__(self, tree):
        self.tree = tree
        self.set_scope()
        
    def set_scope(self):
        self.imports = []
        self.raw_scope = []
        self.functions = []
        self.classes = []
        self.raw_call = []
        self.calls = []
        self.parse_tree(self.tree, [], self.raw_scope, self.raw_call, False)
        self.process_imports()
        self.process_scope()
        self.process_call()
        
    def parse_tree(self, tree, scope, scope_result, call_result, in_call):
        if tree.getName() == "Import":
            self.imports+=eval(tree.getChilds()[0].getName())
        if tree.getName() == "From":
            for i in eval(tree.getChilds()[1].getName()):
                temp_scope = list(scope)+[("Class", i[0], (-1,-1))]
                scope_result.append(temp_scope)
                if i[1]!=None:
                    temp_scope2 = list(scope)+[("Class", i[1], (-1,-1))]
                    scope_result.append(temp_scope2)
        if tree.getName()=="Class":
            end = max(tree.getCoveredLineNumbers())
            scope.append(("Class", tree.getChilds()[0].getName()[1:-1], (tree.getLineNumbers()[0],end)))
            scope_result.append(scope)
        if tree.getName()=="Function":
            end = max(tree.getCoveredLineNumbers())
            scope.append(("Function", tree.getChilds()[0].getName()[1:-1], (tree.getLineNumbers()[0],end)))
            scope_result.append(scope)
        if tree.getName()=="CallFunc" and not in_call:
            in_call = True
            call_result.append((tree.getLineNumbers()[0], self.parse_call(tree.getChilds()[0]), scope))
        for i in tree.getChilds():
            new_scope = list(scope)            
            self.parse_tree(i, scope, scope_result, call_result, in_call)
            scope = new_scope    
            
    def parse_call(self,call):
        if call.getName()=="Name":
            return [call.getChilds()[0].getName()[1:-1]]
        if call.getName()=="Getattr":
            if call.getChilds()[0].getName()=="Name":
                return [call.getChilds()[0].getChilds()[0].getName()[1:-1], call.getChilds()[1].getName()[1:-1]]
            elif call.getChilds()[0].getName()=="Getattr":
                return self.parse_call(call.getChilds()[0])+[call.getChilds()[1].getName()[1:-1]]
            elif call.getChilds()[0].getName()=="CallFunc":
                return self.parse_call(call.getChilds()[0].getChilds()[0])+["()",call.getChilds()[1].getName()[1:-1]]
            elif call.getChilds()[0].getName()=="Subscript" or call.getChilds()[0].getName()=="Slice":
                return [str(call.getChilds()[0]),call.getChilds()[1].getName()[1:-1]]
            else:
                print "Exception Here", call.getChilds()[0].getName()
        print "Exception Here", call.getName()
    
    
    def process_imports(self):
        new_imports = []
        for i in self.imports:
            if i[0].find(".")<0:
                new_i = [self.imports.index(i), i[0]]
            else:
                new_i = [new_i[0]]+i[0].split('.')
            new_imports.append(new_i)
            if i[1]!=None:
                if i[1].find(".")<0:
                    new_i = [-1*self.imports.index(i),i[1]]
                else:
                    new_i = [new_i[0]]+i[1].split('.')
                new_imports.append(new_i)
        self.imports = new_imports
        
    def process_scope(self):
        for i in self.raw_scope:
            if i[-1][0]=="Function":
                func = Function(i, len(self.functions))
                self.functions.append(func)
            else:
                clas = Class(i, len(self.classes))
                self.classes.append(clas)                
                
    def filter_call(self):
        build_in_name = ["abs", "divmod", "input", "open", "staticmethod", "all", "enumerate", "int", "ord", "str", "any", "eval", "isinstance", "pow", "sum", "basestring", "execfile", "issubclass", "print", "super", "bin", "file", "iter", "property", "tuple", "bool", "filter", "len", "range", "type", "bytearray", "float", "list", "raw_input", "unichr", "callable", "format", "locals", "reduce", "unicode", "chr", "frozenset", "long", "reload", "vars", "classmethod", "getattr", "map", "repr", "xrange", "cmp", "globals", "max", "reversed", "zip", "compile", "hasattr", "memoryview", "round", "__import__", "complex", "hash", "min", "set", "apply", "delattr", "help", "next", "setattr", "buffer", "dict", "hex", "object", "slice", "coerce", "dir", "id", "oct", "sorted", "intern"]
        build_in_list = []
        for i in self.raw_call:
            if len(i[1])==1 and i[1][0] in build_in_name:
                build_in_list.append(i)
        for i in build_in_list:
            self.raw_call.remove(i)
    
    def process_call(self):
        self.filter_call()
        for i in self.raw_call:
            call = Call(i)
            self.calls.append(call)
        for i in self.calls:
            if len(i.name)==1:
                self.process_single_call(i)
            else:
                self.process_multi_call(i)
    
    
    def process_single_call(self, call):
        for i in self.classes:
            if call.name[0] == i.name:
                if len(i.scope)>0 and call.line> i.scope[-1][-1][0] and call.line<i.scope[-1][-1][1]:
                    continue
                call.set_source(("class",i.id))
                return
        candidates = []
        for i in self.functions:
            if call.name[0] == i.name:             
                if call.line>=i.scope[0] and call.line<=i.scope[1]:
                    candidates.append(i)
        cur_id = -1
        min_scope = 999999
        for i in candidates:
            if (i.scope[1]-i.scope[0])<min_scope:
                min_scope = (i.scope[1]-i.scope[0])
                cur_id = i.id
        if cur_id!=-1:
            call.set_source(("function", cur_id))
            
    def process_multi_call(self, call):
        candidates = []
        for i in self.classes:
            if call.name[-1] == i.name and len(call.name)-len(i.scope)==1:
                candidates.append(i)
        for i in candidates:
            match = True
            for j in range(len(i.scope)):
                if i.scope[j][0]!="Class" or i.scope[j][1]!=call.name[j]:
                    match = False
            if match:
                call.set_source(("class",i.id))
                return
         
        for i in self.imports:
            if i[1:]==call.name[:-1]:
                call.set_source(("import",i[0]))
                return
        
        if not "()" in call.name:
            call.set_source(("member",-1))
        else:
            idx = call.name.index("()")
            call.name = call.name[:idx]
            self.process_multi_call(call)
            call.set_source((call.source[0],call.source[1],"followed")  )         
        
                 
    
    def output(self, filename):
        file = open(filename, "w")
        for i in self.imports:
            file.write(str(i)+"\n")
        for i in self.functions:
            file.write("=======================\n")
            file.write("ID:"+str(i.id)+"\n")
            file.write("Name:"+i.name+"\n")
            file.write("lines:"+str(i.lines)+"\n")
            file.write("scope:"+str(i.env)+"\n")
            file.write("member:"+str(i.ismember)+"\n")
        for i in self.classes:
            file.write("=======================\n")
            file.write("ID:"+str(i.id)+"\n")
            file.write("Name:"+i.name+"\n")
            file.write("lines:"+str(i.lines)+"\n")
            file.write("scope:"+str(i.scope)+"\n")
        for i in self.calls:
            file.write("=======================\n")
            file.write("Name:"+str(i.name)+"\n")
            file.write("line:"+str(i.line)+"\n")
            file.write("scope:"+str(i.scope)+"\n")
            file.write("source:"+str(i.source)+"\n")
        file.write(self.visualizeTree(self.tree, 0))
        
    def visualizeTree(self, tree, height):
        s = tree.getName()+"\n"
        for i in tree.getChilds():
            for j in range(height):
                s+="\t"
            s += self.visualizeTree(i,height+1) + "\n"
        return s

class Function:
    def __init__(self, func, id):
        self.id = id
        self.name = func[-1][1]
        self.lines = func[-1][2]
        self.env = func[:-1]
        self.set_ismember()
        self.set_scope()
    def set_ismember(self):
        if len(self.env)==0:
            self.ismember = False
            self.env = [("Global","",(0,999998))]
        elif self.env[-1][0]=="Class":
            self.ismember = True
        else:
            self.ismember = False
    def set_scope(self):
        self.scope = self.env[-1][-1]
            
class Class:
    def __init__(self, clas, id):
        self.id = id
        self.name = clas[-1][1]
        self.lines = clas[-1][2]
        self.scope = clas[:-1]
        
class Call:
    def __init__(self, call):
        self.source = -1
        self.line = call[0]
        self.name = call[1]
        self.env = call[2]
        if self.env == []:
            self.env = [("Global","",(0,999998))]
        self.scope = self.env[-1][-1]
    def set_source(self, id):
        self.source = id
        
        
        