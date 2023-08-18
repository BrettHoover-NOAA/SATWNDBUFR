#! /bin/ksh

# Loops stitch_bufr.ksh over selected date-times

export BDMP=gfs
export SDMP=gfs

# "Cross-stitch": Pulling spec data from one dump-type and stitching into another dump-type. This is done if
#                 the spec-file for the date/time doesn't exist for the correct type. For example: we want to
#                 generate a gdas file but the spec gdas file doesn't exist, however, the spec gfs file for
#                 the date/time *does* exist. In this case, we can take the spec-list of data from the gfs file
#                 and stitch it into the base gdas file instead.

export YYYY=2022
export MM=11
export DD=09
export HH=18
#for DD in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20
#do
#    for HH in 00 06 12 18
#    do
        export YMD=${YYYY}${MM}${DD}
        echo "${BDMP} ${SDMP} ${YMD} ${HH}"
        ./stitch_bufr.ksh ${BDMP} ${SDMP} ${YMD} ${HH}
#    done
#done
