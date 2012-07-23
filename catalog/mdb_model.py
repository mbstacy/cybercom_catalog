from pymongo import ReplicaSetConnection, Connection, ReadPreference
from bson.objectid import ObjectId
#from pymongo.objectid import ObjectId
import ConfigParser,os,ast,pymongo


class mongo_catalog():

    def __init__(self,configfile='.cybercom',appdir='~'):
        cfgfile = os.path.join(os.path.expanduser(appdir), configfile)
        config= ConfigParser.RawConfigParser()
        config.read(cfgfile)
        self.dbcon = Connection(config.get('database','host'))
        self.dbcon.read_preference = ReadPreference.SECONDARY
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
        return "Save turned off while no auth in place for MongoDB"
        if document['_id']:
            document['_id']=ObjectId(document['_id'])
        return self.dbcon[db][collection].save(document)
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
    def newCommons(self,commons, owner):
        #need to check for already existing Names
        try:
            userid=int(owner)
        except:
            userid=-999
        user=self.dbcon.cybercom_auth.user.find({'$or':[{'_id':userid},{'user':owner}]})
        if not user.count()==1:
            return False
        usr=user[0]
        res = self.dbcon.cybercom_auth.commons_priviledges.find({'$or':[{'_id':userid},{'user':owner}]})
        if not res.count()==1:
            return False
        rec= res[0]
        rec['commons'].append({ "database" : commons, "permission" : "rwa" } )
        self.dbcon.cybercom_auth.commons_priviledges.save(rec)
        
        return True
        
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
                
