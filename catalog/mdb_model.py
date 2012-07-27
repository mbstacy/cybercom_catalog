from pymongo import ReplicaSetConnection, Connection, ReadPreference
from bson.objectid import ObjectId
#from pymongo.objectid import ObjectId
import ConfigParser,os,ast,pymongo
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
    def getdatabase(self,username="guest", **kwargs):
        #returns authorized databases
        return self.user_authDB(username)
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
    def save(self,db,collection,document):
        #return "Save turned off while no auth in place for MongoDB"
        if '_id' in document:
            document['_id']=ObjectId(document['_id'])
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
    def dropCommons(self,commons,owner):
        try:
            userid=int(owner)
        except:
            userid=-999
        user=self.dbcon.cybercom_auth.user.find({'$or':[{'_id':userid},{'user':owner}]})
        if not user.count()==1:
            return [{'status':False,'description':'Error:User not in Catalog Users'}]
        res = self.dbcon.cybercom_auth.commons_priviledges.find({'$or':[{'_id':userid},{'user':owner}]})
        if not res.count()==1:
            return [{'status':False,'description':'User does not have permission to drop data commons.'}]
        else:
            rec= res[0]
        for d in rec['commons']:
            if d["database"]==commons and d["permission"]=="rwa":
                self.dbcon.drop_database(commons)
                return [{'status':True,'description':'Data Commons Dropped'}]
        return [{'status':False,'description':'User does not have permission or Data Commons does not exist.'}] 
    def newCommons(self,commons,owner):
        #need to check for already existing Names
        if commons in self.dbcon.database_names():
            return [{'status':False,'description':'Duplicate Commons Name'}]
        try:
            userid=int(owner)
        except:
            userid=-999
        user=self.dbcon.cybercom_auth.user.find({'$or':[{'_id':userid},{'user':owner}]})
        if not user.count()==1:
            return [{'status':False,'description':'Error:User not in Catalog Users'}] 
        usr=user[0]
        res = self.dbcon.cybercom_auth.commons_priviledges.find({'$or':[{'_id':userid},{'user':owner}]})
        if not res.count()==1:
            rec = {"_id":userid,"user":owner,"commons":[]}
        else:
            rec= res[0]
        for d in rec['commons']:
            if d["database"]==commons:  
                return [{'status':False,'description':'Commons Name must be unique'}] 
        rec['commons'].append({ "database" : commons, "permission" : "rwa" } )
        self.dbcon.cybercom_auth.commons_priviledges.save(rec)
        
        return [{'status':True,'description':'Data Commons created succesfully.'}]
    def user_authDB(self,username):
        '''returns list of databases that username has authority to see'''
        try:
            userid=int(username)
        except:
            userid=-999
        output=[]
        dbs = self.dbcon.cybercom_auth.commons_priviledges.find({'$or':[{'_id':userid},{'user':username}]},['commons'])
        if dbs.count()== 0:
            return output
        for db in dbs[0]['commons']:
            output.append(db['database'])
        return output
                
