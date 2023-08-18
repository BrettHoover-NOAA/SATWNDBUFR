import bufr
import numpy as np

DATA_PATH = './NC005030'

queryDict = {
             'NC005030/CLATH' : 'latitude',                     # (nobs,) dimension
             #'NC005030/CLONH' : 'longitude',                    # (nobs,) dimension
             'NC005030/PRLC[1]' : 'pressure',                   # (nobs,) dimension, there are multiple copies of PRLC but should all be identical
             'NC005030/WSPD' : 'windSpeed',                      # (nobs,) dimension
             #'NC005030/WDIR' : 'windDirection',                  # (nobs,) dimension, as (int) type
             'NC005030/SAZA'  : 'zenithAngle',                  # (nobs,) dimension
             'NC005030/AMVQIC/PCCF' : 'QIEE',                    # (nobs,4) dimension, GSI uses AMVQIC(2,2), so I will draw [:,1] here
                                                                 #                     GSI uses AMVQIC(2,4) for expectedError, so I will draw [:,3] here
             'NC005030/AMVIVR/CVWD' : 'coefficientOfVariation'  # (nobs,2) dimension, GSI uses AMVIVR(2,1), so I will draw [:,0] here
            }

def bufr_query(bufrFile, queryString, queryName):
    q = bufr.QuerySet()
    q.add(queryName, queryString)
    with bufr.File(bufrFile) as f:
        r = f.execute(q)
    return r.get(queryName)

latitude = np.asarray([])
longitude = np.asarray([])
pressure = np.asarray([])
windSpeed = np.asarray([])
windDirection = np.asarray([])
zenithAngle = np.asarray([])
qualityIndicator = np.asarray([])
expectedError = np.asarray([])
coefficientOfVariation = np.asarray([])

for key in list(queryDict.keys()):
    print('processing '+ key + '...')
    x = bufr_query(DATA_PATH, key, queryDict[key])
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
    elif queryDict[key] == 'zenithAngle':
        zenithAngle = np.append(zenithAngle, x)
    elif queryDict[key] == 'QIEE':
        qualityIndicator = np.append(qualityIndicator, x[:,1].squeeze())
        expectedError = np.append(expectedError, x[:,3].squeeze())
    elif queryDict[key] == 'coefficientOfVariation':
        coefficientOfVariation = np.append(coefficientOfVariation, x[:,0].squeeze())
    else:
        print('unknown key: ' + key)
idxAll = np.arange(np.size(latitude))
idxPass = np.copy(idxAll)

# zenith angle check
angMax = 68.
checkPass = np.where(zenithAngle <= angMax)
checkFail = np.setdiff1d(idxAll, checkPass)
idxPass = np.setdiff1d(idxPass, checkFail)
print('{:d} observations fail zenith angle check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
# quality indicator check
qiMin = 90
qiMax = 100
checkPass = np.where((qualityIndicator >= qiMin) & (qualityIndicator <= qiMax))
checkFail = np.setdiff1d(idxAll, checkPass)
idxPass = np.setdiff1d(idxPass, checkFail)
print('{:d} observations fail quality indicator check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
# pressure check
preMin = 15000.
checkPass = np.where(pressure >= preMin)
checkFail = np.setdiff1d(idxAll, checkPass)
idxPass = np.setdiff1d(idxPass, checkFail)
print('{:d} observations fail pressure check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
# coefficient of variation check
covMin = 0.04
covMax = 0.50
checkPass = np.where((coefficientOfVariation >= covMin) & (coefficientOfVariation <= covMax))
checkFail = np.setdiff1d(idxAll, checkPass)
idxPass = np.setdiff1d(idxPass, checkFail)
print('{:d} observations fail coefficient of variation check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
# exp-errnorm check
expErrNorm = 100. * np.ones(np.size(expectedError,))
speedExists = np.where(windSpeed > 0.1)
expErrNorm[speedExists] = np.divide(10. - 0.1*expectedError[speedExists], windSpeed[speedExists])
eeMax = 0.9
checkPass = np.where(expErrNorm <= eeMax)
checkFail = np.setdiff1d(idxAll, checkPass)
idxPass = np.setdiff1d(idxPass, checkFail)
print('{:d} observations fail exp-errnorm check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))



idxFail = np.setdiff1d(idxAll, idxPass)
print('{:d} OBSERVATIONS FAIL ALL QC, {:d} PASS'.format(np.size(idxFail), np.size(idxPass)))
