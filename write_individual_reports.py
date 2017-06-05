import os
import sys
file_dir = os.getcwd()
sys.path.append(file_dir)

doGeospatial = True

from reporting import *

DATApath = r'C:\Users\ucqba01\Documents\Local Data\Round 6'
GISpath = r'GIS'

# get a list of the database files in the reporting directory. non-zero is a fail-safe measure
allDatabases = [f for f in os.listdir(DATApath) if '.db' in f and os.stat(DATApath + '\\' + f).st_size > 0]
print('databases:',allDatabases)
# load shapefiles

doGeospatial = True
if doGeospatial:
    wgrid = gpd.read_file(os.path.join(GISpath,"wind_grid27700.shp"))
    zones = gpd.read_file(os.path.join(GISpath,"zones_27700.shp"))
    ukrez = gpd.read_file(os.path.join(GISpath,"ukrez.shp"))
    wgrid_rez_geom = wgrid.geometry & ukrez.unary_union
    wgrid_rez = wgrid
    wgrid_rez.geometry = wgrid_rez_geom
    del wgrid_rez_geom

# overwrite or not. for time saving
overwriteReports = False
overwriteMaps = False

#list of databases to write reports for
reportOnDatabases = ['hR_m_2002_waves400_RPS20_fcost80_newfuelcost.db']
for db in allDatabases:
    if overwriteReports or not os.path.exists(DATApath + '\\' + db[:-3] + '.html'):
        reportOnDatabases.append(db)

print('reporting on:',reportOnDatabases)

for db in reportOnDatabases:
    print('starting on %s' % db)

    # create directory to put graphs in
    reportdir = '\\%s\\' % db[:-3]
    if not os.path.exists(DATApath + reportdir):
        os.makedirs(DATApath + reportdir)

    #establist database connection
    con = sq.connect(DATApath + '\\' + db)

    #list tables in database
    tables = getlist(con)

    graphs = []  # graphs are saved as 'div' text into this list which is then printed to an html file
    images = []  # non-plotly graphs are saved as images and the locations stored in this list which are then added as links in the html file

    # Generation and Capacity Pie Charts
    traces_pie = []  # tools.make_subplots(rows=1,cols=2,subplot_titles=['Annual Generation (MWh)','Capacity (MW)'])

    # generation held in two separate tables
    gen_sum_h = mergeGEN('var_vre_gen_sum_h', 'var_non_vre_gen_sum_h', con)
    print(gen_sum_h.head())
    gen_sum = gen_sum_h.pivot_table(values='value', index='gen', aggfunc='sum')
    print(gen_sum.head())
    # generator capacities held in same table
    gen_cap = get('vre_cap_tot', con).rename(columns={'vre': 'gen', 'value': 'level'}).append(
        get('var_non_vre_cap', con).rename(columns={'non_vre': 'gen'}))

    traces_pie.append(pie_trace(gen_sum.index, gen_sum.value.round(0),
                               {'x': [0.0, 0.45], 'y': [0.0,1.0]}))
    print('gen_sum.index',gen_sum.index)
    print('gen_sum.values.round(0)',gen_sum.values.round(0))
    traces_pie.append(pie_trace(gen_cap[gen_cap['gen'] != 'pgen'].sort_values(by='gen').gen,
                                gen_cap[gen_cap['gen'] != 'pgen'].sort_values(by='gen').level.round(0),
                                {'x': [0.55, 1.0], 'y': [0.0, 1.0]}))
    layout = go.Layout(height=500, title='Generation (left) and Capacity (right)')
    fig_pie = go.Figure(data=traces_pie, layout=layout)
    graphs.append(py.offline.plot(fig_pie, filename=DATApath + reportdir + 'pies.html', output_type='div'))
    py.offline.plot(fig_pie, filename=DATApath + reportdir + 'pies.html', auto_open=False)
    # py.offline.plot(fig_pie,filename='test.html')

    # get capacity factors for generators
    CF = gen_cap
    gen_cap.index = gen_cap['gen']
    CF['generation'] = gen_sum
    CF['CF'] = CF['generation'] / (8760 * CF['level'])

    # get storage capacity from separate storage variable
    store_cap = get('var_store_gen_cap', con)
    store_cap.rename(columns={'s': 'gen'}, inplace=True)
    # append storage to df so that it is plotted just like a generator
    gen_cap = gen_cap.append(store_cap)

    # get the curtailment factors
    curtail = getcurtail(con)

    # get storage generation values
    store_gen_sum = get('store_gen_tot', con).rename(columns={'s': 'gen'})
    gen_sto_sum = gen_sum.reset_index().append(store_gen_sum)

    # aggregate storage generation & demand to hourly national resolution
    store = mergestore(con)
    store_h_long = convertToInt(store, 'h').pivot_table(values='value', index='h', aggfunc='sum')
    store_h = pd.DataFrame()
    store_h['h'] = store_h_long.index
    store_h['value'] = store_h_long.values
    store_h['gen'] = 'Storage'
    storeGenActivity = generationTimeFrameCount(store_h).reset_index().rename(
        columns={'index': 'time_period', 0: 'generation_count'})
    storeGenActivity['time_period'] = storeGenActivity['time_period'].astype('str')

    # set up figure for 6 bar charts 2 columns, 3 rows
    fig = tools.make_subplots(rows=3, cols=2, print_grid=False, subplot_titles=['Generator Capacities (MW)',
                                                                                'VRE Capacities (MW)',
                                                                                'Operational Capacity Factors (After Curtailment)',
                                                                                'Percentage Curtailment',
                                                                                'Annual Generation',
                                                                                'Frequency of Net Positive Generation Periods from Storage'])
    fig.append_trace(bar_trace(gen_cap, 'gen', 'level'), 1, 1)
    fig.append_trace(bar_trace(get('vre_cap_tot', con), 'vre', 'value'), 1, 2)
    fig.append_trace(bar_trace(CF, 'gen', 'CF'), 2, 1)
    fig.append_trace(bar_trace(curtail, 'vre', 'curtailment_pct'), 2, 2)
    fig.append_trace(bar_trace(gen_sto_sum, 'gen', 'value'), 3, 1)
    fig.append_trace(bar_trace(storeGenActivity, 'time_period', 'generation_count'), 3, 2)

    fig['layout'].update(height=1500)
    py.offline.plot(fig, filename=DATApath + reportdir + 'generators.html', auto_open=False)

    graphs.append(py.offline.plot(fig, filename=DATApath + reportdir + 'generators.html', output_type='div'))

    # note: windoffshore is aggregated at the moment - use parameter not variable

    # graphs.append(barplot(gen_cap,'gen','level','Generator Capacities (MW)',path+reportdir+'gen_capacities.html'))
    ### plot vre capacities
    # graphs.append(barplot(get('vre_cap_tot',con),'vre','value','vre Capacities (MW)',path+reportdir+'vre_capacities.html'))
    ### plot all generator generation hourly
    # graphs.append(seriesbarplot(clean(gen_sum_h,'value'),'h','value','gen','stack','Hourly Generation by Generator Type (MW)',path+reportdir+'generation_hourly.html'))


    ### plot a bar chart of transmission capacity
    graphs.append(seriesbarplot(transload(con), 'route', 'MW', 'trans', 'group', 'Transmission Capacity',
                                DATApath + reportdir + 'transmission_cap.html'))


    ### demand as a line graph on bar plot
    demand_h = convertToInt(get('demand', con), 'h').pivot_table(values='value', index='h', aggfunc='sum')
    dem = pd.DataFrame()
    dem['h'] = demand_h.index
    dem['value'] = demand_h.values
    dem['gen'] = 'Demand'

    # graphs.append(seriesbarline(clean(gen_sum_h.append(dem),'value'),'h','value','gen','Demand','Generation with Demand',path+reportdir+'generation_hourly_demand.html'))

    ### plot a time series of storage generation and demand with zone as series
    # graphs.append(barplot(store_h,'h','value','Storage Demand(-) and Generation(+)',path+reportdir+'generation_storage.html'))

    ### generation bar chart with demand and 'demand with storage' line graphs
    store_dem = pd.merge(dem[['h', 'value']], store_h[['h', 'value']], on='h')
    store_dem['value'] = store_dem['value_x'] - store_dem['value_y']
    del store_dem['value_x']
    del store_dem['value_y']
    store_dem['gen'] = 'Demand with Storage'

    graphs.append(seriesbarline(clean(gen_sum_h.append(dem).append(store_dem), 'value'), 'h', 'value', 'gen',
                                ['Demand', 'Demand with Storage'], 'Generation with Demand and Storage',
                                DATApath + reportdir + 'generation__storage_hourly_demand2.html'))
    ### percentage fill plotted against capacity factor
    vrecapr = vre_pct(get('vre_cap_r', con), get('vre_CF_r', con),con)

    fig2 = tools.make_subplots(rows=2, cols=3, print_grid=False, subplot_titles=(vrecapr.vre.unique().tolist()))
    fig2['layout'].update(title='Installation Percentages against Available Cf. Bubble size by available area')
    i = 0
    for v in vrecapr.vre.unique():
        bubtrace = bubbleplot_trace(vrecapr, 'vre', v, 'CF', 'pct_installed', 'total_area')
        c = [1, 2, 3, 1, 2, 3]
        fig2.append_trace(bubtrace, 1 + i // 3, c[i])
        i = i + 1
    for yax in [l for l in fig2['layout'] if 'yaxis' in l]:
        fig2['layout'][yax].update(range=[0, 100])
    graphs.append(py.offline.plot(fig2, filename=DATApath + reportdir + 'pctareas_CF.html', output_type='div'))

    ### percentage fill plotted against lcoe
    vrecapr = pd.merge(vrecapr,
                       get('capex_vre_r', con).rename(columns={'value': 'total_capex'}))  # add total capex column
    vrecapr = pd.merge(vrecapr, get('generator_varom', con).rename(columns={'g': 'vre', 'value': 'varom'}),
                       how='left').fillna(0)  # add varom /MWh column. left join because there is no solar varom
    vrecapr['potential_lcoe(£/MWh)'] = ((vrecapr.total_capex / (
    8760 * vrecapr.CF * vrecapr.value)) + vrecapr.varom) * 1000  # potential LCOE if there was no curtailment
    vrecapr = pd.merge(vrecapr, get('var_vre_gen_sum_z', con).rename(
        columns={'value': 'actual_generation'}))  # add in actual generation (model output)
    vrecapr['actual_lcoe(£/MWh)'] = ((
                                     vrecapr.total_capex / vrecapr.actual_generation) + vrecapr.varom) * 1000  # total_capex/actual_generation gives £/MWh from capex, then add varom
    vrecapr['potential_generation'] = vrecapr.total_area * 8760 * vrecapr.CF
    demand_tot = dem.value.sum()
    vrecapr['potential_generation_ratio'] = vrecapr['potential_generation'] / demand_tot
    vrecapr['actual_generation_ratio'] = vrecapr['actual_generation'] / demand_tot
    vrecapr['potential_generation_TWh'] = vrecapr['potential_generation'] * 10 ** -6
    vrecapr['actual_generation_TWh'] = vrecapr['actual_generation'] * 10 ** -6

    graphs.append(
        plotSupplyCurves(vrecapr[vrecapr.value > 0.01], 'actual_generation_TWh', 'potential_lcoe(£/MWh)', 'vre',
                         'Resultant Supply Curves', DATApath + reportdir + 'resultant_supply.html'))
    graphs.append(
        plotSupplyCurves(vrecapr, 'potential_generation_TWh', 'potential_lcoe(£/MWh)', 'vre', 'Input Supply Curves',
                         DATApath + reportdir + 'potential_supply.html'))

    graphs.append(vreRegionalCapacityLcoePlot(vrecapr, 'Installed VRE by LCOE'))

    fig3 = tools.make_subplots(rows=2, cols=3, print_grid=False, subplot_titles=(vrecapr.vre.unique().tolist()))
    fig3['layout'].update(title='Installation Percentages against Potential LCOE. Bubble size by available area')
    i = 0
    for v in vrecapr.vre.unique():
        bubtrace = bubbleplot_trace(vrecapr, 'vre', v, 'potential_lcoe(£/MWh)', 'pct_installed', 'total_area')
        c = [1, 2, 3, 1, 2, 3]
        fig3.append_trace(bubtrace, 1 + i // 3, c[i])
        i = i + 1
    for yax in [l for l in fig3['layout'] if 'yaxis' in l]:
        fig3['layout'][yax].update(range=[0, 100])

    graphs.append(py.offline.plot(fig3, filename=DATApath + reportdir + 'pctareas_potential_LCOE.html', output_type='div'))

    fig4 = tools.make_subplots(rows=2, cols=3, print_grid=False, subplot_titles=(vrecapr.vre.unique().tolist()))
    fig4['layout'].update(title='Installation Percentages against Resultant LCOE. Bubble size by available area')
    i = 0
    for v in vrecapr.vre.unique():
        bubtrace = bubbleplot_trace(vrecapr, 'vre', v, 'actual_lcoe(£/MWh)', 'pct_installed', 'total_area')
        c = [1, 2, 3, 1, 2, 3]
        fig4.append_trace(bubtrace, 1 + i // 3, c[i])
        i = i + 1
    for yax in [l for l in fig4['layout'] if 'yaxis' in l]:
        fig4['layout'][yax].update(range=[0, 100])

    graphs.append(py.offline.plot(fig4, filename=DATApath + reportdir + 'pctareas_potential_LCOE.html', output_type='div'))

    # Correlation
    if not os.path.exists(DATApath + reportdir + 'vreCorrelation.png'):
        vreGenAfterCurtail = get('var_vre_gen_sum_h', con).pivot(columns='vre', values='value', index='h')
        vregenCorr = vreGenAfterCurtail.corr()
        corrAx = plt.axes()
        correlationPlot = sns.heatmap(vregenCorr, annot=True, ax=corrAx)
        corrAx.set_title('National VRE Generation Correlation (on hourly time series)')
        corrAx.set_xlabel('')
        corrAx.set_ylabel('')
        correlationPlot.figure.savefig(DATApath + reportdir + 'vreCorrelation.png')
        plt.close()
    images.append(DATApath + reportdir + 'vreCorrelation.png')

    '''
    vreCFRaw = get('vre_gen',con)
    vre_cap_r = get('vre_cap_r',con)
    vre_cap_r = vre_cap_r[vre_cap_r.value>0.01]
    vreGenBeforeCurtail_r =pd.merge(vreCFRaw.rename(columns={'value':'CF'}),vre_cap_r.rename(columns={'value':'capacity'}),on=['vre','r'])
    vreGenBeforeCurtail_r['generation']=vreGenBeforeCurtail_r['CF']*vreGenBeforeCurtail_r['capacity']
    vreGenBeforeCurtail = dropto(['vre','h'],vreGenBeforeCurtail_r[['vre','h','r','generation']])
    vreGenBeforeCurtail = vreGenBeforeCurtail.pivot(columns='vre',index='h',values='generation')
    sns.heatmap(vreGenBeforeCurtail)
    '''
    ### Geospatial reporting. Using geopandas to produce images which are then read by the html file
    if doGeospatial:
        capmax = get('vre_cap_r', con).pivot(values='value', columns='vre', index='r').max()
        colour = 'viridis'
        scale = 10000
        vre_cap_r = get('vre_cap_r', con)

        for vre in vre_cap_r.vre.unique():
            mapfile = DATApath + reportdir + vre + '.png'
            if overwriteMaps or not os.path.exists(
                    mapfile):  # checks to see if the map already exists or if overwrite is set to True
                print('writing map')
                images.append(
                    vreplot(vre_cap_r, vre, 'value', colour, vre_cap_r[vre_cap_r.vre == vre].value.max(), zones, wgrid_rez, vre, mapfile))
            else:
                images.append(mapfile)
                print('map already exists')

    lcoe = get('scalars', con).iloc[6].value.round(3) * 1000

    ### write graphs into a single html report with lcoe appended to the title
    html = mkreport(graphs, image_html(images), db[:-3] + ' - sys-lcoe £%s /MWh' % lcoe,
                    DATApath + '\\' + db[:-3] + '.html')

    # close db connection
    con.close()
