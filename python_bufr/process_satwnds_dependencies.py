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

# process_NC005030: draws NC005030 observations (GOES LWIR AMVs) from BUFR file, and returns
#                   variables based on entries in returnDict.
#
# INPUTS:
#    bufrFileName: full-path to BUFR file (string)
#    returnDict: dictionary with key/value pairs representing
#                    keys: BUFR query (string)
#                    values: variable name (string)
#
# OUTPUTS:
#    outputDict: dictionary with key/value pairs representing
#                    keys: variable name (string)
#                    values: vector of values (numpy vector)
#
# DEPENDENCIES:
#    numpy
#    bufr
#    bufr_query (above)
def process_NC005030(bufrFileName, returnDict):
    import numpy as np
    import bufr
    #
    # define internal functions
    #
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
    # define dictionary of query/variable key/value pairs needed for pre_qc()
    queryDict = {
                 'NC005030/PRLC[1]'     : 'pressure',               # (nobs,) dimension, there are multiple copies of PRLC but should all be identical
                 'NC005030/WSPD'        : 'windSpeed',              # (nobs,) dimension
                 'NC005030/SAZA'        : 'zenithAngle',            # (nobs,) dimension
                 'NC005030/AMVQIC/PCCF' : 'QIEE',                   # (nobs,4) dimension, GSI uses AMVQIC(2,2), so I will draw [:,1] here
                                                                    #                     GSI uses AMVQIC(2,4) for expectedError, so I will draw [:,3] here
                 'NC005030/AMVIVR/CVWD' : 'coefficientOfVariation'  # (nobs,2) dimension, GSI uses AMVIVR(2,1), so I will draw [:,0] here
                }
    # merge this dictionary with returnDict, defaulting to these values where appropriate
    mergedDict = returnDict.copy()
    mergedDict.update(queryDict)
    # initialize empty arrays for each pre-QC variable
    pressure               = np.asarray([])
    windSpeed              = np.asarray([])
    zenithAngle            = np.asarray([])
    qualityIndicator       = np.asarray([])
    expectedError          = np.asarray([])
    coefficientOfVariation = np.asarray([])
    # obtain resultSet from bufr_query()
    resultSet = bufr_query(bufrFileName, mergedDict)
    # loop through keys, extract array from resultSet and append to appropriate variable array
    # and/or outputDict as appropriate. This is done on a per-variable basis, because some
    # variables are packed together into multi-dimensional arrays and need to be split apart
    # to be sent to separate obs vectors. If you have a variable you want passed along to outputDict
    # that is one of these special cases, include it as a special case below.
    #
    # these are all handled as appends to an initially empty obs vector, since you could have multiple
    # individual queries point to the same output variable, e.g.: latitudes from multiple BUFR tanks
    # all pulled into a single 'latitude' obs vector.
    outputDict = {}
    for varName in list(returnDict.values()):
        outputDict[varName] = np.asarray([])
    for key in list(mergedDict.keys()):
        print('processing '+ key + '...')
        x = resultSet.get(mergedDict[key])
        if mergedDict[key] == 'pressure':
            pressure = np.append(pressure, x)
            if 'pressure' in list(returnDict.values()):
                outputDict['pressure'] = np.append(outputDict['pressure'], x)
        elif mergedDict[key] == 'windSpeed':
            windSpeed = np.append(windSpeed, x)
            if 'windSpeed' in list(returnDict.values()):
                outputDict['windSpeed'] = np.append(outputDict['windSpeed'], x)
        elif mergedDict[key] == 'zenithAngle':
            zenithAngle = np.append(zenithAngle, x)
            if 'zenithAngle' in list(returnDict.values()):
                outputDict['zenithAngle'] = np.append(outputDict['zenithAngle'], x)
        elif mergedDict[key] == 'QIEE':
            qualityIndicator = np.append(qualityIndicator, x[:,1].squeeze())
            expectedError = np.append(expectedError, x[:,3].squeeze())
            if 'qualityIndicator' in list(returnDict.values()):
                outputDict['qualityIndicator'] = np.append(outputDict['qualityIndicator'], x[:,1].squeeze())
            if 'expectedError' in list(returnDict.values()):
                outputDict['expectedError'] = np.append(outputDict['expectedError'], x[:,3].squeeze())
        elif mergedDict[key] == 'coefficientOfVariation':
            coefficientOfVariation = np.append(coefficientOfVariation, x[:,0].squeeze())
            if 'coefficientOfVariation' in list(returnDict.values()):
                outputDict['coefficientOfVariation'] = np.append(outputDict['coefficientOfVariation'], x)
        else:
            # all variables in mergedDict not in queryDict, assumed to be simple variables with no
            # unpacking of multi-dimensional arrays necessary, but if any special cases exist feel free
            # to add them here if they aren't already a pre-QC variable in queryDict
            print('key: ' + key + ' is NOT a pre-QC key')
            if mergedDict[key] in list(returnDict.values()):
                outputDict[mergedDict[key]] = np.append(outputDict[mergedDict[key]], x)
    # perform pre-QC checks
    idxPass, idxFail = pre_qc(pre=pressure,
                              spd=windSpeed,
                              zen=zenithAngle,
                              qin=qualityIndicator,
                              cov=coefficientOfVariation,
                              exp=expectedError)
    print(np.size(idxFail), np.size(idxPass))
    # create a preQC variable with 1==pass, -1==fail
    preQC = -1 * np.ones((np.size(idxPass) + np.size(idxFail),), dtype='int')
    preQC[idxPass] = 1
    # append preQC to outputDict
    outputDict['preQC'] = preQC
    # return outputDict
    return outputDict
    #
    # end
    #


# process_NC005031: draws NC005031 observations (GOES WVDL AMVs) from BUFR file, and returns
#                   variables based on entries in returnDict.
#
# INPUTS:
#    bufrFileName: full-path to BUFR file (string)
#    returnDict: dictionary with key/value pairs representing
#                    keys: BUFR query (string)
#                    values: variable name (string)
#
# OUTPUTS:
#    outputDict: dictionary with key/value pairs representing
#                    keys: variable name (string)
#                    values: vector of values (numpy vector)
#
# DEPENDENCIES:
#    numpy
#    bufr
#    bufr_query (above)
def process_NC005031(bufrFileName, returnDict):
    import numpy as np
    import bufr
    #
    # define internal functions
    #
    # pre_qc: perform pre-QC checks on input data, return indices of pass/fail obs
    #
    # INPUTS:
    #    pre: pressure, float(nobs,), hPa
    #    spd: wind speed, float(nobs,), m/s
    #    zen: zenith, angle float(nobs,), deg
    #    qin: quality indicator w/o forecast, int(nobs,), 0-100 index
    #    exp: expected error, float(nobs,), m/s packed into 10. - 0.1*exp format
    #
    # OUTPUTS:
    #    idxPass: indices of observations passing all checks
    #    idxFail: indices of observations failing at least one check
    #
    # DEPENDENCIES:
    #    numpy
    def pre_qc(pre, spd, zen, qin, exp):
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
    # define dictionary of query/variable key/value pairs needed for pre_qc()
    queryDict = {
                 'NC005031/PRLC[1]'     : 'pressure',               # (nobs,) dimension, there are multiple copies of PRLC but should all be identical
                 'NC005031/WSPD'        : 'windSpeed',              # (nobs,) dimension
                 'NC005031/SAZA'        : 'zenithAngle',            # (nobs,) dimension
                 'NC005031/AMVQIC/PCCF' : 'QIEE'                    # (nobs,4) dimension, GSI uses AMVQIC(2,2), so I will draw [:,1] here
                                                                    #                     GSI uses AMVQIC(2,4) for expectedError, so I will draw [:,3] here
                }
    # merge this dictionary with returnDict, defaulting to these values where appropriate
    mergedDict = returnDict.copy()
    mergedDict.update(queryDict)
    # initialize empty arrays for each pre-QC variable
    pressure               = np.asarray([])
    windSpeed              = np.asarray([])
    zenithAngle            = np.asarray([])
    qualityIndicator       = np.asarray([])
    expectedError          = np.asarray([])
    # obtain resultSet from bufr_query()
    resultSet = bufr_query(bufrFileName, mergedDict)
    # loop through keys, extract array from resultSet and append to appropriate variable array
    # and/or outputDict as appropriate. This is done on a per-variable basis, because some
    # variables are packed together into multi-dimensional arrays and need to be split apart
    # to be sent to separate obs vectors. If you have a variable you want passed along to outputDict
    # that is one of these special cases, include it as a special case below.
    #
    # these are all handled as appends to an initially empty obs vector, since you could have multiple
    # individual queries point to the same output variable, e.g.: latitudes from multiple BUFR tanks
    # all pulled into a single 'latitude' obs vector.
    outputDict = {}
    for varName in list(returnDict.values()):
        outputDict[varName] = np.asarray([])
    for key in list(mergedDict.keys()):
        print('processing '+ key + '...')
        x = resultSet.get(mergedDict[key])
        if mergedDict[key] == 'pressure':
            pressure = np.append(pressure, x)
            if 'pressure' in list(returnDict.values()):
                outputDict['pressure'] = np.append(outputDict['pressure'], x)
        elif mergedDict[key] == 'windSpeed':
            windSpeed = np.append(windSpeed, x)
            if 'windSpeed' in list(returnDict.values()):
                outputDict['windSpeed'] = np.append(outputDict['windSpeed'], x)
        elif mergedDict[key] == 'zenithAngle':
            zenithAngle = np.append(zenithAngle, x)
            if 'zenithAngle' in list(returnDict.values()):
                outputDict['zenithAngle'] = np.append(outputDict['zenithAngle'], x)
        elif mergedDict[key] == 'QIEE':
            qualityIndicator = np.append(qualityIndicator, x[:,1].squeeze())
            expectedError = np.append(expectedError, x[:,3].squeeze())
            if 'qualityIndicator' in list(returnDict.values()):
                outputDict['qualityIndicator'] = np.append(outputDict['qualityIndicator'], x[:,1].squeeze())
            if 'expectedError' in list(returnDict.values()):
                outputDict['expectedError'] = np.append(outputDict['expectedError'], x[:,3].squeeze())
        else:
            # all variables in mergedDict not in queryDict, assumed to be simple variables with no
            # unpacking of multi-dimensional arrays necessary, but if any special cases exist feel free
            # to add them here if they aren't already a pre-QC variable in queryDict
            print('key: ' + key + ' is NOT a pre-QC key')
            if mergedDict[key] in list(returnDict.values()):
                outputDict[mergedDict[key]] = np.append(outputDict[mergedDict[key]], x)
    # perform pre-QC checks
    idxPass, idxFail = pre_qc(pre=pressure,
                              spd=windSpeed,
                              zen=zenithAngle,
                              qin=qualityIndicator,
                              exp=expectedError)
    print(np.size(idxFail), np.size(idxPass))
    # create a preQC variable with 1==pass, -1==fail
    preQC = -1 * np.ones((np.size(idxPass) + np.size(idxFail),), dtype='int')
    preQC[idxPass] = 1
    # append preQC to outputDict
    outputDict['preQC'] = preQC
    # return outputDict
    return outputDict
    #
    # end
    #


# process_NC005032: draws NC005032 observations (GOES VIS AMVs) from BUFR file, and returns
#                   variables based on entries in returnDict.
#
# INPUTS:
#    bufrFileName: full-path to BUFR file (string)
#    returnDict: dictionary with key/value pairs representing
#                    keys: BUFR query (string)
#                    values: variable name (string)
#
# OUTPUTS:
#    outputDict: dictionary with key/value pairs representing
#                    keys: variable name (string)
#                    values: vector of values (numpy vector)
#
# DEPENDENCIES:
#    numpy
#    bufr
#    bufr_query (above)
def process_NC005032(bufrFileName, returnDict):
    import numpy as np
    import bufr
    #
    # define internal functions
    #
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
        # pressure check (preMin=70000. cutoff for VIS winds)
        preMin = 70000.
        checkPass = np.where(pre >= preMin)
        checkFail = np.setdiff1d(idxAll, checkPass)
        idxPass = np.setdiff1d(idxPass, checkFail)
        print('{:d} observations fail pressure check, {:d} pass'.format(np.size(checkFail), np.size(checkPass)))
        # coefficient of variation check
        covMax = 0.50
        checkPass = np.where(cov <= covMax)
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
    # define dictionary of query/variable key/value pairs needed for pre_qc()
    queryDict = {
                 'NC005032/PRLC[1]'     : 'pressure',               # (nobs,) dimension, there are multiple copies of PRLC but should all be identical
                 'NC005032/WSPD'        : 'windSpeed',              # (nobs,) dimension
                 'NC005032/SAZA'        : 'zenithAngle',            # (nobs,) dimension
                 'NC005032/AMVQIC/PCCF' : 'QIEE',                   # (nobs,4) dimension, GSI uses AMVQIC(2,2), so I will draw [:,1] here
                                                                    #                     GSI uses AMVQIC(2,4) for expectedError, so I will draw [:,3] here
                 'NC005032/AMVIVR/CVWD' : 'coefficientOfVariation'  # (nobs,2) dimension, GSI uses AMVIVR(2,1), so I will draw [:,0] here
                }
    # merge this dictionary with returnDict, defaulting to these values where appropriate
    mergedDict = returnDict.copy()
    mergedDict.update(queryDict)
    # initialize empty arrays for each pre-QC variable
    pressure               = np.asarray([])
    windSpeed              = np.asarray([])
    zenithAngle            = np.asarray([])
    qualityIndicator       = np.asarray([])
    expectedError          = np.asarray([])
    coefficientOfVariation = np.asarray([])
    # obtain resultSet from bufr_query()
    resultSet = bufr_query(bufrFileName, mergedDict)
    # loop through keys, extract array from resultSet and append to appropriate variable array
    # and/or outputDict as appropriate. This is done on a per-variable basis, because some
    # variables are packed together into multi-dimensional arrays and need to be split apart
    # to be sent to separate obs vectors. If you have a variable you want passed along to outputDict
    # that is one of these special cases, include it as a special case below.
    #
    # these are all handled as appends to an initially empty obs vector, since you could have multiple
    # individual queries point to the same output variable, e.g.: latitudes from multiple BUFR tanks
    # all pulled into a single 'latitude' obs vector.
    outputDict = {}
    for varName in list(returnDict.values()):
        outputDict[varName] = np.asarray([])
    for key in list(mergedDict.keys()):
        print('processing '+ key + '...')
        x = resultSet.get(mergedDict[key])
        if mergedDict[key] == 'pressure':
            pressure = np.append(pressure, x)
            if 'pressure' in list(returnDict.values()):
                outputDict['pressure'] = np.append(outputDict['pressure'], x)
        elif mergedDict[key] == 'windSpeed':
            windSpeed = np.append(windSpeed, x)
            if 'windSpeed' in list(returnDict.values()):
                outputDict['windSpeed'] = np.append(outputDict['windSpeed'], x)
        elif mergedDict[key] == 'zenithAngle':
            zenithAngle = np.append(zenithAngle, x)
            if 'zenithAngle' in list(returnDict.values()):
                outputDict['zenithAngle'] = np.append(outputDict['zenithAngle'], x)
        elif mergedDict[key] == 'QIEE':
            qualityIndicator = np.append(qualityIndicator, x[:,1].squeeze())
            expectedError = np.append(expectedError, x[:,3].squeeze())
            if 'qualityIndicator' in list(returnDict.values()):
                outputDict['qualityIndicator'] = np.append(outputDict['qualityIndicator'], x[:,1].squeeze())
            if 'expectedError' in list(returnDict.values()):
                outputDict['expectedError'] = np.append(outputDict['expectedError'], x[:,3].squeeze())
        elif mergedDict[key] == 'coefficientOfVariation':
            coefficientOfVariation = np.append(coefficientOfVariation, x[:,0].squeeze())
            if 'coefficientOfVariation' in list(returnDict.values()):
                outputDict['coefficientOfVariation'] = np.append(outputDict['coefficientOfVariation'], x)
        else:
            # all variables in mergedDict not in queryDict, assumed to be simple variables with no
            # unpacking of multi-dimensional arrays necessary, but if any special cases exist feel free
            # to add them here if they aren't already a pre-QC variable in queryDict
            print('key: ' + key + ' is NOT a pre-QC key')
            if mergedDict[key] in list(returnDict.values()):
                outputDict[mergedDict[key]] = np.append(outputDict[mergedDict[key]], x)
    # perform pre-QC checks
    idxPass, idxFail = pre_qc(pre=pressure,
                              spd=windSpeed,
                              zen=zenithAngle,
                              qin=qualityIndicator,
                              cov=coefficientOfVariation,
                              exp=expectedError)
    print(np.size(idxFail), np.size(idxPass))
    # create a preQC variable with 1==pass, -1==fail
    preQC = -1 * np.ones((np.size(idxPass) + np.size(idxFail),), dtype='int')
    preQC[idxPass] = 1
    # append preQC to outputDict
    outputDict['preQC'] = preQC
    # return outputDict
    return outputDict
    #
    # end
    #
