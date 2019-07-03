# gets AIS data for selected years, months, and zones via wget
# total 2017 dataset is about 80GB, so a small subset should be manageable on a laptop/desktop environment
# if only one tuple of year, month, and zone is desired, then use command-line argument './get_raw.sh year month zone'
# if more than one tuple of year, month, and zone is desired, then use command-line argument './get_raw.sh' and modify the parameters in this document

# specify whether or not to delete zipped files that are downloaded during execution
DELETE_ZIPPED=true
# specify whether or not to clear files already extracted before downloading new ones
# TODO: make this smarter so that when CLEAR_BEFORE_DOWNLOAD is false it does not download files already on disk
CLEAR_BEFORE_DOWNLOAD=true
OUTPUT_FILE="AIS_ASCII_by_UTM_Month"

SITE="https://coast.noaa.gov/htdata/CMSP/AISDataHandler/"
# NOTE: all begin/end values are inclusive
# data available in supported format for years 2015 - 2017
# TODO: modify script to support data extraction from before 2015
YEAR_BEGIN=2017
YEAR_END=2017
# data available for all months (1 - 12)
# do not prefix single digit months with zero - the script takes care of that
MONTH_BEGIN=1
MONTH_END=2
# the zones are Universal Transverse Mercator (UTM) zones, defined longitudinally
# zone description: 1 - 9 -> Alaska, 4 - 5 -> Hawaii, 9 - 20 -> continental US
# zones ascending zones correspond to west to east longitude. see originating site for more information
# data available for zones 1 - 20
# do not prefix single digit zones with zero - the script takes care of that
ZONE_BEGIN=18
ZONE_END=18

# define function for retrieving an individual year, month, zone tuple's filename
get_file () {
    year="$1"
    month="$2"
    zone="$3"
    local file=''
    if [ ${month} -gt 9 ]; then # drop 0 if month > 9
        if [ ${zone} -gt 9 ]; then # drop 0 if zone > 9
            file="${year}/AIS_${year}_${month}_Zone${zone}.zip"
        else # add 0 if zone <= 9
            file="${year}/AIS_${year}_${month}_Zone0${zone}.zip"
        fi
    else # add 0 if month <= 9
        if [ ${zone} -gt 9 ]; then # drop 0 if zone > 9
            file="${year}/AIS_${year}_0${month}_Zone${zone}.zip"
        else # add 0 if zone <= 9
            file="${year}/AIS_${year}_0${month}_Zone0${zone}.zip"
        fi
    fi
    echo "$file"
}

if [ "$CLEAR_BEFORE_DOWNLOAD" = true ]; then
    echo "removing all AIS data on machine before download"
    rm -rf "$OUTPUT_FILE"
fi

# parse command line arguments
if [[ ! -z "$1" && ! -z "$2" && ! -z "$3" ]]; then # command line argument used: $1 is year, $2 is month, and $3 is zone
    echo "getting AIS data for ${2}/${1}, zone ${3}"
    file=$(get_file "$1" "$2" "$3")
    wget "${SITE}${file}"
else
    if [[ -z "$1"  && -z "$2" && -z "$3" ]]; then # command line argument is empty: use ranges defined above
        # iterate through cartesian product of selected years, months, and zones
        echo "getting AIS data for years ${YEAR_BEGIN}-${YEAR_END}, months ${MONTH_BEGIN}-${MONTH_END}, and zones ${ZONE_BEGIN}-${ZONE_END}"
        for year in $(seq $YEAR_BEGIN $YEAR_END); do # iterates through selected years
            for month in $(seq $MONTH_BEGIN $MONTH_END); do # iterates through selected months
                for zone in $(seq $ZONE_BEGIN $ZONE_END); do # iterates through selected zones
                    file=$(get_file "$year" "$month" "$zone")
                    wget "$SITE$file"
                done
            done
        done
    else # invalid command line argument
        echo "usage option 1: './get_raw.sh year month zone' for one tuple of year, month, and zone"
        echo "usage option 2: './get_raw.sh' and set year, month, and zone ranges in the file"
    fi
fi
for zipped in *.zip; do
    unzip $zipped -d ./
    if [ "$DELETE_ZIPPED" = true ]; then
        rm "$zipped"
    fi
done
