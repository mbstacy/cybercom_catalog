import cherrypy
import json, os,ast
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
#from convert import *
'''

MongoDB web interface with 

'''
templatepath= os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))

def mimetype(type):
    def decorate(func):
        def wrapper(*args, **kwargs):
            cherrypy.response.headers['Content-Type'] = type
            return func(*args, **kwargs)
        return wrapper
    return decorate


class Root(object):
    def __init__(self,mongoHost='fire.rccc.ou.edu',port=27017,database='cybercom_queue',collection='task_log'):
        self.mongo = mdb_model.mongo_catalog()
    #@cherrypy.expose
    #def index(self):
    #    #cherrypy.InternalRedirect("/data")
    #    cherrypy.HTTPRedirect("/catalog/data/")
    @cherrypy.expose
    def data(self,db=None,col='data',query={},record=1,page=1,nPerpage=100, **kwargs):
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
                doc=cherrypy.request.params
                db= doc['database']
                if not db in self.mongo.getdatabase(username=user):
                    return json.dumps({'status':False,'description':'Error: User does not have permission to alter Data Commons '}, default = handler)    
                if 'collection' in doc:
                    col=doc['collection']
                    #doc.pop('collection')
                else:
                    col='data'
                doc.pop('database')
                data = json.loads(doc['data'])
                try:
                    dkey=ast.literal_eval(doc['date_keys'])
                except Exception as inst:
                    #print inst
                    dkey=[]
                #print type(data), type(dkey), type(doc['date_keys'])
                #print dkey
                return json.dumps({'status':True,'_id':self.mongo.save(db,col,data,dkey)}, default = handler)
            except Exception as inst:
                return str(inst)
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
            return find(db, col, query, callback, showids, date)
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
        if not db:
            return json.dumps(res , default = handler)
        if db in res:
            return distinct(db,col,distinct_key,query,callback)
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
        #return str(user)
        res= self.mongo.getdatabase(username=user)
        res.sort()
        if not db:
            return json.dumps(res , default = handler)
        if db in res:
            return group(db, col, key,variable,query,callback)
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

