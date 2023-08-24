import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import process_satwnds_dependencies
import bulk_stats_dependencies
outDict={
         'NC005069/CLATH'       : 'latitude',
         'NC005069/CLONH'       : 'longitude',
         'NC005069/PRLC[1]'     : 'pressure',
         'NC005069/WSPD'        : 'windSpeed',
         'NC005069/WDIR'        : 'windDirection',
         'NC005069/YEAR'        : 'year',
         'NC005069/MNTH'        : 'month',
         'NC005069/DAYS'        : 'day',
         'NC005069/HOUR'        : 'hour',
         'NC005069/MINU'        : 'minute',
         'PREQCVARIABLE'        : 'qualityIndicator'   # special case, unpacked from multi-dimensional array, handled through pre-QC variables and passed through, key is a dummy
        }
bufrFileName='./NC005069'
amvDict = process_satwnds_dependencies.process_NC005069(bufrFileName, outDict)

# stage data for plotting
lat = amvDict['latitude']
lon = amvDict['longitude']  # needs to be fixed to 0 to 360 format
fix = np.where(lon < 0.)
lon[fix] = lon[fix] + 360.
pre = amvDict['pressure']
wspd = amvDict['windSpeed']
wdir = amvDict['windDirection'].astype('float')  # needs to be asserted as float
qi = amvDict['qualityIndicator']
obDensityFig, obHistLatLonPreFig, obHistSpdDirQIFig = bulk_stats_dependencies.stage_scorecard( ob_lat=lat,
                                                                                               ob_lon=lon,
                                                                                               ob_pre=pre,
                                                                                               ob_spd=wspd,
                                                                                               ob_dir=wdir,
                                                                                               ob_qi=qi,
                                                                                               qi_thresh=90. )
# report ob-types
typ = amvDict['observationType']
for t in np.unique(typ):
    n = np.size(np.where(typ==t))
    print('{:d} observations of Type={:d}'.format(n, t))
obDensityFig.savefig('NC005069_density.png', bbox_inches='tight', facecolor='white')
obHistLatLonPreFig.savefig('NC005069_latlonpre.png', bbox_inches='tight', facecolor='white')
obHistSpdDirQIFig.savefig('NC005069_spddirqi.png', bbox_inches='tight', facecolor='white')

