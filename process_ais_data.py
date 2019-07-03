# IMPORTANT: run ./get_raw.sh with desired parameters to obtain the actual CSVs on your local machine before running this file
import os
import csv
import math

# set number of rows to read of each CSV file since reading > 3 GB is going to take forever
MAX_ROWS = 100
# sets the side length of the square being used to discretize the grid, in degrees
grid_len = 1.

# row indices to be accessed later in case other data does not have same row order
ind_mmsi = 0
ind_lat = 2
ind_lon = 3

# UTM zones exclude values outside 84 N latitude and 80 S latitude
global_min_lat = -80
global_max_lat = 84.

# helper function to get longitude boundaries corresponding to zone
def get_bounds(zone):
    min_lon = (6. * ((zone - 1) % 60)) - 180.
    return min_lon, (min_lon + 6.)

# helper function to get file year, month, and zone given file name
def get_meta_data(file_name):
    meta_file_data = csv_file.split('_') # splits csv file on '_' character, which separates relevant file name information (zone, month, year)
    year = int(meta_file_data[-3]) # third to last element of file is the year
    month = int(meta_file_data[-2]) # second to last element of file is the month
    # get zone number for csv file being read
    ending_raw = meta_file_data[-1] # gets last part of the file, with format "ZoneXX.csv"
    ending_data = ending_raw.split('.') # splits last part of file on '.' character, so the file extension can be ignored
    zone_raw = ending_data[0] # gets "ZoneXX" string
    zone_data = zone_raw[-2:] # gets last 2 characters of "ZoneXX" string - will be the zone number
    zone = int(zone_data)
    return year, month, zone

# takes in latitude and longitude and returns the resultant integer state
def get_state(cur_lat, cur_lon, min_lat, min_lon, num_cols, grid_len):
    return 0

# traverses the directory containing the decompressed AIS data to get the CSV names for further processing
csv_files = []
dir_data = "AIS_ASCII_by_UTM_Month/"
for root, dirs, files in os.walk(dir_data):
    for file in files:
        if file.endswith(".csv"):
             csv_files.append(os.path.join(root, file)) # csv_files will contain file locations relative to current directory

# initialize dictionary that will be filled with all trajectories
trajectories = {}
# min_lat and min_lon will keep track of the maximum and minimum longitudes in the dataset over all csvs
min_lat = global_max_lat
max_lat = global_min_lat
# these lists will keep track of minimum and maximum longitudes for all the zones seen
# minimum of minimum longitudes and maximum of maximum longitudes will be used for final grid
min_lons = []
max_lons = []

# iterate through each csv_file
for csv_file in csv_files:
    print('reading csv file: {}'.format(csv_file))
    year, month, zone = get_meta_data(csv_file) # finds the data year, month, and zone based on the file name
    print('year: {}, month: {}, zone: {}'.format(year, month, zone))
    min_lon, max_lon = get_bounds(zone) # finds longitude boundaries based on the zone number
    # keeps track of longitude minima and maxima across files
    min_lons.append(min_lon)
    max_lons.append(max_lon)
    with open(csv_file, 'r') as fh: # boilerplate to read in csv file
        reader = csv.reader(fh)
        header = reader.__next__() # retrieves header of csv
        print('header: {}'.format(header))
        # for i in range(MAX_ROWS):
            # row = reader.__next__() # get new row of the data
        for row in reader:
            mmsi = row[ind_mmsi] # gets current id, latitude, and longitude of column
            cur_lat = float(row[ind_lat])
            cur_lon = float(row[ind_lon])
            if not (mmsi in trajectories): # create new trajectory for unseen mmsi
                trajectories[mmsi] = []
            trajectories[mmsi].append([cur_lat, cur_lon]) # add state to mmsi's trajectory

            # finds minimum and maximum latitude in dataset for later grid sizing
            if (cur_lat > max_lat):
                max_lat = cur_lat
            elif (cur_lat < min_lat):
                min_lat = cur_lat

# minimum and maximum longitude for final grid
min_lon = min(min_lons)
max_lon = max(max_lons)
print('minimum longitude: {}, maximum longitude: {}'.format(min_lon, max_lon))
# TODO: change grid boundaries to provide a degree of padding max to each of the boundary values

num_cols = math.ceil((max_lon - min_lon)/grid_len) # number of columns in the resulting grid
print('number of columns in final grid: {}'.format(num_cols))

# minimum and maximum latitude for final grid
print('minimum latitude: {}, maximum latitude: {}'.format(min_lat, max_lat))

# TODO: open csv to write to once trajectories are discretized
# TODO: write csv header line

# discretize each trajectory now that boundaries of grid are known
for mmsi, trajectory in trajectories.items():
    # print('trajectory for {}: {}'.format(mmsi, trajectory))
    prev_state = -1
    for coords in trajectory:
        cur_lat = coords[0]
        cur_lon = coords[1]
        # gets discretized state based on current coordinates, the upper left bound of the grid, the number of columns, and the grid unit length
        cur_state = get_state(cur_lat, cur_lon, min_lat, min_lon, num_cols, grid_len)
        if (prev_state != -1): # if there is a valid previous state, write a line of the csv
            cur_action = get_action(prev_state, cur_state, num_cols) # infers action, implying that the system is deterministic
            # TODO: write SAS line of csv

# TODO: visualize resulting trajectories on matplotlib

# TODO: convert each step of this process to a Jupyter notebook
