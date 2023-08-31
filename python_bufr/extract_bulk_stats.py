import numpy as np
import process_satwnds_dependencies
from netCDF4 import Dataset

tankNameList = ['NC005030',
                'NC005031',
                'NC005032',
                'NC005034',
                'NC005039',
                'NC005044',
                'NC005045',
                'NC005046',
                'NC005067',
                'NC005068',
                'NC005069',
                'NC005070',
                'NC005071',
                'NC005072',  # NC005072 encounters floating-point exceptions in this test data file for some reason 
                'NC005080',
                'NC005081',
                'NC005091']
# initialize empty arrays
obLat = np.asarray([])
obLon = np.asarray([])
obPre = np.asarray([])
obSpd = np.asarray([])
obDir = np.asarray([])
obYr  = np.asarray([])
obMon = np.asarray([])
obDay = np.asarray([])
obHr  = np.asarray([])
obMin = np.asarray([])
obTyp = np.asarray([])
obPQC = np.asarray([])
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
    bufrFileName='./gdas.t00z.satwnd.tm00.bufr_d'
    # attempt to extract data from tank, exceptions raise warning and do not append tank data
    try:
        amvDict = process_satwnds_dependencies.process_satwnd_tank(tankName, bufrFileName, outDict)
        # append data to master arrays
        obLat = np.append(obLat, amvDict['latitude'])
        obLon = np.append(obLon, amvDict['longitude'])
        obPre = np.append(obPre, amvDict['pressure'])
        obSpd = np.append(obSpd, amvDict['windSpeed'])
        obDir = np.append(obDir, amvDict['windDirection'])
        obYr  = np.append(obYr,  amvDict['year'])
        obMon = np.append(obMon, amvDict['month'])
        obDay = np.append(obDay, amvDict['day'])
        obHr  = np.append(obHr,  amvDict['hour'])
        obMin = np.append(obMin, amvDict['minute'])
        obTyp = np.append(obTyp, amvDict['observationType'])
        obPQC = np.append(obPQC, amvDict['preQC'])
    except:
        print('warning: ' + tankName + ' was not processed due to errors')
# report ob-types and pre-QC
for t in np.unique(obTyp):
    i = np.where(obTyp==t)
    n = np.size(i)
    p = np.size(np.where(obPQC[i]==1.))
    f = np.size(np.where(obPQC[i]==-1.))
    print('{:d} observations of Type={:d} ({:.1f}% pass pre-QC, {:.1f}% fail)'.format( n,
                                                                                       int(t),
                                                                                       100. * float(p)/float(n),
                                                                                       100. * float(f)/float(n)
                                                                                      ))
# save data to netCDF file
nc_out_filename = bufrFileName + '.nc'
nc_out = Dataset( 
                  nc_out_filename  , # Dataset input: Output file name
                  'w'              , # Dataset input: Make file write-able
                  format='NETCDF4' , # Dataset input: Set output format to netCDF4
                )
# Dimensions
ob  = nc_out.createDimension( 
                             'ob' , # nc_out.createDimension input: Dimension name 
                             None    # nc_out.createDimension input: Dimension size limit ("None" == unlimited)
                             )
# Variables
lat = nc_out.createVariable(
                              'lat'       ,
                              'f8'        ,
                              ('ob')
                            )
lon= nc_out.createVariable(
                              'lon'       ,
                              'f8'        ,
                              ('ob')
                            )
pre = nc_out.createVariable(
                              'pre'       ,
                              'f8'        ,
                              ('ob')
                            )
wspd = nc_out.createVariable(
                              'wspd'       ,
                              'f8'        ,
                              ('ob')
                            )
wdir = nc_out.createVariable(
                              'wdir'       ,
                              'f8'        ,
                              ('ob')
                            )
year = nc_out.createVariable(
                              'year'       ,
                              'f8'        ,
                              ('ob')
                            )
mon = nc_out.createVariable(
                              'mon'       ,
                              'f8'        ,
                              ('ob')
                            )
day = nc_out.createVariable(
                              'day'       ,
                              'f8'        ,
                              ('ob')
                            )
hour = nc_out.createVariable(
                              'hour'       ,
                              'f8'        ,
                              ('ob')
                            )
minute = nc_out.createVariable(
                               'minute'       ,
                              'f8'        ,
                              ('ob')
                            )
typ = nc_out.createVariable(
                              'typ'       ,
                              'f8'        ,
                              ('ob')
                            )
pqc = nc_out.createVariable(
                              'pqc'       ,
                              'f8'        ,
                              ('ob')
                            )
# Fill netCDF file variables
lat[:]      = obLat
lon[:]      = obLon
pre[:]      = obPre
wspd[:]     = obSpd
wdir[:]     = obDir
year[:]     = obYr
mon[:]      = obMon
day[:]      = obDay
hour[:]     = obHr
minute[:]   = obMin
typ[:]      = obTyp
pqc[:]      = obPQC
# Close netCDF file
nc_out.close()
