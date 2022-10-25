#! /bin/ksh

# Loops stitch_bufr.ksh over selected date-times

export DMP=gfs

export YYYY=2022
export MM=09

for DD in 24 25 26 27 28 29 30
do
    for HH in 00 06 12 18
    do
        export YMD=${YYYY}${MM}${DD}
        echo "${DMP} ${YMD} ${HH}"
        ./stitch_bufr.ksh ${DMP} ${YMD} ${HH}
    done
done

export YYYY=2022
export MM=10

for DD in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19
do
    for HH in 00 06 12 18
    do
        export YMD=${YYYY}${MM}${DD}
        echo "${DMP} ${YMD} ${HH}"
        ./stitch_bufr.ksh ${DMP} ${YMD} ${HH}
    done
done
