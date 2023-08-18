# data ingest and pre-QC checks on GOES WVDL AMVs from NC005031 tank

import bufr
import numpy as np

DATA_PATH = './NC005031'

queryDict = {
             'NC005031/CLATH'       : 'latitude',               # (nobs,) dimension
             'NC005031/CLONH'       : 'longitude',              # (nobs,) dimension
             'NC005031/PRLC[1]'     : 'pressure',               # (nobs,) dimension, there are multiple copies of PRLC but should all be identical
             'NC005031/WSPD'        : 'windSpeed',              # (nobs,) dimension
             'NC005031/WDIR'        : 'windDirection',          # (nobs,) dimension, as (int) type
             'NC005031/YEAR'        : 'year',                   # (nobs,) dimension, as (int) type
             'NC005031/MNTH'        : 'month',                  # (nobs,) dimension, as (int) type
             'NC005031/DAYS'        : 'days',                   # (nobs,) dimension, as (int) type
             'NC005031/HOUR'        : 'hour',                   # (nobs,) dimension, as (int) type
             'NC005031/MINU'        : 'minu',                   # (nobs,) dimension, as (int) type 
             'NC005031/SAZA'        : 'zenithAngle',            # (nobs,) dimension
             'NC005031/AMVQIC/PCCF' : 'QIEE',                   # (nobs,4) dimension, GSI uses AMVQIC(2,2), so I will draw [:,1] here
                                                                #                     GSI uses AMVQIC(2,4) for expectedError, so I will draw [:,3] here
             'NC005031/AMVIVR/CVWD' : 'coefficientOfVariation'  # (nobs,2) dimension, GSI uses AMVIVR(2,1), so I will draw [:,0] here
            }
# bufr_query: make a stack of BUFR queries and return resultSet object containing data
#
# INPUTS:
#    bufrFile: full-path to BUFR file (string)
#    queryDict: dictionary with keys as query-strings and values as variable-names (dict)
#
# OUTPUTS:
#    r: resultSet object from BUFR query
#
# DEPENDENCIES:
#    bufr
def bufr_query(bufrFile, queryDict):
    import bufr
    # define a bufr.QuerySet() object
    q = bufr.QuerySet()
    # loop through queryDict key-value pairs and add them to QuerySet
    for key in list(queryDict.keys()):
       q.add(queryDict[key], key)
    # safe-open bufrFile and execute query
    with bufr.File(bufrFile) as f:
        r = f.execute(q)
    # return resultSet object
    return r

# pre_qc: perform pre-QC checks on input data, return indices of pass/fail obs
#
# INPUTS:
#    pre: pressure, float(nobs,), hPa
#    spd: wind speed, float(nobs,), m/s
#    zen: zenith, angle float(nobs,), deg
#    qin: quality indicator w/o forecast, int(nobs,), 0-100 index
#    cov: coefficient of variation, float(nobs,), fractional coefficient
#    exp: expected error, float(nobs,), m/s packed into 10. - 0.1*exp format
#
# OUTPUTS:
#    idxPass: indices of observations passing all checks
#    idxFail: indices of observations failing at least one check
#
# DEPENDENCIES:
#    numpy
def pre_qc(pre, spd, zen, qin, cov, exp):
    import numpy as np
    # generate vector of all indices and copy to idxPass
    idxAll = np.arange(np.size(pre))
    idxPass = np.copy(idxAll)
    # zenith angle check
    angMax = 68.
    checkPass = np.where(zen <= angMax)
    checkFail = np.setdiff1d(idxAll, checkPass)
    idxPass = np.setdiff1d(idxPass, checkFail)
    print('{:d} observations fail zenith angle check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
    # quality indicator check
    qiMin = 90
    qiMax = 100
    checkPass = np.where((qin >= qiMin) & (qin <= qiMax))
    checkFail = np.setdiff1d(idxAll, checkPass)
    idxPass = np.setdiff1d(idxPass, checkFail)
    print('{:d} observations fail quality indicator check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
    # pressure check
    preMin = 15000.
    checkPass = np.where(pre >= preMin)
    checkFail = np.setdiff1d(idxAll, checkPass)
    idxPass = np.setdiff1d(idxPass, checkFail)
    print('{:d} observations fail pressure check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
    # coefficient of variation check
    covMin = 0.04
    covMax = 0.50
    checkPass = np.where((cov >= covMin) & (cov <= covMax))
    checkFail = np.setdiff1d(idxAll, checkPass)
    idxPass = np.setdiff1d(idxPass, checkFail)
    print('{:d} observations fail coefficient of variation check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
    # exp-errnorm check
    expErrNorm = 100. * np.ones(np.size(exp,))
    speedExists = np.where(spd > 0.1)
    expErrNorm[speedExists] = np.divide(10. - 0.1*exp[speedExists], spd[speedExists])
    eeMax = 0.9
    checkPass = np.where(expErrNorm <= eeMax)
    checkFail = np.setdiff1d(idxAll, checkPass)
    idxPass = np.setdiff1d(idxPass, checkFail)
    print('{:d} observations fail exp-errnorm check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
    # define idxFail as all indices not in idxPass
    idxFail = np.setdiff1d(idxAll, idxPass)
    print('{:d} OBSERVATIONS FAIL ALL QC, {:d} PASS'.format(np.size(idxFail), np.size(idxPass)))
    # return
    return idxPass, idxFail

#
# begin
#
if __name__ == "__main__":
    # define BUFR file-name and dictionary of query/variable key/value pairs
    DATA_PATH = './NC005030'
    queryDict = {
                 'NC005030/CLATH'       : 'latitude',               # (nobs,) dimension
                 'NC005030/CLONH'       : 'longitude',              # (nobs,) dimension
                 'NC005030/PRLC[1]'     : 'pressure',               # (nobs,) dimension, there are multiple copies of PRLC but should all be identical
                 'NC005030/WSPD'        : 'windSpeed',              # (nobs,) dimension
                 'NC005030/WDIR'        : 'windDirection',          # (nobs,) dimension, as (int) type
                 'NC005030/YEAR'        : 'year',                   # (nobs,) dimension, as (int) type
                 'NC005030/MNTH'        : 'month',                  # (nobs,) dimension, as (int) type
                 'NC005030/DAYS'        : 'day',                    # (nobs,) dimension, as (int) type
                 'NC005030/HOUR'        : 'hour',                   # (nobs,) dimension, as (int) type
                 'NC005030/MINU'        : 'minute',                 # (nobs,) dimension, as (int) type 
                 'NC005030/SAZA'        : 'zenithAngle',            # (nobs,) dimension
                 'NC005030/AMVQIC/PCCF' : 'QIEE',                   # (nobs,4) dimension, GSI uses AMVQIC(2,2), so I will draw [:,1] here
                                                                    #                     GSI uses AMVQIC(2,4) for expectedError, so I will draw [:,3] here
                 'NC005030/AMVIVR/CVWD' : 'coefficientOfVariation'  # (nobs,2) dimension, GSI uses AMVIVR(2,1), so I will draw [:,0] here
                }
    # initialize empty arrays for each variable
    latitude               = np.asarray([])
    longitude              = np.asarray([])
    pressure               = np.asarray([])
    windSpeed              = np.asarray([])
    windDirection          = np.asarray([])
    year                   = np.asarray([])
    month                  = np.asarray([])
    day                    = np.asarray([])
    hour                   = np.asarray([])
    minute                 = np.asarray([])
    zenithAngle            = np.asarray([])
    qualityIndicator       = np.asarray([])
    expectedError          = np.asarray([])
    coefficientOfVariation = np.asarray([])
    # obtain resultSet from bufr_query()
    print('obtaining ResultSet from bufr_query...')
    resultSet = bufr_query(DATA_PATH, queryDict)
    # loop through keys, extract array from resultSet and append to appropriate variable array
    for key in list(queryDict.keys()):
        print('processing '+ key + '...')
        x = resultSet.get(queryDict[key])
        print(np.shape(x))
        if queryDict[key] == 'latitude':
            latitude = np.append(latitude, x)
        elif queryDict[key] == 'longitude':
            longitude = np.append(longitude, x)
        elif queryDict[key] == 'pressure':
            pressure = np.append(pressure, x)
        elif queryDict[key] == 'windSpeed':
            windSpeed = np.append(windSpeed, x)
        elif queryDict[key] == 'windDirection':
            windDirection = np.append(windDirection, x.astype('float'))  # assert as float
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
        elif queryDict[key] == 'zenithAngle':
            zenithAngle = np.append(zenithAngle, x)
        elif queryDict[key] == 'QIEE':
            qualityIndicator = np.append(qualityIndicator, x[:,1].squeeze())
            expectedError = np.append(expectedError, x[:,3].squeeze())
        elif queryDict[key] == 'coefficientOfVariation':
            coefficientOfVariation = np.append(coefficientOfVariation, x[:,0].squeeze())
        else:
            print('unknown key: ' + key)
    # perform pre-QC checks
    idxPass, idxFail = pre_qc(pre=pressure,
                              spd=windSpeed,
                              zen=zenithAngle,
                              qin=qualityIndicator,
                              cov=coefficientOfVariation,
                              exp=expectedError)
    print(np.size(idxFail), np.size(idxPass))
    #
    # end
    #
