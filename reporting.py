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

legNames = {'Solar':'Solar',
            'Windonshore':'Onshore Wind',
            'Windoffshore_Shallow':'Shallow Offshore',
            'Windoffshore_Mid':'Mid Depth Offshore',
            'Windoffshore_Floating':'Floating Offshore',
            'NaturalgasOCGTnew':'Natural Gas OCGT'}

# list of tables
def getList(con):
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tables = cursor.fetchall()
    tables = [x[0] for x in tables]
    return tables