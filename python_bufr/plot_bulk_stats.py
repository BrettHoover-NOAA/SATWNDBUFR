import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import process_satwnds_dependencies
import bulk_stats_dependencies
outDict={
         'NC005030/CLATH'       : 'latitude',
         'NC005030/CLONH'       : 'longitude',
         'NC005030/PRLC[1]'     : 'pressure',
         'NC005030/WSPD'        : 'windSpeed',
         'NC005030/WDIR'        : 'windDirection',
         'NC005030/YEAR'        : 'year',
         'NC005030/MNTH'        : 'month',
         'NC005030/DAYS'        : 'day',
         'NC005030/HOUR'        : 'hour',
         'NC005030/MINU'        : 'minu',
         'PREQCVARIABLE'        : 'qualityIndicator'   # special case, unpacked from multi-dimensional array, handled through pre-QC variables and passed through
        }
bufrFileName='./NC005030'
NC005030Dict = process_satwnds_dependencies.process_NC005030(bufrFileName, outDict)

# stage data for plotting
lat = NC005030Dict['latitude']
lon = NC005030Dict['longitude']  # needs to be fixed to 0 to 360 format
fix = np.where(lon < 0.)
lon[fix] = lon[fix] + 360.
pre = NC005030Dict['pressure']
wspd = NC005030Dict['windSpeed']
wdir = NC005030Dict['windDirection'].astype('float')  # needs to be asserted as float
#qi = np.nan * np.ones(np.shape(NC005030Dict['latitude']))  # all NaN, for now
qi = NC005030Dict['qualityIndicator']
obDensityFig, obHistLatLonPreFig, obHistSpdDirQIFig = bulk_stats_dependencies.stage_scorecard( ob_lat=lat,
                                                                                               ob_lon=lon,
                                                                                               ob_pre=pre,
                                                                                               ob_spd=wspd,
                                                                                               ob_dir=wdir,
                                                                                               ob_qi=qi,
                                                                                               qi_thresh=90. )
obDensityFig.savefig('NC005030_density.png', bbox_inches='tight', facecolor='white')
obHistLatLonPreFig.savefig('NC005030_latlonpre.png', bbox_inches='tight', facecolor='white')
obHistSpdDirQIFig.savefig('NC005030_spddirqi.png', bbox_inches='tight', facecolor='white')

