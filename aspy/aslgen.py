# python client for ASL
# asl generator and pipeline
# prototype and demo

import json
import sys
import os
import xml.dom.minidom
import StringIO
import re

# locate analyic_server from the build/checker library
# sys.path.append(sys.path.append(os.path.join(os.path.dirname(__file__),"../../../../build/checker/lib")))

#from analytic_server import analyticServer
from aspy.analytic_server import analyticServer

class as_datamodel(object):

    def __init__(self,dmxml):
        self.dmxml = dmxml
        self.fields = []
        doc = xml.dom.minidom.parse(StringIO.StringIO(self.dmxml))
        fields = doc.getElementsByTagName("Field")
        for field in fields:
            name = field.getAttribute("name")
            storage = field.getAttribute("storage")
            self.fields.append((name,storage))

    def __repr__(self):
        return str(self.fields)

    def getFieldNames(self):
        return [name for (name,_) in self.fields]

class as_resultset(object):

    def __init__(self,server,dsname,removeOnClose=False):
        self.server = server
        self.dsname = dsname
        self.removeOnClose = removeOnClose
        dmxml = self.server.get_datasource_datamodel(dsname)
        self.dm = as_datamodel(dmxml)
        self.row = -1
        self.batchsize = 1000
        self.batchdata = []

    def reset(self):
        self.row = -1
        self.batchsize = 1000
        self.batchdata = []

    def __iter__(self):
        return self

    def next(self):
        if self.row == -1:
            self.row += 1
            return self.dm.getFieldNames()
        else:
            if len(self.batchdata) == 0:
                self.getBatch()
            if len(self.batchdata) == 0:
                raise StopIteration
            result = self.batchdata[0]
            self.batchdata = self.batchdata[1:]
            self.row += 1
            return result

    def getBatch(self):   
        self.batchdata = json.loads(self.server.get_datasource_records(self.dsname,self.row,self.batchsize))

    def close(self):
        if self.removeOnClose:
            self.server.remove_datasource(self.dsname)

    def toPandas(self):
        import pandas as pd
        self.reset()
        rows = [row for row in self]
        headers = rows[0]
        data = rows[1:]
        dd = {}
        for i in range(0,len(headers)):
            header = headers[i]
            column = [row[i] for row in data]
            dd[header] = column
        return pd.DataFrame(dd)

class as_pipeline(object):
       
    def __init__(self,server):
        self.server = server
        self.ops = []

    class as_datasource_read(object):

        def __init__(self,datasource):
            self.ds = datasource

        def to_asl(self):
            return "read(%s)"%(json.dumps({"dataSource":self.ds}))

    class as_aggregate(object):
        
        def __init__(self,keys,functions):
            self.keys = keys
            self.functions = functions

        def to_asl(self):
            conf = {}
            output = []
            for key in self.keys:
                output.append({ "input":key, "function":"key"})
            for function in self.functions:
                if function == "count":
                    output.append({ "function":"count" })
                else:
                    aggfn = function[:function.index("_")]
                    inp = function[function.index("_")+1:]
                    output.append({ "outName":function, "input":inp, "function":aggfn })
            conf["output"] = output
            return "aggregate(%s)"%(json.dumps(conf))

    class as_select(object):

        def __init__(self,expr):
            m = re.search('lambda ([^:]+):(.*)',expr)
            self.varname = m.group(1)
            self.body = m.group(2)

        def to_asl(self):
            return "filterRecords(_,ctx => %s => %s)"%(self.varname,self.body)

    class as_derive(object):

        def __init__(self,name,expr):
            m = re.search('lambda ([^:]+):(.*)',expr)
            self.name = name
            self.varname = m.group(1)
            self.body = m.group(2)

        def to_asl(self):
            return "deriveField(_,ctx => %s => (\"%s\",%s))"%(self.varname,self.name,self.body)

    class as_datasource_write(object):

        def __init__(self,datasource,mode):
            self.ds = datasource
            self.mode = mode

        def to_asl(self):
            return "write(%s)"%(json.dumps({"dataSource":self.ds,"mode":self.mode}))

    def read_datasource(self,datasource):
        self.ops = [as_pipeline.as_datasource_read(datasource)]
        return self

    def aggregate(self,keys,functions):
        self.ops.append(as_pipeline.as_aggregate(keys,functions))
        return self

    def select(self,lf):
        self.ops.append(as_pipeline.as_select(lf))
        return self

    def derive(self,name,expr):
        self.ops.append(as_pipeline.as_derive(name,expr))
        return self

    def write_datasource(self,datasource,mode):
        self.ops.append(as_pipeline.as_datasource_write(datasource,mode))
        return self

    def __repr__(self):
        s = ""
        for i in range(0,len(self.ops)):
            if i:
                s += " -> "
            s += self.ops[i].to_asl()
        return s

    def run(self):
        if len(self.ops) > 0 and isinstance(self.ops[0],as_pipeline.as_datasource_read):
            if isinstance(self.ops[-1],as_pipeline.as_datasource_write):
                self.server.run(self)
                return None
            else:
                dsName = "foobaz" # FIXME should use a UUID
                self.server.create_writable_datasource(dsName)
                self.write_datasource(dsName,"overwrite")
                self.server.run(self)
                self.ops = self.ops[:-1]
                return as_resultset(self.server,dsName,True)
        else:
            raise Exception("cannot run malformed pipeline")

class analytic_server(object):

    def __init__(self, host, port, useSSL, user, password):
        self.server = analyticServer(host,port, None, False)
        self.server.login(user,password)

    def run(self,pipeline,project="public"):
        self.server.lock_project("public")
        try:
            self.server.run_asl("public",str(pipeline))    
        finally:
            self.server.commit_project("public")

    def remove_datasource(self,name):
        self.server.remove_datasource(name)
             
    def create_writable_datasource(self,name,project="public"):
        self.server.create_writable_datasource(name,project)

    def get_datasource_records(self,name,start,count):
        return self.server.get_datasource_records(name,start,count)
           
    def get_datasource_datamodel(self,name):
        return self.server.get_datasource_datamodel(name)

    def create_pipeline(self):
        return as_pipeline(self)


    
        
