#! /bin/ksh

# BASETANK: Tank containing all 'base' subsets (default subsets not picked from SPECTANK)
# SPECTANK: Tank containing all 'specific' subsets being picked for stitching into base subsets
# TDIR: Name for directory off of CURRDIR to store stitched satwndbufr files
# BASECDUMP (INPUT 1): Name for base dump file type (typically 'gdas' or 'gfs')
# SPECCDUMP (INPUT 2): Name for spec dump file type (typically 'gdas' or 'gfs')
# YYYYMMDD (INPUT 3): Date in YYYYMMDD format
# HH (INPUT 4): Hour in HH format
# SPECLIST: List of BUFR tanks to stitch from SPECTANK into satwndbufr from BASETANK
# SPLITBUFREXEC: Full path to split_by_subset.x executable file
# SETMISSING: Define how to handle cases where tank from SPECLIST is not found in SPECTANK
#             "COPY" == copy the tank from BASETANK instead, if it exists
#             "KILL" == leave the missing tank entirely missing from the new BUFR file
export BASETANK=/scratch1/NCEPDEV/global/glopara/dump
export SPECTANK=/scratch2/NCEPDEV/stmp3/Brett.Hoover/GOES_test_data/EA_GOESR_GROUND_SYS
export TDIR=GOESEA
export BASECDUMP=${1}
export SPECCDUMP=${2}
export YYYYMMDD=${3}
export HH=${4}
export SPECLIST="NC005030 NC005031 NC005032 NC005034 NC005039"
export SPLITBUFREXEC=/scratch1/NCEPDEV/stmp4/Brett.Hoover/NCEPLIBS-bufr/build/utils/split_by_subset.x
export SETMISSING="KILL"
#
####### Probably no further changes necessary below this line ##########

# Define TMPDIR off of current directory and assert SPLITBUFREXEC
export CURRDIR=`pwd`
export TMPDIR=${CURRDIR}/${TDIR}

# Load modules for SPLITBUFREXEC
module purge
module load intel/2020.2
module load impi/2020.2

# Create TMPDIR if it does not already exist
if [ ! -d ${TMPDIR} ]; then
    mkdir -p ${TMPDIR}
fi
# Enter TMPDIR
cd ${TMPDIR}
# Create ${BASECDUMP}.${YYYYMMDD}/${HH}/atmos if it does not already exist
if [ ! -d ${BASECDUMP}.${YYYYMMDD}/${HH}/atmos ]; then
    mkdir -p ${BASECDUMP}.${YYYYMMDD}/${HH}/atmos
fi
# Enter ${BASECDUMP}/${YYYYMMDD}/${HH}/atmos
cd ${BASECDUMP}.${YYYYMMDD}/${HH}/atmos
# Create BASETANK and SPECTANK subdirectories if they do not already exist
if [ ! -d BASETANK ]; then
    mkdir -p BASETANK
fi
if [ ! -d SPECTANK ]; then
    mkdir -p SPECTANK
fi

# Copy satwndbufr file from BASETANK and SPECTANK to respective subdirectories
export SATWNDBUFR=${BASETANK}/${BASECDUMP}.${YYYYMMDD}/${HH}/atmos/${BASECDUMP}.t${HH}z.satwnd.tm00.bufr_d
if [ -f ${SATWNDBUFR} ]; then
    cp ${SATWNDBUFR} BASETANK/satwnd_base
else
    echo "BASETANK: ${SATWNDBUFR} NOT FOUND"
    # Mini clean-up
    rm -rf ./BASETANK
    rm -rf ./SPECTANK
    exit
fi
export SATWNDBUFR=${SPECTANK}/${SPECCDUMP}.${YYYYMMDD}/${HH}/atmos/${SPECCDUMP}.t${HH}z.satwnd.tm00.bufr_d
if [ -f ${SATWNDBUFR} ]; then
    cp ${SATWNDBUFR} SPECTANK/satwnd_spec
else
    echo "SPECTANK: ${SATWNDBUFR} NOT FOUND"
    # Mini clean-up
    rm -rf ./BASETANK
    rm -rf ./SPECTANK
    exit
fi
# Copy SPLITBUFREXEC
if [ -f ${SPLITBUFREXEC} ]; then
    cp ${SPLITBUFREXEC} splitbufr.x
else
    echo "SPLITBUFREXEC: ${SPLITBUFREXEC} NOT FOUND"
    # Mini clean-up
    rm -rf ./BASETANK
    rm -rf ./SPECTANK
    exit
fi

# Move to BASETANK, split satwnd_base
cd BASETANK
../splitbufr.x satwnd_base
# Return
cd ..
# Move to SPECTANK, split satwnd_spec
cd SPECTANK
../splitbufr.x satwnd_spec
# Return
cd ..
# Copy entire BASETANK to current directory
cp BASETANK/NC005* .
# Copy each entry in SPECLIST from SPECTANK to current directory (clobbering any already-existing subset from BASETANK)
for SPEC in $SPECLIST; do
    if [ -f SPECTANK/${SPEC} ]; then
        cp SPECTANK/${SPEC} .
    else
        echo "SPEC: ${SPEC} DOES NOT EXIST, SKIPPING"
        if [ "${SETMISSING}" = "COPY" ]; then
            # You can do nothing here, the default behavior is to keep the already-existing subset from BASETANK, if it exists
            echo "${SPEC} COPIED FROM BASE IF FOUND"
        elif [ "${SETMISSING}" = "KILL" ]; then
            # Delete already-existing ${SPEC} from BASETANK, if it exists
            if [ -f ${SPEC} ]; then
                echo "${SPEC} FROM BASE REMOVED"
                rm ${SPEC}
            else
                echo "${SPEC} FROM BASE NOT FOUND, DOING NOTHING"
            fi
        else
            # Unknown ${SETMISSING} value, defaulting to "COPY" behavior
            echo "SETMISSING=${SETMISSING} UNKNOWN, DEFAULTING TO COPY FROM BASE IF FOUND"
        fi
    fi
done

# Generate list of all tanks in current directory (should contain base-tanks plus any spec-tanks from SPECLIST that exist)
export TANKLIST=""
for TANK in NC005*; do
    export TANKLIST="${TANKLIST} ${TANK}"
done
echo "${TANKLIST}"
# Concatenate TANKLIST to new satwndbufr file
cat ${TANKLIST} > ./${BASECDUMP}.t${HH}z.satwnd.tm00.bufr_d

# Cleanup all NC005* tanks, BASETANK and SPECTANK subdirectories, and splitbufr.x
rm -f ./NC005*
rm -f ./splitbufr.x
rm -rf ./BASETANK
rm -rf ./SPECTANK
# Return to CURRDIR
cd ${CURRDIR}
# END

