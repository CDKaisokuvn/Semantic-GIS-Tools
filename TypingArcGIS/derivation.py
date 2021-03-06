#-------------------------------------------------------------------------------
# Name:        Derivation
# Purpose:     Implements a typed spatio-temporal derivation graph.The vertices in
#               this graph are type instances, namely operations (of type function)
#               or their inputs and outputs (of any type). All vertices
#               are typed with types from the module Typing.
#               A derivation graph is generated by adding operations
#               (with inputs and outputs added
#               in the constructor of the operation). See test for examples.
# Author:      Simon Scheider
#
# Created:     30-04-2016
# Copyright:   (c) simon 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------


from Typing import *

class inst:
    """This is the class of type instances (=nodes in a derivation graph). Instances have some type from "Typing" which is set during their creation. If nothing is set, the default type is a type variable."""
    id= "inst"
    succ = {} #The predecessor node in the graph stored when DFS searching. Here called successor because we are backtracking
    link = "" # This is the kind of backlink found when DFS searching through the graph
    col= "w" # This is the color used in DFS backtracking through the derivation graph, inititially "white"
    def __init__(self, type=a(), name="inst"):
        self.type = type
        """Atrribute that links this instance to its type"""
        if (name == "inst"):
            self.id ="".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        else:
            self.id = name
    def __str__(self):
        return self.id+"::"+str(self.type)

class oprtn(inst):
    """This is a concrete (executed) instance of an operation (e.g. an executed method of some tool like R). It is an instance, has a function type, but furthermore, it also has an input and an output instance generated by its execution."""
    def __init__(self, fun, inputl, output, name="inst"):
        if not isinstance(fun,Fun):
            raise ValueError('Operations need to be functions!')
        if not isinstance(output,inst):
            raise ValueError('Operations need to have an instance as output')
        if not (isinstance(inputl,inst) or isinstance(inputl,list)):
           raise ValueError('Operations need to have instances as input')
        if (name == "inst"):
            self.id ="".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        else:
            self.id = name
        self.type = fun
        self.input= inputl #The list of input instances. Can also be a single instance.
        self.multi = False #Says whether the the input is single or multi
        if isinstance(self.input,list):
            self.multi = True
        self.output = output #The single output instance
    def __str__(self):
        return self.id+"::"+str(self.type)

class dgraph:
    """This is a tree of operators, stored in two dictionaries with inputs/output as key. Therefore, there is always a defined predecessor operation of an output and a root."""
    def __init__(self):
        self.indict = {}
        self.outdict = {}
        self.operationlist=[] #This list contains the non-normalized (n-ary) operations together with objects supplying their types after unification.

    def __str__(self):
        s = "Graph triples: "
        #for i in self.indict.keys():
        #   s += "input:"+ str(i)+" oper:"+ str(self.indict[i])+" output:"+ str((self.indict[i]).output)+" $$ "
        for i in self.operationlist:
            if (i[0].multi):
                for input in (i[0].input):
                    s += str(input)+" is input of "+ str(i[0])+" $$ "
                s += str(i[0])+" output "+ str(i[0].output)+" $$ "
            else:
                s += str(i[0].input)+" is input of "+ str(i[0])+" $$ "
                s += str(i[0])+" output "+ str(i[0].output)+" $$ "
        return s

    def add(self,operation):
        """This adds an operation to the graph (registers it in the two dictionaries and a list that represent the graph)"""
        if isinstance(operation,oprtn):
            if (operation.output not in self.outdict.keys()):
                lastoutput = operation.output
                #self.outdict[operation.output]=operation
                if (operation.multi):
                    """If operation is multi-ary, then normalize: generate new functions for each of its inputs and nest the functions into each other, starting from the last output backwards."""
                    count = 0
                    for i in reversed(operation.input):
                        count=count+1
                        stype = Fun(a(),a())
                        if (count == len(operation.input)):# if the first input of the original operation is reached, take the operation type otherwise take a variable
                            stype = operation.type
                        x = oprtn(stype, i, lastoutput)
                        if(count == len(operation.input)):
                            self.operationlist.append([operation,x]) #add the non-normalized operation to a list, but get its type from its first normalized function
                        #print str(lastoutput)
                        self.indict[i] = x
                        self.outdict[lastoutput]= x
                        lastoutput = x #set the new operation as last output, because we move backwards from outputs to inputs
                else:
                    self.operationlist.append([operation,operation])
                    self.indict[operation.input] = operation
                    self.outdict[operation.output]= operation
            else:
                raise ValueError('No output can be output of two operations (this is a tree)!')

        else:
            raise ValueError('Only Operations can be added!')

    def getRoot(self):
        """Gets the root of the tree (not really needed, but saves some recursions when DFS searching)"""
        k =list(self.indict.keys())
        ok = self.indict.get(k[0])
        root ={}
        default = "no"
        while (self.indict.get(ok.output,default)!="no" or isinstance(ok.output,oprtn)):
            #root = ok.output
            if self.indict.get(ok.output,default)!="no":
                ok =self.indict.get(ok.output)
            elif isinstance(ok.output,oprtn):
                ok = ok.output
        return ok.output

    def TypeUnifyGraph(self):
        """This is the central type unification command for the graph. It visits each node in a DFS fashion, unifies types and propagates types through the derivation graph. The resulting graph may have some new types."""
        self.DFSVisit(self.getRoot())
        for o in self.operationlist: #update types in operation list
            o[0].type=o[1].type

    def DFSVisit(self, n):
        """An implementation of Depth First Search on the derivation graph"""
        n.col = "g" # colors this node in grey
        for v in self.getneighbours(n):
            if v[0].col == "w":
                v[0].succ = n # stores the predecessor link
                v[0].link = v[1] # stores the kind of link to the predecessor (input, output,...)
                self.DFSVisit(v[0])
        n.col = "b" # colors this node in black
        #print "unify: "+str(n.type) + " "+str(n.type.__class__)+ " "+str(n.type.setType) +" "+str(n.type.setType.subType(n.type))
        n.type = n.type.unify()
        #print "unified?: "+str(n.type)
        if n.link != "": # if there is a predecessor, then propagate the type of this node to the predecessor
            self.propagateType(n,n.link,n.succ)

    def propagateType(self,n,link,succ):
        """Propagates types along the edges in the derivation graph, depending on the kind of edge (input, output)"""
        #print str(n)+" "+str(link)+" "+str(succ)+"..."
        if link == "in":
            succ.type.setIn=n.type
        elif link == "out":
            succ.type.setType = n.type.getOut
            #print str(n.type.getOut)


    def getneighbours(self,n):
        """Gets the neighbors (predecessor nodes) in the graph of node n"""
        list = []
        if isinstance(n,oprtn):
            if n.multi:
                for i in n.input:
                    list.append([i,"in"])
            else:
                list.append([n.input,"in"])
        if self.outdict.get(n, "no")!="no":
            list.append([self.outdict[n],"out"])
        #print list
        return list






def test():
    #Note: the dgraph should be a tree with the overall output as root.

    #Testing operations with n-ary inputs (a list of inputs) as well as unary input and with operations as out put and input
    x = inst(a()) #an instance of any type
    inst1  = inst(a()) #an instance of any type
    binop = oprtn(Fun(a(),Fun(T(),Q())), [inst(S()),inst(T())], x) #an operation with binary input and untyped output
    binop3 = oprtn(Fun(a(),a()), inst1, inst(a())) #an operation that is output of another operation
    binop2 = oprtn(Fun(Q(),Fun(Q(),Q())), x, binop3) #an operation that outputs another operation
    fun     = inst(Fun(S(),Q())) #note: this is a function which is not ! an operation (because it has no input or output instances)
    binop4 = oprtn(Fun(Fun(a(),a()),Q()),fun, inst1) #an operation with a function as input

    #Testing the GIS tool types
    my_bu_dist = inst(a())
    my_bu_ext = inst(a())
    u =inst(a())
    ed1 = oprtn(EuclideanDistance(), [inst(Q()),inst(a())],my_bu_dist)
    ed2 = oprtn(EuclideanDistance(), [inst(Q()),inst(a())],u)
    rc = oprtn(ReClassify(),my_bu_dist,my_bu_ext)
    route2_cost = inst(a())
    lma = oprtn(LocalMA(),[my_bu_ext,u],route2_cost)

    g1 = dgraph()
    g1.add(ed1)
    g1.add(ed2)
    g1.add(lma)

    print "Before unification: "+str(g1)
    g1.TypeUnifyGraph()
    print "After unification: "+str(g1)

    g2 = dgraph()
    g2.add(binop)
    g2.add(binop2)
    g2.add(binop3)
    g2.add(binop4)



    print "Before unification: "+str(g2)
    g2.TypeUnifyGraph()
    print "After unification: "+str(g2)


if __name__ == '__main__':
    test()
