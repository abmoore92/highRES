# -*- coding: utf-8 -*-
"""
Created on Fri Mar 17 14:44:56 2017
create floating cost scale factor dataset based on depths
@author: Andy
C:\Users\Andy\Google Drive\Extended Research\Scripts and Calculations
"""
import pandas as pd 
import geopandas as gpd
import numpy as np

# read in a csv with the regions and their average depths, 
# make a df with the regions and cost scales based on depth
def write_dd3(df,file):
    cols = [c for c in df.columns if c != 'value']
    a = pd.Series(['.'.join([str(y) for y in x if pd.notnull(y)]) for x in df[cols].values.tolist()])
    b = pd.Series([x for x in df['value']])
    dd = pd.DataFrame({'label' : a, 'value' : b})
    dd.to_csv(file,sep=' ',index=False,header=False)    
    return dd

def read_dd(cols,file):
    df = pd.read_csv(file, names = ['code','value'],skiprows=0, sep=' ',engine='python')
    df[cols]=df['code'].apply(lambda x: pd.Series(str(x).split('.')))
    cols.append('value')
    return df[cols]

### Floating Functions

#create a set of scaled costs based on depth
# 0.0003 comes from £300/MW.m 2.51 comes from £2.51m/MW for mid depth turbines in 4coffshore. (70% capex portion of the 3.57 total)
# values to be applied multiplicatively with uktm costs 
def floating_scale(infile):
    f = pd.read_csv(infile) #floating/region depths.csv
    f['value']=(1+f['depth']*0.0003/2.51
    if 'numpy' in f.columns:
        f.rename(columns={'numpy':'r'},inplace=True)
    return f[['r','value']]

def categorise(shpdf,areacol,difcol,difdict):
    df = shpdf[[difcol,'numpy',areacol]]
    df = df[df.RESULT.isin(difdict.keys())]
    df = df.replace(to_replace=difdict)
    df['value'] = df[areacol].round(2)            
    return df[[difcol,'numpy','value']].sort_values(by=difcol)

    
def lookuptable():
    zones_regions = pd.read_excel('GIS/zones-regions.xls')
    zr_lookup = zones_regions[['wind_grid27700.numpy','zones_27700.Name_1']]
    zr_lookup.columns=['numpy','zone']    
    return zr_lookup
    
difdict = {-3:'Windoffshore_Floating',-2:'Windoffshore_Mid',-1:'Windoffshore_Shallow'}
area_high = gpd.read_file('GIS\\areas\\areas_high_0_20_70.shp')
areas_out = categorise(area_high,'area','RESULT',difdict)
print (areas_out.duplicated(['RESULT','numpy']).sum())

lookup = lookuptable()
areas_file = pd.merge(areas_out,lookup,on='numpy')    
areas_file = areas_file[['RESULT','zone','numpy','value']].sort_values(by='RESULT')
write_dd3(areas_file,'offshore_areas_high.dd')


#f_depthcosts = floating_scale('region depths.csv')

#write_dd3(f_depthcosts,'floating_cost_ratio.dd')

### Electrical Functions

# distance in km is input, electrical loss factor is output
# losses are interpolated/extrapolated according to the data from Negra et al
# minimum loss is 0.741% taken from the AC transformer losses
def electrical(d):
    #loss is in percent. values taken from Negra et al
    ACnoncable = 0.741
    data = pd.read_csv('electrical/electrical loss data (Negra).csv')
    mins = data.pivot_table(values = 'Losses (%)',index='Distance /km',columns = 'Technology',aggfunc='min')
    if d < 50:
        loss = ACnoncable + d*(mins['HVAC'][50]-ACnoncable)/50
    elif d < 200:
        ACloss = np.interp(d,mins.index,mins['HVAC'])
        DCloss = np.interp(d,mins.index,mins['HVDC LCC'])
        loss = np.min([ACloss,DCloss])
    else:
        loss = mins['HVDC LCC'][200] + (d-200)*(mins['HVDC LCC'][200]-mins['HVDC LCC'][150])/50
    return (100-loss)/100        

el = np.vectorize(electrical)

# attribute table for wind grid is read and the electrical losses applied to the near_dist parameter
# resultant output is a DataFrame
def electricalgrid():
    distgrid = pd.read_csv('electrical/distance_to_grid.txt')[['numpy','NEAR_DIST','lat','lon']]
    distgrid['Electrical Loss Factor'] = el(distgrid['NEAR_DIST']/1000)
    return distgrid 

# eg. writeelec('test2.dd')
def writeelec(file):    
    from readgams import write_dd
    grid = electricalgrid()
    simpleGrid = grid[['numpy','Electrical Loss Factor']]
    simpleGrid.columns = ['num','value']
    output = write_dd(simpleGrid,file)
    return output


#1-distgrid[distgrid.NEAR_DIST > 0][distgrid.NEAR_DIST < 200000]['Electrical Loss Factor'].describe()