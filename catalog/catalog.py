import cherrypy
import json, os #, math,commands,ast
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
        if not db:
            res= self.mongo.getdatabase(username=user)
            res.sort()
            nameSpace = dict(database=res,baseurl=cherrypy.url('/')[:-1],FName=fname,user=user)        
            t = Template(file = templatepath + '/database.tmpl', searchList=[nameSpace])
            return t.respond()
        #col1='data'
        #if not col:
        #    res= self.mongo.getcollections(db)
        #    res.sort()
        #    nameSpace = dict(database=db,collection=res,baseurl=cherrypy.url('/')[:-1],FName=fname,user=user)
        #    t = Template(file = templatepath + '/collection.tmpl', searchList=[nameSpace])
        #    return t.respond()
        #if record == 'json':
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
        #else:
        #    skip=(int(record)-1)
        #    prev=int(record)-1
        #    if prev < 1: 
        #        prev=1
        #    next=int(record)+1
        #    limit=1
        #    serialized=''
        #    cur = self.mongo.getDoc(db,col,query,skip,limit)#.skip(int(record)-1).limit(1)
        info = self.mongo.getInfo(db,col,query,skip,limit)
        nameSpace = dict(database=db,collection=col,data=cur,baseurl=cherrypy.url('/')[:-1],
            serial=serialized,FName=fname,prev=prev,next=next,rec_info=info,user=user,serialmeta=serial_meta,seriallocation=serial_location)
        t = Template(file = templatepath + '/data.tmpl', searchList=[nameSpace])
        return t.respond()
    @cherrypy.expose
    def save(self, **kwrgs):
        if cherrypy.request.method =="POST":
            try:
                doc=cherrypy.request.params
                print str(doc)
                db= doc['database']
                col=doc['collection']
                doc.pop('database')
                doc.pop('collection')
                return self.mongo.save(db,col,doc)#'commons',cherrypy.request.params)
            except Exception as inst:
                return str(inst)
        else:
            return 'Error: Save only accepts posts'
    @cherrypy.expose
    @mimetype('application/json')
    def getIndexes(self,database,collection):
        indx = self.mongo.getIndexes(database,collection)
        #cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps([indx], default = handler, sort_keys=True, indent=4)
        #pass#self.mongo
    @cherrypy.expose
    @mimetype('application/json')
    def get_user(self,url='http://production.cybercommons.org/accounts/userdata/',cookies=None):
        #import urllib2
        #return cherrypy.request.cookie
        #return cherrypy.url() #path='', qs='', script_name=None, base=None, relative=None)
        cj=self.create_cookiejar(cherrypy.request,cherrypy.url())

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
        user=urllib2.urlopen('http://test.cybercommons.org/accounts/userdata/')
        #if not cookies:
        #    cookies=cherrypy.request.cookie
        #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),urllib2.HTTPHandler())
        #rest=''
        #for name in cookies.keys():
        #    cookie= "%s=%s" % (name, cookies[name].value)
        #    rest=rest + cookie
        #    opener.addheaders.append(('Cookie', cookie))
        #return rest + ' ' + str(opener.open(url))
        result =  user.read()  + str(len(cj))#opener.open(urllib2.Request(url))
        for cok in cj:
            result = result + str(cok) + '=' + cok.value

        return result
    def create_cookiejar(self,cherrypy_request,browser_url):
        "Returns a cookielib.CookieJar based on cookies found in cherrypy.request"

        req = cherrypy_request
        cookiejar = cookielib.CookieJar()
        # fake request to make cookielib happy
        fake_req = FakeRequest(req,browser_url)
        for cookie_name, morsel in req.cookie.items():#req.simple_cookie.items():
            std_attr = {}
            # copy attributes that have values
            for attr in morsel.keys():
                if morsel[attr]:
                    std_attr[attr]=morsel[attr]
            tup = (cookie_name, morsel.value, std_attr, {})
            new_cookie = cookiejar._cookie_from_cookie_tuple(tup, fake_req)

            cookiejar.set_cookie(new_cookie)

        return cookiejar
class FakeRequest(object):
    """A request object that pretends it is a urlib2.Request.

    Not a full implementation, but enough to get by.
    """

    def __init__(self, cherrypy_request,browser_url):
        self.req = cherrypy_request
        self.url = browser_url
    def get_full_url(self):
        return self.url

    def get_host(self):
        return self.req.headers['Host']

    def get_type(self):
        return self.req.scheme

    def is_unverifiable(self):
        # Assuming everything has been verified
        return False

    def get_origin_req_host(self):
        # Again, this is more of a client function, so punting
        return self.req.headers['Host']
cherrypy.tree.mount(Root())
application = cherrypy.tree

if __name__ == '__main__':
    cherrypy.engine.start()
    cherrypy.engine.block()
