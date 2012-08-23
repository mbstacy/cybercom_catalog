from pymongo import ReplicaSetConnection, Connection, ReadPreference
from bson.objectid import ObjectId
#from pymongo.objectid import ObjectId
import ConfigParser,os,ast,pymongo
import iso8601
cybercomdir = '/opt/cybercom'
cybercomfile='cybercom.conf'
class mongo_catalog():

    def __init__(self,configfile=cybercomfile,appdir=cybercomdir):
        cfgfile = os.path.join(os.path.expanduser(appdir), configfile)
        config= ConfigParser.RawConfigParser()
        config.read(cfgfile)
        self.dbcon = Connection(config.get('database','host'))
        self.dbcon.read_preference = ReadPreference.SECONDARY
        self.dbwrite = Connection(config.get('database','host'))
        self.dbwrite.read_preference = ReadPreference.PRIMARY
    def getdatabase(self,username="guest",multiple=False, **kwargs):
        if multiple:
            priv =[]
            pub=[]
            cpub=[]
            lapub=[]
            res =self.user_authDB(username)
            pub_rec=self.check_auth('public')
            for d in pub_rec['commons']:
                lapub.append(d['database'])
                if d['database'] in res:
                    temp = d
                    if temp['permission']=='r':
                        temp['permission']='Read'
                    elif temp['permission']=='rw':
                        temp['permission']='Read/Write'
                    pub.append(temp)
                else:
                    temp = d
                    if temp['permission']=='r':
                        temp['permission']='Read'
                    elif temp['permission']=='rw':
                        temp['permission']='Read/Write'
                    cpub.append(temp)
            return res,pub,cpub,lapub
        #returns authorized databases
        return self.user_authDB(username)
    def getpublic(self,auth='r'):
        pdb=[]
        pub_rec=self.check_auth('public')
        for db in pub_rec['commons']:
            if auth=='rw':
                if db['permission']=='rw':
                    pdb.append(db['database'])
            elif auth == 'r':
                pdb.append(db['database'])
        return pdb        
    def getcollections(self,database):
        #returns collections associated with database 
        return self.dbcon[database].collection_names()
    def getInfo(self,db,collection,query=None,skip=0,limit=0):
        #get page information for query
        info = {}
        if query:
            query = ast.literal_eval(query)
            info['totalRecords']=self.dbcon[db][collection].find(**query).count()
        else:
            info['totalRecords']=self.dbcon[db][collection].find().count()
        if info['totalRecords'] > skip + limit:
            info['startRecord']=skip + 1
            info['endRecord']=skip + limit
        else:
            info['startRecord']=skip + 1
            info['endRecord']=info['totalRecords']
        info['totalCollection']=self.dbcon[db][collection].find().count()
        return info
    def getDoc(self,db,collection,query=None,skip=0,limit=0):
        #returns data in monogDB cursor
        if query:
            query = ast.literal_eval(query)
            cur = self.dbcon[db][collection].find(**query).skip(skip).limit(limit)
        else:
            cur = self.dbcon[db][collection].find().skip(skip).limit(limit).sort([('_id',1)])
        return cur         
    def save(self,db,collection,document,date_key):
        #return "Save turned off while no auth in place for MongoDB"
        if '_id' in document:
            document['_id']=ObjectId(document['_id'])
        for key in date_key:
            document[key]=iso8601.parse_date(document[key]) 
        #return str(db) + '\n'+ str(collection) + '\n' + str(document)
        return self.dbwrite[db][collection].save(document)
    def getkeys(self,database,collection,popID=True):
        #Returns Information regarding keys from database and collection
        col=database + "." + collection  
        cur = self.dbcon['mongoSchema'][col].find({'value.type':{'$nin':['function','object']}})
        cur1= self.dbcon['mongoSchema'][col].find({'value.type':{'$nin':['function']}})
        out=[]
        for row in cur:
            if not (row['_id']['key']=='_id' and popID):
                out.append(row['_id']['key'])
        cols=[]
        for row in cur1:
            if not (row['_id']['key']=='_id' and popID):
                cols.append(row['_id']['key'])
        out.sort()
        cols.sort()
        return out,cols
    def getIndexes(self,database,collection):
        #Resturns Index information for database and collection    
        return self.dbcon[database][collection].index_information()
    def getID_timestamp(self,id,type='iso_string'):
        #returns generated document timestamp from ObjectID
        if type == 'iso_string':
            try:
                return str(ObjectId(id).generation_time)
            except:
                return str(id.generation_time)
    def setPublic(self,commons,user,auth):
        setdesc={'r':'Read','rw':'Read/Write','n':'off'}
        rec = self.check_auth(user)
        for d in rec['commons']:
            if d["database"]==commons and d["permission"]=="rwa":
                pub_rec=self.check_auth('public')
                if auth =='n': #revoke==True or revoke == 'True' or revoke == 'true':
                    for d in pub_rec['commons']:
                        if d["database"]==commons:
                            self.del_Commons(d,pub_rec)
                            desc= 'Data Commons: %s  Public Access Status: off' % (commons)
                            return [{'status':True,'description':desc}]
                    desc= 'Data Commons: %s - Public Access Status: off' % (commons)
                    return [{'status':True,'description':desc}]
                for d in pub_rec['commons']:
                    if d["database"]==commons:
                        self.del_Commons(d,pub_rec)
                        pub_rec['commons'].append({ "database" : commons, "permission" : auth } )
                        self.dbwrite.cybercom_auth.commons_priviledges.save(pub_rec)
                        desc= 'Data Commons: %s  Public Access Status: %s Permissions' % (commons,setdesc[auth])
                        return [{'status':True,'description':desc}]
                pub_rec['commons'].append({ "database" : commons, "permission" : auth } )
                self.dbwrite.cybercom_auth.commons_priviledges.save(pub_rec)
                desc= 'Data Commons: %s  Public Access Status: %s Permissions' % (commons,setdesc[auth])
                return [{'status':True,'description':desc}]    
        return [{'status':False,'description':'User does not have permission or data commons does not exist.'}]

    def dropCommons(self,commons,owner):
        rec = self.check_auth(owner) 
        for d in rec['commons']:
            if d["database"]==commons and d["permission"]=="rwa":
                self.dbcon.drop_database(commons)
                return self.del_Commons(d,rec)
                #return [{'status':True,'description':'Data Commons Dropped'}]
        return [{'status':False,'description':'User does not have permission or Data Commons does not exist.'}] 
    def newCommons(self,commons,owner):
        #need to check for already existing Names
        if commons in self.dbcon.database_names():
            return [{'status':False,'description':'Data Commons Name must be unique.'}]
        rec = self.check_auth(owner)
        for d in rec['commons']:
            if d["database"]==commons:  
                return [{'status':False,'description':'Data Commons Name must be unique.'}] 
        rec['commons'].append({ "database" : commons, "permission" : "rwa" } )
        self.dbwrite.cybercom_auth.commons_priviledges.save(rec)
        
        return [{'status':True,'description':'Data Commons created succesfully.'}]
    def del_Commons(self,item,doc):
        try:
            doc['commons'].remove(item)
            self.dbwrite.cybercom_auth.commons_priviledges.save(doc)
            return [{'status':True,'description':'Data Commons Dropped'}]
        except:
            return [{'status':False,'description':'Error deleting Data Commons from cybercom_auth'}]
    def check_auth(self,owner):
        try:
            userid=int(owner)
        except:
            userid=-999
        res = self.dbcon.cybercom_auth.commons_priviledges.find({'$or':[{'_id':userid},{'user':owner}]})
        if not res.count()==1:
            rec = {"_id":userid,"user":owner,"commons":[]}
        else:
            rec= res[0]
        return rec
    def user_authDB(self,username):
        '''returns list of databases that username has authority to see'''
        try:
            userid=int(username)
        except:
            userid=-999
        output=[]
        dbs = self.dbcon.cybercom_auth.commons_priviledges.find({'$or':[{'_id':userid},{'user':username}]},['commons'])
        if dbs.count()== 0:
            if userid==-999:
                user_per={ "_id" : username, "user" : username, "commons" : [ ]}
            else:
                user_per={ "_id" : userid, "user" : username, "commons" : [ ]}
            self.dbwrite.cybercom_auth.commons_priviledges.save(user_per)
            return output
        for db in dbs[0]['commons']:
            output.append(db['database'])
        return output
                
