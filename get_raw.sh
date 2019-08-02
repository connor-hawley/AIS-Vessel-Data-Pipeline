#!/usr/bin/env bash
# gets AIS data for selected years, months, and zones via wget
# total 2017 dataset is about 80GB, so a small subset should be manageable on a laptop/desktop environment
# if only one tuple of year, month, and zone is desired, then use command-line argument './get_raw.sh year month zone'
# if more than one tuple of year, month, and zone is desired, then use command-line argument './get_raw.sh' and modify the parameters in this document

# specify whether or not to delete zipped files that are downloaded during execution
DELETE_ZIPPED=true
# specify whether or not to clear files already extracted before downloading new ones
CLEAR_BEFORE_DOWNLOAD=false
# specify the output path for the files to be downloaded
OUTPUT_DIR="./"

SITE="https://coast.noaa.gov/htdata/CMSP/AISDataHandler/"
# NOTE: all begin/end values are inclusive
# data available in supported format for years 2015 - 2017
YEAR_BEGIN=2015
YEAR_END=2017
# data available for all months (1 - 12)
# do not prefix single digit months with zero - the script takes care of that
MONTH_BEGIN=1
MONTH_END=12
# the zones are Universal Transverse Mercator (UTM) zones, defined longitudinally in 6 degree increments
# with zone 1 being 180 W - 174 W
# zone description: 1 - 9 -> Alaska, 4 - 5 -> Hawaii, 9 - 20 -> continental US
# zones ascending zones correspond to west to east longitude. see originating site for more information
# data available for zones 1 - 20
# do not prefix single digit zones with zero - the script takes care of that
ZONE_BEGIN=15
ZONE_END=20

# Retrieves an individual year, month, zone tuple's filename
get_file () {
    year="$1"
    month="$2"
    zone="$3"
    local file=''
    if [[ ${month} -gt 9 ]]; then # drop 0 if month > 9
        if [[ ${zone} -gt 9 ]]; then # drop 0 if zone > 9
            file="${year}/AIS_${year}_${month}_Zone${zone}.zip"
        else # add 0 if zone <= 9
            file="${year}/AIS_${year}_${month}_Zone0${zone}.zip"
        fi
    else # add 0 if month <= 9
        if [[ ${zone} -gt 9 ]]; then # drop 0 if zone > 9
            file="${year}/AIS_${year}_0${month}_Zone${zone}.zip"
        else # add 0 if zone <= 9
            file="${year}/AIS_${year}_0${month}_Zone0${zone}.zip"
        fi
    fi
    echo "$file"
}

# sets output directory to specified value or loads it from command line argument
if [[ (! -z "$1" && ! -z "$2" && ! -z "$3" && ! -z "$4") || \
   ( ! -z "$1" && -z "$2" ) ]]; then
   OUTPUT_DIR="$1"
fi

# changes to specified output directory before downloading the data
OUTPUT_FILE="AIS_ASCII_BY_UTM_Month"
if [[ ! -d "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR"
fi
cd "$OUTPUT_DIR"

# removes existing data on machine if CLEAR_BEFORE_DOWNLOAD is set to true
if [[ "$CLEAR_BEFORE_DOWNLOAD" = true ]]; then
    echo "removing all AIS data on machine before download"
    rm -rf "$OUTPUT_FILE"
fi

# if all 3 command line arguments are not empty, then get the data for the specified year, month, and zone
if [[ ! -z "$1" && ! -z "$2" && ! -z "$3" && ! -z "$4" ]]; then # command line argument used: $2 is year, $3 is month, and $4 is zone
    echo "getting AIS data for ${3}/${2}, zone ${4}"
    file=$(get_file "$2" "$3" "$4")
    wget "${SITE}${file}"
elif [[ ! -z "$1" && ! -z "$2" && ! -z "$3" ]]; then # command line argument used: $1 is year, $2 is month, and $3 is zone
    echo "getting AIS data for ${2}/${1}, zone ${3}"
    file=$(get_file "$1" "$2" "$3")
    wget "${SITE}${file}"
else # command line argument for year month zone is empty: use ranges defined above
    if [[ -z "$2" ]]; then
        # iterate through selected years, months, and zones
        echo "getting AIS data for times ${MONTH_BEGIN}/${YEAR_BEGIN}-${MONTH_END}/${YEAR_END}, and zones ${ZONE_BEGIN}-${ZONE_END}"
        for year in $(eval echo "{${YEAR_BEGIN}..${YEAR_END}}"); do # iterates through selected years
            for month in {1..12}; do
                for zone in $(eval echo "{${ZONE_BEGIN}..${ZONE_END}}"); do # iterates through selected zones
                    # only gets files for months after MONTH_BEGIN on YEAR_BEGIN and vice versa for MONTH_END, YEAR_END
                    if [[ ( ! ${year} -eq ${YEAR_BEGIN} || ${month} -ge ${MONTH_BEGIN} ) && \
                       ( ! ${year} -eq ${YEAR_END} || ${month} -le ${MONTH_END} ) ]]; then
                        file=$(get_file "$year" "$month" "$zone")
                        wget "${SITE}${file}"
                    fi
                done
            done
        done
    else # invalid command line argument
        echo "usage option 1: './get_raw.sh path year month zone' for specified year, month, and zone to be downloaded to path"
        echo "usage option 2: './get_raw.sh year month zone' for specified year, month, and zone. set path in file"
        echo "usage option 3: './get_raw.sh path' for specified path. set year, month, and zone ranges in file"
        echo "usage option 4: './get_raw.sh' set path, year, month, and zone ranges in file"

    fi
fi

# unzip the collected files and then delete the .zip files remaining
for zipped in *.zip; do
    unzip -o "$zipped" -d ./
    if [[ "$DELETE_ZIPPED" = true ]]; then
        rm "$zipped"
    fi
done
