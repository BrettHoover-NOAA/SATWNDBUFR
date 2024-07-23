# data ingest and pre-QC checks on GOES LWIR AMVs from NC005030 tank

import bufr
import numpy as np
from glob import glob
from netCDF4 import Dataset
import datetime

# bufr_query: make a stack of BUFR queries and return resultSet object containing data
#
# INPUTS:
#    bufrFile: full-path to BUFR file (string)
#    bufrTableDir: full-path to BUFR tables (string, required for reading WMO BUFR files)
#    queryDict: dictionary with keys as query-strings and values as variable-names (dict)
#
# OUTPUTS:
#    r: resultSet object from BUFR query
#
# DEPENDENCIES:
#    bufr
def bufr_query(bufrFile, bufrTableDir, queryDict):
    import bufr
    # define a bufr.QuerySet() object
    q = bufr.QuerySet()
    # loop through queryDict key-value pairs and add them to QuerySet
    for key in list(queryDict.keys()):
       q.add(queryDict[key], key)
    # safe-open bufrFile and execute query
    with bufr.File(bufrFile, bufrTableDir) as f:
        r = f.execute(q)
    # return resultSet object
    return r
#
# begin
#
if __name__ == "__main__":
    # define BUFR file-name and dictionary of query/variable key/value pairs
    anaDateTime = datetime.datetime(2023,3,1,6,0)
    DATA_PATH = '/scratch1/NCEPDEV/da/Brett.Hoover/IASI_3D/*/IASI_3D_Winds_*.bufr'
    print('DATA_PATH:', DATA_PATH)
    TABLE_PATH = './ioda-bundle/iodaconv/test/testinput/bufr_tables/'
    queryDict = {
                  '*/CLAT' : 'latitude',                                # (nobs,) dimension, deg
                  '*/CLON' : 'longitude',                               # (nobs,) dimension, deg
                  '*/YEAR' : 'year',                                    # (nobs,) dimension, as (int) type
                  '*/MNTH' : 'month',                                   # (nobs,) dimension, as (int) type
                  '*/DAYS' : 'day',                                     # (nobs,) dimension, as (int) type
                  '*/HOUR' : 'hour',                                    # (nobs,) dimension, as (int) type
                  '*/MINU' : 'minute',                                  # (nobs,) dimension, as (int) type
                  '*/RPSEQ002/PRLC[1]' : 'pressureTop',                 # (nobs,npre) dimension, Pa
                  '*/RPSEQ002/PRLC[2]' : 'pressureBottom',              # (nobs,npre) dimension, Pa
                  '*/RPSEQ002/RPSEQ003/FOST' : 'firstOrderStatistics',  # (nobs,npre,2) dimension, 10==stdv, --=observation
                  '*/RPSEQ002/RPSEQ003/UWND' : 'uwnd',                  # (nobs,npre,2) dimension, see FOST for details
                  '*/RPSEQ002/RPSEQ003/VWND' : 'vwnd',                  # (nobs,npre,2) dimension, see FOST for details
                }
    # initialize empty arrays for each variable
    latitude               = np.asarray([])  # 1D (nobs,) array
    longitude              = np.asarray([])  # 1D (nobs,) array
    pressureTop            = np.asarray([])  # 2D (nobs, npre) array
    pressureBottom         = np.asarray([])  # 2D (nobs, npre) array
    year                   = np.asarray([])  # 1D (nobs,) array
    month                  = np.asarray([])  # 1D (nobs,) array
    day                    = np.asarray([])  # 1D (nobs,) array
    hour                   = np.asarray([])  # 1D (nobs,) array
    minute                 = np.asarray([])  # 1D (nobs,) array
    firstOrderStatistics   = np.asarray([])  # 3D (nobs, npre, 2) array
    uwnd                   = np.asarray([])  # 3D (nobs, npre, 2) array
    vwnd                   = np.asarray([])  # 3D (nobs, npre, 2) array
    # compose sorted list of BUFR files
    bufrFileList = glob(DATA_PATH)
    bufrFileList.sort()
    # define list of datetime strings from bufrFileList
    bufrFileListSaved = []
    for bufrFile in bufrFileList:
        bufrFileSegments = bufrFile.split('/')[-1].split('_')
        bufrDateTimeStr = bufrFileSegments[3][0:12]
        bufrDT = datetime.datetime.strptime(bufrDateTimeStr,'%Y%m%d%H%M')
        # compute datetime difference between BUFR file and anaDateTime
        diffTime = bufrDT - anaDateTime
        diffHrs = diffTime.total_seconds()/3600.
        # save only those files within +/- 3 hrs of anaDateTime
        if np.abs(diffHrs) <= 3.:
            bufrFileListSaved.append(bufrFile)
    print('found {:d} BUFR files to process'.format(len(bufrFileListSaved)))
    # loop through BUFR files
    for bufrFile in bufrFileListSaved:
        # obtain resultSet from bufr_query()
        print('obtaining ResultSet from bufr_query...')
        resultSet = bufr_query(bufrFile, TABLE_PATH, queryDict)
        # loop through keys, extract array from resultSet and append to appropriate variable array
        for key in list(queryDict.keys()):
            print('processing '+ key + '...')
            x = resultSet.get(queryDict[key])
            #print(np.shape(x))
            # 1D variables
            if queryDict[key] == 'latitude':
                latitude = np.append(latitude, x)
            elif queryDict[key] == 'longitude':
                longitude = np.append(longitude, x)
            elif queryDict[key] == 'year':
                year = np.append(year, x)
            elif queryDict[key] == 'month':
                month = np.append(month, x)
            elif queryDict[key] == 'day':
                day = np.append(day, x)
            elif queryDict[key] == 'hour':
                hour = np.append(hour, x)
            elif queryDict[key] == 'minute':
                minute = np.append(minute, x)
            # 2D variables
            elif queryDict[key] == 'pressureTop':
                if np.size(pressureTop) == 0:
                    pressureTop = x.copy()
                else:
                    pressureTop = np.concatenate((pressureTop,x.copy()), axis=0)
            elif queryDict[key] == 'pressureBottom':
                if np.size(pressureBottom) == 0:
                    pressureBottom = x.copy()
                else:
                    pressureBottom = np.concatenate((pressureBottom,x.copy()), axis=0)
            # 3D variables
            elif queryDict[key] == 'firstOrderStatistics':
                if np.size(firstOrderStatistics) == 0:
                    firstOrderStatistics = x.copy()
                else:
                    firstOrderStatistics = np.concatenate((firstOrderStatistics,x.copy()), axis=0)
            elif queryDict[key] == 'uwnd':
                if np.size(uwnd) == 0:
                    uwnd = x.copy()
                else:
                    uwnd = np.concatenate((uwnd,x.copy()), axis=0)
            elif queryDict[key] == 'vwnd':
                if np.size(vwnd) == 0:
                    vwnd = x.copy()
                else:
                    vwnd = np.concatenate((vwnd,x.copy()), axis=0)
            else:
                print('unknown key: ' + key)
    # report size of variables
    #print('latitude shape:',np.shape(latitude))
    #print('longitude shape:',np.shape(longitude))
    #print('year shape:',np.shape(year))
    #print('month shape:',np.shape(month))
    #print('day shape:',np.shape(day))
    #print('hour shape:',np.shape(hour))
    #print('minute shape:',np.shape(minute))
    #print('pressureTop shape:',np.shape(pressureTop))
    #print('pressureBottom shape:',np.shape(pressureBottom))
    #print('firstOrderStatistics shape:',np.shape(firstOrderStatistics))
    #print('uwnd shape:',np.shape(uwnd))
    #print('vwnd shape:',np.shape(vwnd))
    print('processing {:d} observations'.format(np.size(latitude)))
    # write to netCDF file
    nc_out_filename = 'IASI3D_' + datetime.datetime.strftime(anaDateTime,'%Y%m%d%H') + '.nc'
    nc_out = Dataset(
                      nc_out_filename  , # Dataset input: Output file name
                      'w'              , # Dataset input: Make file write-able
                      format='NETCDF4' , # Dataset input: Set output format to netCDF4
                    )
    # Dimensions
    ob = nc_out.createDimension(
                                 'ob' , # nc_out.createDimension input: Dimension name
                                 None    # nc_out.createDimension input: Dimension size limit ("None" == unlimited)
                               )
    pre = nc_out.createDimension(
                                  'pre' , # nc_out.createDimension input: Dimension name
                                  None    # nc_out.createDimension input: Dimension size limit ("None" == unlimited)
                                )
    cat = nc_out.createDimension(
                                 'cat' , # nc_out.createDimension input: Dimension name
                                 None    # nc_out.createDimension input: Dimension size limit ("None" == unlimited)
                                )
    # Variables
    NC4lat = nc_out.createVariable(
                                  'latitude'       ,
                                  'f8'        ,
                                  ('ob')
                                )
    NC4lon = nc_out.createVariable(
                                  'longitude'       ,
                                  'f8'        ,
                                  ('ob')
                                )
    NC4year = nc_out.createVariable(
                                  'year'       ,
                                  'i8'        ,
                                  ('ob')
                                )
    NC4month = nc_out.createVariable(
                                  'month'       ,
                                  'i8'        ,
                                  ('ob')
                                )
    NC4day = nc_out.createVariable(
                                  'day'       ,
                                  'i8'        ,
                                  ('ob')
                                )
    NC4hour = nc_out.createVariable(
                                  'hour'       ,
                                  'i8'        ,
                                  ('ob')
                                )
    NC4minute = nc_out.createVariable(
                                  'minute'       ,
                                  'i8'        ,
                                  ('ob')
                                )
    NC4preTop = nc_out.createVariable(
                                  'pressureTop'       ,
                                  'f8'        ,
                                  ('ob', 'pre')
                                )
    NC4preBot = nc_out.createVariable(
                                      'pressureBottom'       ,
                                      'f8'        ,
                                       ('ob', 'pre')
                                     )
    NC4FOST = nc_out.createVariable(
                                    'firstOrderStatistics'       ,
                                    'f8'        ,
                                     ('ob', 'pre', 'cat')
                                   )
    NC4uwnd = nc_out.createVariable(
                                    'uwnd'       ,
                                    'f8'        ,
                                     ('ob', 'pre', 'cat')
                                   )
    NC4vwnd = nc_out.createVariable(
                                    'vwnd'       ,
                                    'f8'        ,
                                     ('ob', 'pre', 'cat')
                                   )
    # Fill netCDF file variables
    NC4lat[:]       = latitude
    NC4lon[:]       = longitude
    NC4year[:]      = year
    NC4month[:]     = month
    NC4day[:]       = day
    NC4hour[:]      = hour
    NC4minute[:]    = minute
    NC4preTop[:,:]  = pressureTop
    NC4preBot[:,:]  = pressureBottom
    NC4FOST[:,:,:]  = firstOrderStatistics
    NC4uwnd[:,:,:]  = uwnd
    NC4vwnd[:,:,:]  = vwnd
    # Close netCDF file
    nc_out.close()
    #
    # end
    #
