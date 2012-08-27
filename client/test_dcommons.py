import datacommons
import ConfigParser, os,datetime

#Retrieve Cybercommons Username and Pasword
cfgfile = os.path.join(os.path.expanduser('~'), '.cybercom')
config= ConfigParser.RawConfigParser()
config.read(cfgfile)
username = config.get('user','username')
password = config.get('user','password')

#Set new Commons Name. Must be unique across all users. Need to fix!
commons_name = username + '_test6'

#initialize Data Commons Toolkit

dcommons = datacommons.toolkit(username,password)

#Drop Data Commons

print dcommons.dropCommons(commons_name)

#Query existing Data Commons

records= dcommons.get_data('EOMF_Products',{'spec':{'Name':'MOD09A1.A2000289.h24v12.005.2008205235853.aerosolmask.tif'}},showids=False,col='data')
print records
#records= dd.get_data('EOMF_Products',{},showids=False,col='data') #Returns all
#print records
#print 'shit'
#Create Data Commons

print dcommons.createCommons(commons_name)
print dcommons.setPublic(commons_name,auth='r')
for doc in records:
    #example to change list of dictionary to single dictionary
    #print doc
    data = {}
    for d in doc['data']:
        data.update(d)
    doc['data']=data
    #example using date
    doc['input_date'] = datetime.datetime.now()
    ##print doc
    #save requires commons name, document and a list of date keys
    #print dcommons.save(commons_name,doc)
    print dcommons.save(commons_name ,doc,['input_date'])#,collection='Location')

