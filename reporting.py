import sqlite3 as sq
import pandas as pd
import os

def get(table,con): 
    return pd.read_sql('select * from '+table,con)

#return scenario settings from reading db file
def dbFileSettings(db):
    settings = {}
    settings['waves'] = int(db.split('waves')[1].split('_')[0])
    settings['fcost'] = int(db.split('fcost')[1].split('_')[0])
    settings['RPS'] = int(db.split('RPS')[1].split('_')[0])
    return settings

def makedbName(dbgeneric,labelDict):
    dbstring = dbgeneric
    for param in labelDict.keys():
        dbstring = dbstring.replace(param,str(labelDict[param]))
    return dbstring
	
