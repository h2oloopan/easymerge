'''
Created on Mar 15, 2014

@author: h7qin
'''
"Usage: unparse.py <path to source file>"
import sys
import ast
import cStringIO
import os

# Large float and imaginary literals get turned into infinities in the AST.
# We unparse those infinities to INFSTR.
INFSTR = "1e" + repr(sys.float_info.max_10_exp + 1)
build_in_name = ["abs", "divmod", "input", "open", "staticmethod", "all", "enumerate", "int", "ord", "str", "any", "eval", "isinstance", "pow", "sum", "basestring", "execfile", "issubclass", "print", "super", "bin", "file", "iter", "property", "tuple", "bool", "filter", "len", "range", "type", "bytearray", "float", "list", "raw_input", "unichr", "callable", "format", "locals", "reduce", "unicode", "chr", "frozenset", "long", "reload", "vars", "classmethod", "getattr", "map", "repr", "xrange", "cmp", "globals", "max", "reversed", "zip", "compile", "hasattr", "memoryview", "round", "__import__", "complex", "hash", "min", "set", "apply", "delattr", "help", "next", "setattr", "buffer", "dict", "hex", "object", "slice", "coerce", "dir", "id", "oct", "sorted", "intern", "None", "False", "True"]

def interleave(inter, f, seq):
    """Call f on each item in seq, calling inter() in between.
    """
    seq = iter(seq)
    try:
        f(next(seq))
    except StopIteration:
        pass
    else:
        for x in seq:
            inter()
            f(x)
            
class Code:
    s = ""
    def __init__(self, id):
        self.id = id
    def write(self, s):
        self.s+=s
    def flush(self):
        pass
    def split(self):
        self.code_lines = self.s.splitlines()
        #self.code_lines = filter(lambda a: a != "", self.code_lines)
        while self.code_lines[0]=="":
            self.code_lines = self.code_lines[1:]
    
    def generate_var_set(self, vars):
        self.orig_vars = vars
        self.var_set = []
        for i in range(len(vars)):
            self.var_set.append(i)
            var = vars[i]
            for j in range(0,i):
                cur_var = vars[j]
                if cur_var==var:
                    self.var_set[-1] = j
                    break
        #print self.var_set
    
    def add_parameter(self, vars, bins):
        
        self.generate_var_set(vars)
        self.orig_bins = bins
        
        param = [] 
    
        def merge_vars(vars):
            var_dict = {}
            for i in vars:
                var_dict[i]=1
            return var_dict                

        self.vars = merge_vars(vars)
        if "self" in self.vars:
            param.append("self")  
        for i in self.vars:
            if i=="self":
                continue
            if not i.startswith("new@"):
                param.append(i)
                 
        self.param = param

    def write_head_line(self,vars, bins):
        self.add_parameter(vars, bins)
        func_name = "helper"+str(self.id)
        if len(self.param)>0:
            param = "("
            for i in self.param:
                param += i+", "
            param = param[:-2]+")"
        else:
            param = "()"
        headline = "def "+func_name+param+":"
        for i in range(len(self.code_lines)):
            self.code_lines[i] = "    "+self.code_lines[i]
        self.code_lines = [headline]+self.code_lines
    
    def rewrite_head_line(self, new_param):
        func_name = "helper"+str(self.id)
        if len(new_param)>0:
            param = "("
            for i in new_param:
                param += (i+", ")
            param = param[:-2]+")"
        else:
            param = "()"
        headline = "def "+func_name+param+":"
        self.code_lines[0] = headline
        
    def add_rets(self, return_vars):
        def merge_vars(vars):
            var_dict = {}
            for i in vars:
                var_dict[i]=1
            return var_dict
        ret_vars = []
        for i in merge_vars(return_vars):
            ret_vars.append(i)
        self.return_vars = ret_vars
        
        
    def write_return_line(self,return_vars):
        
        self.add_rets(return_vars)
        
        ret_line = "    return ("
        if len(self.return_vars)>1:
            for i in self.return_vars:
                ret_line+=(i+", ")
            ret_line = ret_line[:-2]+")"
        elif len(self.return_vars)==1:
            ret_line = ret_line[:-1]+self.return_vars[0]
        else:
            ret_line = ret_line[:-2]
        self.code_lines.append(ret_line)
        
        self.receiver = ret_line.strip()[6:].strip()
    
    def rewrite_return_line(self, new_ret):

        ret_line = "    return ("
        if len(new_ret)>1:
            for i in new_ret:
                ret_line+=(i+", ")
            ret_line = ret_line[:-2]+")"
        elif len(new_ret)==1:
            ret_line = ret_line[:-1]+new_ret[0]
        else:
            ret_line = ret_line[:-2]
        self.code_lines[-1] = ret_line
        

    def get_caller(self):
            
        func_name = "helper"+str(self.id)
        
        s2 = ""
        if self.receiver:
            s2 += self.receiver+" = "
        s2 += self.code_lines[0][4:-1]

        self.caller = s2
    
    def reget_caller(self, new_caller, new_receiver):
            
        func_name = "helper"+str(self.id)
        
        if len(new_caller)>0:
            paramline = "("
            for i in new_caller:
                paramline += i+", "
            paramline = paramline[:-2]+")"
        else:
            paramline = "()"
        
        ret_line = "("
        if len(new_receiver)>1:
            for i in new_receiver:
                ret_line+=(i+", ")
            ret_line = ret_line[:-2]+")"
        elif len(new_receiver)==1:
            ret_line = ret_line[:-1]+new_receiver[0]
        else:
            ret_line = ""
        
        s2 = ""
        if ret_line!="":
            s2 += ret_line+" = "
        s2 += func_name+paramline

        self.caller = s2
    
    def rewrite_code(self, new_vars, diff_bins):
        for j in range(len(new_vars)):
            for i in range(1,len(self.code_lines)-1):
                line = self.code_lines[i]
                tag = self.orig_vars[j]
                if tag.startswith("new@"):
                    tag = tag[4:]
                tag+=("@"+str(j))
                if line.find(tag)>=0:
                    line = line.replace(tag,new_vars[j])
                    break
            self.code_lines[i] = line
        for j in range(len(self.orig_bins)):
            for i in range(1,len(self.code_lines)-1):
                line = self.code_lines[i]
                tag = self.orig_bins[j]
                tag+=("@bin"+str(j))
                new_tag = self.orig_bins[j]
                if j in diff_bins:
                    id = diff_bins.index(j)
                    new_tag = "diff_params["+str(id)+"]"
                if line.find(tag)>=0:
                    line = line.replace(tag,new_tag)
                    break
            self.code_lines[i] = line
                    
    
    def get_code(self):
        s = ""
        for i in self.code_lines:
            s+=i+"\n"
        return s
        
    def output(self,file = sys.stdout):
        self.f = file
        self.f.write("======================\n")
        self.f.write(self.caller+"\n")
        for i in self.code_lines:
            self.f.write(i+"\n")
        self.f.flush()

class Unparser:
    """Methods in this class recursively traverse an AST and
    output source code for the abstract syntax; original formatting
    is disregarded. """

    def __init__(self, tree, lines, src_ast, file = sys.stdout):
        """Unparser(tree, file=sys.stdout) -> None.
         Print the source for tree to file."""
        self.calls = self.crop_calls(lines, src_ast)
        self.variable, self.return_vars = self.crop_vars(lines, src_ast)
        self.mod_calls = []
        self.functions = src_ast.functions
        self.classes = src_ast.classes
        self.lines = lines
        self.cur_call = -1        
        self.incall = False
        self.cur_str = ""
        self.ret_str = False
        self.top_level = True
        self.args = []
        
        self.all_name = []
        self.bins = []
        self.vars = []
        self.is_func_name = False 
        
        self.f = file
        
        #for i in src_ast.raw_scope:
        #    print i
        
        '''for i in self.calls:
            self.f.write("=======================\n")
            self.f.write("Name:"+str(i.name)+"\n")
            self.f.write("line:"+str(i.line)+"\n")
            self.f.write("scope:"+str(i.scope)+"\n")
            self.f.write("source:"+str(i.source)+"\n")
            self.f.write("tree:"+str(i.tree)+"\n") '''
         
        self.f = file
        self.future_imports = []
        self._indent = 0
        self.dispatch(tree)
        self.f.write("\n")
        self.f.flush()
        
        rm_ret_var = []
        for i in self.return_vars:
            if i in self.mod_calls:
                rm_ret_var.append(i)
        for i in rm_ret_var:
            self.return_vars.remove(i)
                
        
        #print "mod_calls:",self.mod_calls
        #print "new_vars:",self.vars
        '''for i in range(len(self.variable)):
            if self.variable[i].startswith("new@"):
                self.variable[i]=""'''
        #print "old_vars:",self.variable
        if self.vars!=self.variable:
            print "ERROR"
        #print "return_vars:",self.return_vars
        #print ""
        
    def crop_calls(self, lines, src_ast):
        calls = []
        for i in src_ast.calls:
            if i.line<lines[0] or i.line>lines[1]:
                continue
            else:
                calls.append(i)
        return calls
    
    def crop_vars(self, lines, src_ast):
        
        #for i in src_ast.functions:
        #    print i.name, i.env

        new_imports = []
        for i in src_ast.raw_imports:
            new_imports.append(i[0])
            if i[1]:
                new_imports.append(i[1])
        
        vars = []
        return_vars = []
        for i in src_ast.var:
            if i[0]<lines[0] or i[0]>lines[1]:
                continue
            else:
                
                if i[1] in build_in_name:
                    continue
                
                if i[1]=="self":
                    vars.append(i[1])
                    return_vars.append(i[1])
                    continue
                
                if i[1] in new_imports:
                    vars.append(i[1])
                    continue
                
                is_class = False
                for j in src_ast.classes:
                    if i[1]==j.name:
                        vars.append(i[1])
                        is_class = True
                        break
                if is_class:
                    continue
                    
                env = ["Global", "Function"]
                is_func = False
                for j in src_ast.functions:
                    if i[1]==j.name:                        
                        if j.env[-1][0] in env:
                            vars.append(i[1])
                            is_func = True
                            break
                if is_func:
                    continue
                        
                vars.append("new@"+i[1])
                for j in src_ast.var:
                    if j[1]==i[1] and j[0]<lines[0]:
                        #-1?
                        if j[2]==-1:
                            #print "global",j
                            vars[-1]=i[1]
                            break
                        scope_i = src_ast.raw_scope[i[2]]
                        scope_j = src_ast.raw_scope[j[2]]
                        if len(scope_j)<=len(scope_i) and scope_j==scope_i[:len(scope_j)]:
                            #print i,j
                            vars[-1]=i[1]
                            break
                for j in src_ast.var:
                    if j[1]==i[1] and j[0]>lines[1]:
                        #-1?
                        if i[2]==-1:
                            #print "return global",i
                            return_vars.append(i[1])
                            break
                        scope_i = src_ast.raw_scope[i[2]]
                        scope_j = src_ast.raw_scope[j[2]]
                        if len(scope_j)>=len(scope_i) and scope_i==scope_j[:len(scope_i)]:
                            #print "return:", i,j
                            return_vars.append(i[1])
                            break
                #print src_ast.raw_scope[i[2]]
                #print i
        #print vars
        return vars,return_vars
    
    def call_dealer(self,tree):
        #self.write("CALL_HERE"+str(tree.lineno)+","+str(tree.col_offset))
        
        def process_mod_call(call):
            self.is_func_name = True
            self.ret_str = True   
            self.dispatch(tree.func)
            self.f.write(self.cur_str)            
            self.ret_str = False
            self.is_func_name = False
  
            #print "@"+self.cur_str, 
            #self.write("unreachable_method["+str(len(self.mod_calls))+"]")
            #self.write("$CALL:"+str(call.source)+"$")
            if not self.cur_str in build_in_name:
                if self.cur_str.find(".")>0:
                    self.mod_calls.append(self.cur_str[:self.cur_str.find(".")])
                else:
                    self.mod_calls.append(self.cur_str)
            self.cur_str = ""
            
            
        self.cur_call+=1
        call = self.calls[self.cur_call]
        if isinstance(call.source, tuple):
            source = call.source
        else:
            source = ("Unknown", call.source)
            
        if source==("Unknown",-1) or source==("member",-1):
            return False
        else: #call import
            process_mod_call(call)
            return True

    def fill(self, text = ""):
        "Indent a piece of text, according to the current indentation level"
        self.f.write("\n"+"    "*self._indent + text)


    def write(self, text):
        "Append a piece of text to the current line."
        if not self.ret_str:
            self.f.write(text)
        else:
            self.cur_str+=(text)

    def enter(self):
        "Print ':', and increase the indentation."
        self.write(":")
        self._indent += 1

    def leave(self):
        "Decrease the indentation level."
        self._indent -= 1

    def dispatch(self, tree):
        "Dispatcher function, dispatching tree type T to method _T."
        if isinstance(tree, list):
            for t in tree:
                self.dispatch(t)
            return
        meth = getattr(self, "_"+tree.__class__.__name__)
        meth(tree)


    ############### Unparsing methods ######################
    # There should be one method per concrete grammar type #
    # Constructors should be grouped by sum type. Ideally, #
    # this would follow the order in the grammar, but      #
    # currently doesn't.                                   #
    ########################################################

    def _Module(self, tree):
        for stmt in tree.body:
            self.dispatch(stmt)

    # stmt
    def _Expr(self, tree):
        self.fill()
        self.dispatch(tree.value)

    def _Import(self, t):
        self.fill("import ")
        interleave(lambda: self.write(", "), self.dispatch, t.names)

    def _ImportFrom(self, t):
        # A from __future__ import may affect unparsing, so record it.
        if t.module and t.module == '__future__':
            self.future_imports.extend(n.name for n in t.names)

        self.fill("from ")
        self.write("." * t.level)
        if t.module:
            self.write(t.module)
        self.write(" import ")
        interleave(lambda: self.write(", "), self.dispatch, t.names)

    def _Assign(self, t):
        self.fill()
        for target in t.targets:
            self.dispatch(target)
            self.write(" = ")
        self.dispatch(t.value)

    def _AugAssign(self, t):
        self.fill()
        self.dispatch(t.target)
        self.write(" "+self.binop[t.op.__class__.__name__]+"= ")
        self.dispatch(t.value)

    def _Return(self, t):
        self.fill("return")
        if t.value:
            self.write(" ")
            self.dispatch(t.value)

    def _Pass(self, t):
        self.fill("pass")

    def _Break(self, t):
        self.fill("break")

    def _Continue(self, t):
        self.fill("continue")

    def _Delete(self, t):
        self.fill("del ")
        interleave(lambda: self.write(", "), self.dispatch, t.targets)

    def _Assert(self, t):
        self.fill("assert ")
        self.dispatch(t.test)
        if t.msg:
            self.write(", ")
            self.dispatch(t.msg)

    def _Exec(self, t):
        self.fill("exec ")
        self.dispatch(t.body)
        if t.globals:
            self.write(" in ")
            self.dispatch(t.globals)
        if t.locals:
            self.write(", ")
            self.dispatch(t.locals)

    def _Print(self, t):
        self.fill("print ")
        do_comma = False
        if t.dest:
            self.write(">>")
            self.dispatch(t.dest)
            do_comma = True
        for e in t.values:
            if do_comma:self.write(", ")
            else:do_comma=True
            self.dispatch(e)
        if not t.nl:
            self.write(",")

    def _Global(self, t):
        self.fill("global ")
        interleave(lambda: self.write(", "), self.write, t.names)

    def _Yield(self, t):
        self.write("(")
        self.write("yield")
        if t.value:
            self.write(" ")
            self.dispatch(t.value)
        self.write(")")

    def _Raise(self, t):
        self.fill('raise ')
        if t.type:
            self.dispatch(t.type)
        if t.inst:
            self.write(", ")
            self.dispatch(t.inst)
        if t.tback:
            self.write(", ")
            self.dispatch(t.tback)

    def _TryExcept(self, t):
        self.fill("try")
        self.enter()
        self.dispatch(t.body)
        self.leave()

        for ex in t.handlers:
            self.dispatch(ex)
        if t.orelse:
            self.fill("else")
            self.enter()
            self.dispatch(t.orelse)
            self.leave()

    def _TryFinally(self, t):
        if len(t.body) == 1 and isinstance(t.body[0], ast.TryExcept):
            # try-except-finally
            self.dispatch(t.body)
        else:
            self.fill("try")
            self.enter()
            self.dispatch(t.body)
            self.leave()

        self.fill("finally")
        self.enter()
        self.dispatch(t.finalbody)
        self.leave()

    def _ExceptHandler(self, t):
        self.fill("except")
        if t.type:
            self.write(" ")
            self.dispatch(t.type)
        if t.name:
            self.write(" as ")
            self.dispatch(t.name)
        self.enter()
        self.dispatch(t.body)
        self.leave()

    def _ClassDef(self, t):
        self.write("\n")
        for deco in t.decorator_list:
            self.fill("@")
            self.dispatch(deco)
        self.fill("class "+t.name)
        if t.bases:
            self.write("(")
            for a in t.bases:
                self.dispatch(a)
                self.write(", ")
            self.write(")")
        self.enter()
        self.dispatch(t.body)
        self.leave()

    def _FunctionDef(self, t):
        self.write("\n")
        for deco in t.decorator_list:
            self.fill("@")
            self.dispatch(deco)
        self.fill("def "+t.name + "(")
        self.dispatch(t.args)
        self.write(")")
        self.enter()
        self.dispatch(t.body)
        self.leave()

    def _For(self, t):
        self.fill("for ")
        self.dispatch(t.target)
        self.write(" in ")
        self.dispatch(t.iter)
        self.enter()
        self.dispatch(t.body)
        self.leave()
        if t.orelse:
            self.fill("else")
            self.enter()
            self.dispatch(t.orelse)
            self.leave()

    def _If(self, t):
        self.fill("if ")
        self.dispatch(t.test)
        self.enter()
        self.dispatch(t.body)
        self.leave()
        # collapse nested ifs into equivalent elifs.
        while (t.orelse and len(t.orelse) == 1 and
               isinstance(t.orelse[0], ast.If)):
            t = t.orelse[0]
            self.fill("elif ")
            self.dispatch(t.test)
            self.enter()
            self.dispatch(t.body)
            self.leave()
        # final else
        if t.orelse:
            self.fill("else")
            self.enter()
            self.dispatch(t.orelse)
            self.leave()

    def _While(self, t):
        self.fill("while ")
        self.dispatch(t.test)
        self.enter()
        self.dispatch(t.body)
        self.leave()
        if t.orelse:
            self.fill("else")
            self.enter()
            self.dispatch(t.orelse)
            self.leave()

    def _With(self, t):
        self.fill("with ")
        self.dispatch(t.context_expr)
        if t.optional_vars:
            self.write(" as ")
            self.dispatch(t.optional_vars)
        self.enter()
        self.dispatch(t.body)
        self.leave()

    # expr
    def _Str(self, tree):
        # if from __future__ import unicode_literals is in effect,
        # then we want to output string literals using a 'b' prefix
        # and unicode literals with no prefix.
        if "unicode_literals" not in self.future_imports:
            self.write(repr(tree.s)+"@bin"+str(len(self.bins)))
            self.bins.append(repr(tree.s))
        elif isinstance(tree.s, str):
            self.write("b" + repr(tree.s)+"@bin"+str(len(self.bins)))
            self.bins.append("b" + repr(tree.s))
        elif isinstance(tree.s, unicode):
            self.write(repr(tree.s).lstrip("u")+"@bin"+str(len(self.bins)))
            self.bins.append(repr(tree.s).lstrip("u"))
        else:
            assert False, "shouldn't get here"

    def _Name(self, t):
        
        self.all_name.append(t.id)
        #if t.id=="ui":
            #print "ui=======",self.rec_var
        if t.id in build_in_name:
            self.write(t.id+"@bin"+str(len(self.bins)))
            self.bins.append(t.id)   
        else:
            idx = len(self.vars)
            should_var = self.variable[idx]
            if should_var.startswith("new@"):
                should_id = should_var[4:]
                if should_id!=t.id:
                    self.write(t.id)
                else:
                    self.vars.append("new@"+t.id)
                    self.write(t.id+"@"+str(idx))
            else:
                if t.id!=should_var:
                    self.write(t.id)
                else:
                    self.vars.append(t.id)
                    self.write(t.id+"@"+str(idx))
                    
           
        '''if not self.is_func_name: 
            #print self.variable 
            #print self.vars
            #print self.incall
            #print self.is_func_name
            #print t.id
            if t.id in build_in_name:
                self.write(t.id)
            elif self.variable[len(self.vars)]!="new" :
                if t.id==self.variable[len(self.vars)]:
                    self.vars.append(t.id)
                self.write(t.id)#+"@VAR")
            else:
                self.vars.append("")
                self.write(t.id)
        else:
            #del self.variable[len(self.vars)]
            self.write(t.id)'''

            

    def _Repr(self, t):
        self.write("`")
        self.dispatch(t.value)
        self.write("`")

    def _Num(self, t):
        tmp_s = ""
        repr_n = repr(t.n)
        # Parenthesize negative numbers, to avoid turning (-1)**2 into -1**2.
        if repr_n.startswith("-"):
            self.write("(")
            tmp_s += "("
        # Substitute overflowing decimal literal for AST infinities.
        self.write(repr_n.replace("inf", INFSTR))
        tmp_s += (repr_n.replace("inf", INFSTR))
        if repr_n.startswith("-"):
            self.write(")")
            tmp_s += ")"
        self.write("@bin"+str(len(self.bins)))
        self.bins.append(tmp_s)

    def _List(self, t):
        self.write("[")
        interleave(lambda: self.write(", "), self.dispatch, t.elts)
        self.write("]")

    def _ListComp(self, t):
        self.write("[")
        self.dispatch(t.elt)
        for gen in t.generators:
            self.dispatch(gen)
        self.write("]")

    def _GeneratorExp(self, t):
        self.write("(")
        self.dispatch(t.elt)
        for gen in t.generators:
            self.dispatch(gen)
        self.write(")")

    def _SetComp(self, t):
        self.write("{")
        self.dispatch(t.elt)
        for gen in t.generators:
            self.dispatch(gen)
        self.write("}")

    def _DictComp(self, t):
        self.write("{")
        self.dispatch(t.key)
        self.write(": ")
        self.dispatch(t.value)
        for gen in t.generators:
            self.dispatch(gen)
        self.write("}")

    def _comprehension(self, t):
        self.write(" for ")
        self.dispatch(t.target)
        self.write(" in ")
        self.dispatch(t.iter)
        for if_clause in t.ifs:
            self.write(" if ")
            self.dispatch(if_clause)

    def _IfExp(self, t):
        self.write("(")
        self.dispatch(t.body)
        self.write(" if ")
        self.dispatch(t.test)
        self.write(" else ")
        self.dispatch(t.orelse)
        self.write(")")

    def _Set(self, t):
        assert(t.elts) # should be at least one element
        self.write("{")
        interleave(lambda: self.write(", "), self.dispatch, t.elts)
        self.write("}")

    def _Dict(self, t):
        self.write("{")
        def write_pair(pair):
            (k, v) = pair
            self.dispatch(k)
            self.write(": ")
            self.dispatch(v)
        interleave(lambda: self.write(", "), write_pair, zip(t.keys, t.values))
        self.write("}")

    def _Tuple(self, t):
        self.write("(")
        if len(t.elts) == 1:
            (elt,) = t.elts
            self.dispatch(elt)
            self.write(",")
        else:
            interleave(lambda: self.write(", "), self.dispatch, t.elts)
        self.write(")")

    unop = {"Invert":"~", "Not": "not", "UAdd":"+", "USub":"-"}
    def _UnaryOp(self, t):
        self.write("(")
        self.write(self.unop[t.op.__class__.__name__])
        self.write(" ")
        # If we're applying unary minus to a number, parenthesize the number.
        # This is necessary: -2147483648 is different from -(2147483648) on
        # a 32-bit machine (the first is an int, the second a long), and
        # -7j is different from -(7j).  (The first has real part 0.0, the second
        # has real part -0.0.)
        if isinstance(t.op, ast.USub) and isinstance(t.operand, ast.Num):
            self.write("(")
            self.dispatch(t.operand)
            self.write(")")
        else:
            self.dispatch(t.operand)
        self.write(")")

    binop = { "Add":"+", "Sub":"-", "Mult":"*", "Div":"/", "Mod":"%",
                    "LShift":"<<", "RShift":">>", "BitOr":"|", "BitXor":"^", "BitAnd":"&",
                    "FloorDiv":"//", "Pow": "**"}
    def _BinOp(self, t):
        self.write("(")
        self.dispatch(t.left)
        self.write(" " + self.binop[t.op.__class__.__name__] + " ")
        self.dispatch(t.right)
        self.write(")")

    cmpops = {"Eq":"==", "NotEq":"!=", "Lt":"<", "LtE":"<=", "Gt":">", "GtE":">=",
                        "Is":"is", "IsNot":"is not", "In":"in", "NotIn":"not in"}
    def _Compare(self, t):
        self.write("(")
        self.dispatch(t.left)
        for o, e in zip(t.ops, t.comparators):
            self.write(" " + self.cmpops[o.__class__.__name__] + " ")
            self.dispatch(e)
        self.write(")")

    boolops = {ast.And: 'and', ast.Or: 'or'}
    def _BoolOp(self, t):
        self.write("(")
        s = " %s " % self.boolops[t.op.__class__]
        interleave(lambda: self.write(s), self.dispatch, t.values)
        self.write(")")

    def _Attribute(self,t):
        self.dispatch(t.value)
        # Special case: 3.__abs__() is a syntax error, so if t.value
        # is an integer literal then we need to either parenthesize
        # it or add an extra space to get 3 .__abs__().
        if isinstance(t.value, ast.Num) and isinstance(t.value.n, int):
            self.write(" ")
        self.write(".")
        self.write(t.attr)
  
    def _Call(self, t):
        mod = False
        #print "F:=========",t.func._fields
        
        cur_incall = self.incall

        if not self.incall:
            self.incall = True
            if self.call_dealer(t):
                mod = True       
        
        if not mod:                        
            self.dispatch(t.func)            
        '''else:
            self.is_func_name = True
            self.ret_str = True
            self.dispatch(t.func)
            self.ret_str = False
            self.mod_calls[-1] = self.cur_str
            self.cur_str = ""
            self.is_func_name = False'''
            
        self.write("(")
        if not cur_incall:
            self.incall = False
        comma = False
        for e in t.args:
            if comma: self.write(", ")
            else: comma = True
            self.dispatch(e)
        for e in t.keywords:
            if comma: self.write(", ")
            else: comma = True
            self.dispatch(e)
        if t.starargs:
            if comma: self.write(", ")
            else: comma = True
            self.write("*")
            self.dispatch(t.starargs)
        if t.kwargs:
            if comma: self.write(", ")
            else: comma = True
            self.write("**")
            self.dispatch(t.kwargs)
        self.write(")")
        

    def _Subscript(self, t):
        self.dispatch(t.value)
        self.write("[")
        self.dispatch(t.slice)
        self.write("]")

    # slice
    def _Ellipsis(self, t):
        self.write("...")

    def _Index(self, t):
        self.dispatch(t.value)

    def _Slice(self, t):
        if t.lower:
            self.dispatch(t.lower)
        self.write(":")
        if t.upper:
            self.dispatch(t.upper)
        if t.step:
            self.write(":")
            self.dispatch(t.step)

    def _ExtSlice(self, t):
        interleave(lambda: self.write(', '), self.dispatch, t.dims)

    # others
    def _arguments(self, t):
        first = True
        # normal arguments
        defaults = [None] * (len(t.args) - len(t.defaults)) + t.defaults
        for a,d in zip(t.args, defaults):
            if first:first = False
            else: self.write(", ")
            if self.top_level:
                self.args.append(a.id)
                
            self.dispatch(a),
            if d:
                self.write("=")
                self.dispatch(d)

        # varargs
        if t.vararg:
            if first:first = False
            else: self.write(", ")
            if self.top_level:
                self.args.append("*"+str(t.vararg))
            self.write("*")
            self.write(t.vararg)

        # kwargs
        if t.kwarg:
            if first:first = False
            else: self.write(", ")
            if self.top_level:
                self.args.append("**"+str(t.kwarg))
            self.write("**"+t.kwarg)
        
        self.top_level = False

    def _keyword(self, t):
        self.write(t.arg)
        self.write("=")
        self.dispatch(t.value)

    def _Lambda(self, t):
        self.write("(")
        self.write("lambda ")
        self.dispatch(t.args)
        self.write(": ")
        self.dispatch(t.body)
        self.write(")")

    def _alias(self, t):
        self.write(t.name)
        if t.asname:
            self.write(" as "+t.asname)

def generateNewCode(id, source, lines, src_ast, tag, output=sys.stdout):
    tree = compile(source, tag[0], "exec", ast.PyCF_ONLY_AST)
    merged = Code(id)
    up = Unparser(tree, lines, src_ast, merged)
    merged.split()    
    merged.write_head_line(up.vars, up.bins)
    merged.write_return_line(up.return_vars)
    merged.get_caller()
    #merged.output()
    #print up.vars
    return merged


'''def mergeDiffResults(merged_list):
    def mergeSet(setList):
        d = {}
        for i in setList:
            for j in i:
                if j in d:
                    d[j] += 1
                else:
                    d[j] = 1
        return d
    
    paramList = []
    returnList = []
    
    for i in merged_list:
        paramList.append(i.param)
        returnList.append(i.return_vars)
    
    paramList = mergeSet(paramList).keys()
    returnList = mergeSet(returnList).keys()
    
    for i in merged_list:
        i.rewrite_head_line(paramList)
        i.rewrite_return_line(returnList)
        i.reget_caller(paramList, returnList)
    
    return merged_list'''

def checkMergable(merged_list):
    mergable = True
    for merge in merged_list[1:]:
        if merge.var_set!=merged_list[0].var_set:
            mergable = False
        if len(merge.orig_bins) != len(merged_list[0].orig_bins):
            mergable = False
            
    if mergable:
        #print "YES MERGABLE"
        return True
    else:
        #print "NOT MERGABLE"
        return False
    

def generateCommonCode(merged_list):
    common_vars = []
    common_param = []
    common_ret = []
    new_caller = []
    new_receiver = []
    for i in merged_list:
        new_caller.append([])
        new_receiver.append([])
    
    def mergeNames(names):
        new_name = []
        for i in names:
            if i.startswith("new@"):
                i = i[4:]
            if not i in new_name:
                new_name.append(i)
        if len(new_name)==1:
            return new_name[0]
        else:
            name = ""
            for i in new_name:
                name+=(i+"_")
            name=name[:-1]
            return name
    
    def setTrue(li):
        for i in li:
            if i:
                return True
        return False       
    
    for i in range(len(merged_list[0].var_set)):
        names = []
        is_param = []
        is_ret = []
        for merge in merged_list:
            names.append(merge.orig_vars[i])
            if merge.orig_vars[i] in merge.param:
                is_param.append(True)
            else:
                is_param.append(False)
            if merge.orig_vars[i] in merge.return_vars:
                is_ret.append(True)
            else:
                is_ret.append(False)
        name = mergeNames(names)
        common_vars.append(name)
        if setTrue(is_param) and not name in common_param:
            common_param.append(name)
            for i2 in range(len(is_param)):
                if is_param[i2]:
                    new_caller[i2].append(names[i2])
                else:
                    new_caller[i2].append("None")
        if setTrue(is_ret) and not name in common_ret:
            common_ret.append(name)
            for i2 in range(len(is_ret)):
                if is_ret[i2]:
                    new_receiver[i2].append(names[i2])
                else:
                    new_receiver[i2].append("None")
    
    diff_bins = []          
    for i in range(len(merged_list[0].orig_bins)):
        for merge in merged_list[1:]:
            if merge.orig_bins[i]!=merged_list[0].orig_bins[i]:
                diff_bins.append(i)
                break
    #print "DIFF_BIN :", diff_bins
    
    if len(diff_bins)>0:
        common_param.append("*diff_params")
        param_bins = []
        for i in merged_list:
            param_bins.append([])
            for j in diff_bins:
                param_bins[-1].append(i.orig_bins[j])
            for j in param_bins[-1]:
                new_caller[merged_list.index(i)].append(j)
            #print "PARAM :", param_bins[-1]
            
    
    for i in range(len(merged_list)):
        merge = merged_list[i]
        #merge.output()
        merge.rewrite_code(common_vars, diff_bins)
        merge.rewrite_head_line(common_param)
        merge.rewrite_return_line(common_ret)
        merge.reget_caller(new_caller[i], new_receiver[i])
        #merge.output()
        merged_list[i] = merge
    
    return merged_list
            
            
        
         

    
