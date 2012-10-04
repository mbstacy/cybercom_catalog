import cherrypy
import json, os,ast,types
import urllib2,cookielib
#import pickle
#from celery.result import AsyncResult
#from celery.execute import send_task
#from celery.task.control import inspect
#from pymongo import Connection
from datetime import datetime
from Cheetah.Template import Template
import mdb_model
from json_handler import handler
from get import find,group,distinct
from cybercom.data.mongo import get
#from convert import *
import ConfigParser
'''

MongoDB web interface with 

'''
templatepath= os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
cybercomdir = '/opt/cybercom'
cybercomfile='cybercom.conf'
cfgfile = os.path.join(os.path.expanduser(cybercomdir), cybercomfile)
config= ConfigParser.RawConfigParser()

def mimetype(type):
    def decorate(func):
        def wrapper(*args, **kwargs):
            cherrypy.response.headers['Content-Type'] = type
            return func(*args, **kwargs)
        return wrapper
    return decorate


class Root(object):
    def __init__(self):
        self.mongo = mdb_model.mongo_catalog()
        config.read(cfgfile)
        host = config.get('database','host')
        port = int(config.get('database','port'))
        self.getdata = get.data(host, port)
    @cherrypy.expose
    def index(self):
        #raise cherrypy.InternalRedirect("data")
        raise cherrypy.HTTPRedirect("/catalog/data/")
    @cherrypy.expose
    def data(self,db=None,col='data',query={},page=1,nPerpage=10, **kwargs):
        fname='data'
        try:
            if cherrypy.request.login:
                user = cherrypy.request.login
            else:
                user = "guest"
        except:
            user = "guest"
        #return str(user)
        res,pub,cpub,list_all_pub= self.mongo.getdatabase(username=user,multiple=True)
        res.sort()
        pub.sort()
        if not db:
            nameSpace = dict(database=res,pub_acc=pub,com_acc=cpub,baseurl=cherrypy.url('/')[:-1],FName=fname,user=user)        
            t = Template(file = templatepath + '/database.tmpl', searchList=[nameSpace])
            return t.respond()
        if db not in res:
            if db not in list_all_pub:
                return json.dumps([{'status':False,'description':'User dos not have permissions to view Data Commons'}], default = handler)
        skip=(int(page)-1)*int(nPerpage)
        limit= int(nPerpage)
        dump_out=[]
        cur = self.mongo.getDoc(db,col,query,skip,limit)
        for item in cur:
            dump_out.append(item)
        serialized = json.dumps(dump_out, default = handler, sort_keys=True)#, indent=4)
        cur =''
        prev=1
        next=1
        #set Metadata
        dump_out=[]
        cur_meta = self.mongo.getDoc(db,'Metadata')#,query,skip,limit)
        for item in cur_meta:
            dump_out.append(item)
        serial_meta = json.dumps(dump_out, default = handler, sort_keys=True)#, indent=4)
        #set Location
        dump_out=[]
        cur_meta = self.mongo.getDoc(db,'Location')#,query,skip,limit)
        for item in cur_meta:
            dump_out.append(item)
        serial_location = json.dumps(dump_out, default = handler, sort_keys=True)#, indent=4)
        info = self.mongo.getInfo(db,col,query,skip,limit)
        nameSpace = dict(database=db,collection=col,data=cur,baseurl=cherrypy.url('/')[:-1],
            serial=serialized,FName=fname,prev=prev,next=next,rec_info=info,user=user,serialmeta=serial_meta,seriallocation=serial_location)
        t = Template(file = templatepath + '/data.tmpl', searchList=[nameSpace])
        return t.respond()
    @cherrypy.expose
    def ajax_data(self,db=None,col='data',query={},page=1,nPerpage=10, **kwargs):
        skip=(int(page)-1)*int(nPerpage)
        limit= int(nPerpage)
        dump_out=[]
        cur = self.mongo.getDoc(db,col,query,skip,limit)
        for item in cur:
            dump_out.append(item)
        return json.dumps(dump_out, default = handler, sort_keys=True)
    
    @cherrypy.expose
    def save(self, **kwrgs):
        try:
            if cherrypy.request.login:
                user = cherrypy.request.login
            else:
                user = "guest"
        except:
            user = "guest"
        if cherrypy.request.method =="POST":
            try:
                if cherrypy.request.headers['Content-Type'] == "application/json":
                    cl = cherrypy.request.headers['Content-Length']
                    doc = json.loads(cherrypy.request.body.read(int(cl)))
                    data = doc['data']
                    if doc.has_key('date_keys'):
                        dkey = doc['date_keys']
                    else:
                        dkey=[]
                else:  
                    doc=cherrypy.request.params
                    data = json.loads(doc['data'])
                    if doc.has_key('date_keys'):
                        dkey = ast.literal_eval(doc['date_keys'])
                    else:
                        dkey = []
                if 'api_key' in doc:
                    api_key=doc['api_key']
                else:
                    api_key=None
                db = doc['database']
                if not self.mongo.check_auth(db,user,api_key):#getdatabase(username=user):
                    return json.dumps({'status':False,'description':'Error: User does not have permission to alter Data Commons '}, default = handler) 
                #if not db in self.mongo.getdatabase(username=user):
                #    return json.dumps({'status':False,'description':'Error: User does not have permission to alter Data Commons '}, default = handler)    
                if 'collection' in doc:
                    col = doc['collection']
                else:
                    col='data'
                #doc.pop('database')
                return json.dumps({'status':True,'_id':self.mongo.save(db,col,data,dkey)}, default = handler)
            except Exception as inst:
                raise inst #return str(inst)
        else:
            return 'Error: Save only accepts posts'
    @cherrypy.expose
    @mimetype('application/json')
    def dropCommons(self,commons_name):
        try:
            if cherrypy.request.login:
                user = cherrypy.request.login
            else:
                raise
        except:
            return json.dumps([{'status':False,'description':'Error returning User Information'}], default = handler)
        dump_out=self.mongo.dropCommons(commons_name,user)
        return json.dumps(dump_out, default = handler)
    @cherrypy.expose
    @mimetype('application/json')
    def newCommons(self,commons_name):
        try:
            if cherrypy.request.login:
                user = cherrypy.request.login
            else:
                raise
        except:
            return json.dumps([{'status':False,'description':'Error returning User Information'}], default = handler)
        dump_out=self.mongo.newCommons(commons_name,user)
        return json.dumps(dump_out, default = handler)
    @cherrypy.expose
    @mimetype('application/json')
    def setPublic(self,commons_name,auth='r'):
        try:
            if cherrypy.request.login:
                user = cherrypy.request.login
            else:
                user = "guest"
        except:
            user = "guest"
        if auth in ['n','r','rw']:
            return json.dumps(self.mongo.setPublic(commons_name,user,auth), default = handler)
        else:
            return json.dumps([{'status':False,'description':'Auth must be either r or rw'}], default = handler)
    @cherrypy.expose
    @mimetype('application/json')
    @cherrypy.tools.gzip()
    def db_find(self, db=None, col=None, query=None, callback=None, showids=None, date=None, outtype=None, **kwargs):
        """ 
        Wrapper for underlying pymongo access
        """
        try:
            if cherrypy.request.login:
                user = cherrypy.request.login
            else:
                user = "guest"
        except:
            user = "guest"
        #return str(user)
        res= self.mongo.getdatabase(username=user)
        res.sort()
        pub_res= self.mongo.getpublic()
        pub_res.sort()
        if not db:
            rtn = {'My Data Commons':res, 'Public Data Commons':pub_res}
            return json.dumps(rtn , default = handler, sort_keys=True, indent=4)
        if db in res or db in pub_res:
            return self.getdata.find(db, col, query, callback, showids, date)
        else:
            return json.dumps([{'status':False,'description':'User dos not have permissions to view Data Commons'}], default = handler)
    @cherrypy.expose
    @mimetype('application/json')
    @cherrypy.tools.gzip()
    def distinct(self, db=None, col=None, distinct_key=None, query=None, callback=None, **kwargs):
        try:
            if cherrypy.request.login:
                user = cherrypy.request.login
            else:
                user = "guest"
        except:
            user = "guest"
        #return str(user)
        res= self.mongo.getdatabase(username=user)
        res.sort()
        pub_res= self.mongo.getpublic()
        pub_res.sort()
        #res= self.mongo.getdatabase(username=user)
        #res.sort()
        if not db:
            rtn = {'My Data Commons':res, 'Public Data Commons':pub_res}
            return json.dumps(rtn , default = handler, sort_keys=True, indent=4)
            #return json.dumps(res , default = handler)
        if db in res or db in pub_res:
            return self.getdata.distinct(db,col,distinct_key,query,callback)
        else:
            return json.dumps([{'status':False,'description':'User dos not have permissions to view Data Commons'}], default = handler)
    @cherrypy.expose
    @mimetype('application/json')
    @cherrypy.tools.gzip()
    def group_by(self, db=None, col=None,key=None,variable=None, query=None,callback=None, outtype=None, **kwargs):
        """ 
        Wrapper for underlying pymongo access
        """
        try:
            if cherrypy.request.login:
                user = cherrypy.request.login
            else:
                user = "guest"
        except:
            user = "guest"
        res= self.mongo.getdatabase(username=user)
        res.sort()
        pub_res= self.mongo.getpublic()
        pub_res.sort()
        if not db:
            rtn = {'My Data Commons':res, 'Public Data Commons':pub_res}
            return json.dumps(rtn , default = handler, sort_keys=True, indent=4)
        if db in res or db in pub_res:
            return self.getdata.group(db, col, key,variable,query,callback)
        else:
            return json.dumps([{'status':False,'description':'User dos not have permissions to view Data Commons'}], default = handler)
    @cherrypy.expose
    @mimetype('application/json')
    def getIndexes(self,database,collection):
        indx = self.mongo.getIndexes(database,collection)
        #cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps([indx], default = handler, sort_keys=True, indent=4)
        #pass#self.mongo

cherrypy.tree.mount(Root())
application = cherrypy.tree

if __name__ == '__main__':
    cherrypy.engine.start()
    cherrypy.engine.block()

