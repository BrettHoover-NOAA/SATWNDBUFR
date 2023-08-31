import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import process_satwnds_dependencies
import bulk_stats_dependencies

tankNameList = [#'NC005030',
                #'NC005031',
                #'NC005032',
                #'NC005034',
                #'NC005039',
                #'NC005044',
                #'NC005045',
                #'NC005046',
                #'NC005067',
                #'NC005068',
                #'NC005069',
                #'NC005070',
                #'NC005071',
                #'NC005072',  # NC005072 encounters floating-point exceptions in this test data file for some reason 
                'NC005080']#,
                #'NC005081',
                #'NC005091']
for tankName in tankNameList:
    print('processing ' + tankName)
    outDict={
             tankName + '/CLAT'        : 'latitude',
             tankName + '/CLON'        : 'longitude',
             tankName + '/PRLC'        : 'pressure',
             tankName + '/WSPD'        : 'windSpeed',
             tankName + '/WDIR'        : 'windDirection',
             tankName + '/YEAR'        : 'year',
             tankName + '/MNTH'        : 'month',
             tankName + '/DAYS'        : 'day',
             tankName + '/HOUR'        : 'hour',
             tankName + '/MINU'        : 'minute'
            }
#             'PREQCVARIABLE'           : 'qualityIndicator'   # special case, unpacked from multi-dimensional array, handled through pre-QC variables and passed through, key is a dummy
#            }
    bufrFileName='./gdas.t00z.satwnd.tm00.bufr_d'
    amvDict = process_satwnds_dependencies.process_satwnd_tank(tankName, bufrFileName, outDict)
    # stage data for plotting
    lat = amvDict['latitude']
    lon = amvDict['longitude']  # needs to be fixed to 0 to 360 format
    fix = np.where(lon < 0.)
    lon[fix] = lon[fix] + 360.
    pre = amvDict['pressure']
    wspd = amvDict['windSpeed']
    wdir = amvDict['windDirection'].astype('float')  # needs to be asserted as float
    qc = amvDict['preQC']
    # generate scorecard figures
    obDensityFig, obHistLatLonPreFig, obHistSpdDirQCFig = bulk_stats_dependencies.stage_scorecard( ob_lat=lat,
                                                                                                   ob_lon=lon,
                                                                                                   ob_pre=pre,
                                                                                                   ob_spd=wspd,
                                                                                                   ob_dir=wdir,
                                                                                                   ob_qc=qc
                                                                                                 )
    # report ob-types
    typ = amvDict['observationType']
    for t in np.unique(typ):
        n = np.size(np.where(typ==t))
        print('{:d} observations of Type={:d}'.format(n, t))
    # save scorecard figures
    obDensityFig.savefig(tankName + '_density.png', bbox_inches='tight', facecolor='white')
    obHistLatLonPreFig.savefig(tankName + '_latlonpre.png', bbox_inches='tight', facecolor='white')
    obHistSpdDirQCFig.savefig(tankName + '_spddirqc.png', bbox_inches='tight', facecolor='white')
