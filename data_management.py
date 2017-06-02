import sqlite3 as sq
import pandas as pd
import os
from reporting import *
import shutil

mainPath   = r'C:\Users\ucqba01\Documents\Local Data\testing databases/'
mergePath = r'\merged'
databases = [f for f in os.listdir(mainPath) if f[-3:] == '.db']
connections = [sq.connect(mainPath+db) for db in databases]
print(databases)

tables = getList(connections[0])
print(tables)

tableUnique = {'common':[],'specific':[]}

for t in tables:
    tableData0 = get(t,connections[0])
    tableData1 = get(t,connections[1])
    if tableData0.equals(tableData1):
        tableUnique['common'].append(t)
    else:
        tableUnique['specific'].append(t)

print('common tables',len(tableUnique['common']))
print('specific tables',len(tableUnique['specific']))

def getMemoryUsage(tableList,con)
    dataUsage = {}
    for t in tableList:
        dataUsage[t] = get(t,con).memory_usage().sum()

def makeDirectory(mainPath,mergePath):
    if not os.path.exists(mainPath+mergePath):
        os.makedirs(mainPath+mergePath)

def replaceString(myString, dict):
    for k in dict.keys():
        myString = myString.replace(k, dict[k])
    return myString


#getMemoryUsage(tableUnique['common'],connections[0])
mergeCon = makeDataBase(mainPath+mergePath,'merged.db')

makeDirectory(mainPath,mergePath)

mergeDataBaseFile = '/merge3.db'

shutil.copy(mainPath+'/'+databases[0],mainPath+mergePath+mergeDataBaseFile)

scenarios = {}
scenarioSettings = pd.DataFrame(columns=['scenario','identifier','value'])

for db in databases:
    scenarios[db] = replaceString(db,{'hR_m_2002_waves':'w','_newfuelcost.db':''})

#this function is very user specific
identifiersDict = {'waves'}

con = sq.connect(mainPath+mergePath+mergeDataBaseFile)


for t in tableUnique['specific']:
    scen=scenarios[databases[0]]
    colCursor = con.execute('select * from %s'%t)
    cursor = con.cursor()
    if 'scenario' not in [col[0] for col in colCursor.description]:
        cursor.execute("ALTER TABLE %s ADD COLUMN scenario string;"%t)
    cursor.execute("UPDATE %s SET scenario='%s'" %(t,scen))
    cursor.execute("""CREATE TABLE 
                        IF NOT EXISTS scenarios (
                        scenario string NOT NULL,
                        identifier string NOT NULL,
                        value string NOT NULL
                        );""")
    scenarioSettings = dbFileSettings(databases[0])
for id in scenarioSettings.keys():
    cursor.execute("INSERT INTO scenarios (scenario,identifier,value) VALUES ('%s','%s','%s');"%(scen,id,scenarioSettings[id]))


