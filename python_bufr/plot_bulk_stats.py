import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import process_satwnds_dependencies
import bulk_stats_dependencies
outDict={
         'NC005071/CLAT'       : 'latitude',
         'NC005071/CLON'       : 'longitude',
         'NC005071/PRLC'     : 'pressure',
         'NC005071/WSPD'        : 'windSpeed',
         'NC005071/WDIR'        : 'windDirection',
         'NC005071/YEAR'        : 'year',
         'NC005071/MNTH'        : 'month',
         'NC005071/DAYS'        : 'day',
         'NC005071/HOUR'        : 'hour',
         'NC005071/MINU'        : 'minute'#,
         #'PREQCVARIABLE'        : 'qualityIndicator'   # special case, unpacked from multi-dimensional array, handled through pre-QC variables and passed through, key is a dummy
        }
bufrFileName='./NC005071'
amvDict = process_satwnds_dependencies.process_NC005071(bufrFileName, outDict)

# stage data for plotting
lat = amvDict['latitude']
lon = amvDict['longitude']  # needs to be fixed to 0 to 360 format
fix = np.where(lon < 0.)
lon[fix] = lon[fix] + 360.
pre = amvDict['pressure']
wspd = amvDict['windSpeed']
wdir = amvDict['windDirection'].astype('float')  # needs to be asserted as float
#qi = amvDict['qualityIndicator']
qi = np.nan * np.ones(np.shape(lat))
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
obDensityFig.savefig('NC005071_density.png', bbox_inches='tight', facecolor='white')
obHistLatLonPreFig.savefig('NC005071_latlonpre.png', bbox_inches='tight', facecolor='white')
obHistSpdDirQIFig.savefig('NC005071_spddirqi.png', bbox_inches='tight', facecolor='white')

