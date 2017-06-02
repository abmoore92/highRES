import sqlite3 as sq
import pandas as pd
import os
from reporting import *

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

#getMemoryUsage(tableUnique['common'],connections[0])


def makeDataBase(path,filename)
    if not os.path.exists(mainPath+mergePath):
        os.makedirs(mainPath+mergePath)
    conMerged = sq.connect(path+'/'+filename)
    return conMerged

mergeCon = makeDataBase(mainPath+mergePath,'merged.db')


