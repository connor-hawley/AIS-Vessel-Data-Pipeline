# IMPORTANT: run ./get_raw.sh with desired parameters to obtain the actual CSVs
# on your local machine before running this file
import os
import csv
import math

# set number of rows to read of each CSV file since reading > 3 GB is going to take forever
MAX_ROWS = 100000
# sets the side length of the square being used to discretize the grid, in degrees
grid_len = 0.1
# specifies output file name (should be .csv)
out_file = 'ais_data_output.csv'
# specifies header row of output csv file
out_header = ['sequence_id', 'from_state_id', 'action_id', 'to_state_id']

# row indices to be accessed later in case other data does not have same row order
ind_mmsi = 0
ind_lat = 2
ind_lon = 3

# UTM zones exclude values outside 84 N latitude and 80 S latitude
global_min_lat = -80
global_max_lat = 84.


def get_bounds(zone):
    # helper function to get longitude boundaries corresponding to zone
    min_lon = (6. * ((zone - 1) % 60)) - 180.
    return min_lon, (min_lon + 6.)


def get_meta_data(file_name):
    # helper function to get file year, month, and zone given file name
    meta_file_data = file_name.split('_')  # splits csv file on '_' character, which separates relevant file info
    year = int(meta_file_data[-3])  # third to last element of file is the year
    month = int(meta_file_data[-2])  # second to last element of file is the month
    # get zone number for csv file being read
    ending_raw = meta_file_data[-1] # gets last part of the file, with format "ZoneXX.csv"
    ending_data = ending_raw.split('.')  # splits last part of file on '.' character
    zone_raw = ending_data[0] # gets "ZoneXX" string
    zone_data = zone_raw[-2:] # gets last 2 characters of "ZoneXX" string - will be the zone number
    zone = int(zone_data)
    return year, month, zone


def get_state(cur_lat, cur_lon, min_lat, min_lon, num_cols, grid_len):
    # takes in latitude and longitude and returns the resultant integer state
    # normalize lat and lon to the minimum values
    cur_lat -= min_lat
    cur_lon -= min_lon
    # find the row and column position based on grid_len
    row = math.floor(cur_lat / grid_len)
    col = math.floor(cur_lon / grid_len)
    # find total state based on num_cols in final grid
    return row * num_cols + col


def get_action(prev_state, cur_state, num_cols):
    # finds action according to spiral rule
    # gets row, column decomposition for previous and current states
    prev_row = math.floor(prev_state / num_cols)
    prev_col = prev_state % num_cols
    cur_row = math.floor(cur_state / num_cols)
    cur_col = cur_state % num_cols
    rel_row = cur_row - prev_row
    rel_col = cur_col - prev_col

    # simple routine to calculate a spiral set of actions
    action_num = x = y = i = 0
    layer = (2 * i + 1) ** 2  # sets breakpoint for when to increment i
    while not(x == rel_col and y == rel_row):
        if action_num == layer - 1:
            i += 1  # move to next spiral
            x = i
            layer = (2 * i + 1) ** 2  # calculate breakpoint for next spiral
        elif x == i and y < i:
            y += 1
        elif x > -i and y == i:
            x -= 1
        elif x == -i and y > -i:
            y -= 1
        elif x < i and y == -i:
            x += 1
        elif x == i and y < 0:
            y += 1
        action_num += 1
        print('x: {}, y: {}, action_num: {}'.format(x, y, action_num))

    return action_num

# traverses the directory containing the decompressed AIS data to get the CSV names for further processing
csv_files = []
dir_data = "AIS_ASCII_by_UTM_Month/"
for root, dirs, files in os.walk(dir_data):
    for file in files:
        if file.endswith(".csv"):
            # csv_files will contain file locations relative to current directory
            csv_files.append(os.path.join(root, file))

# initialize dictionary that will be filled with all trajectories
trajectories = {}
# min_lat and min_lon will keep track of the maximum and minimum longitudes in the dataset over all csvs
min_lat = global_max_lat
max_lat = global_min_lat
# these lists will keep track of minimum and maximum longitudes for all the zones seen
# minimum of minimum longitudes and maximum of maximum longitudes will be used for final grid
min_lons = []
max_lons = []

# iterate through each csv_file to build trajectories
for csv_file in csv_files:
    print('reading csv file: {}'.format(csv_file))
    year, month, zone = get_meta_data(csv_file)  # finds the data year, month, and zone based on the file name
    print('year: {}, month: {}, zone: {}'.format(year, month, zone))
    min_lon, max_lon = get_bounds(zone)  # finds longitude boundaries based on the zone number
    # keeps track of longitude minima and maxima across files
    min_lons.append(min_lon)
    max_lons.append(max_lon)
    with open(csv_file, 'r') as fh:  # boilerplate to read in csv file
        reader = csv.reader(fh)
        header = reader.__next__()  # retrieves header of csv
        print('header: {}'.format(header))
        for i in range(MAX_ROWS):
            row = reader.__next__()  # get new row of the data
        # for row in reader:  # placeholder for complete code
            mmsi = row[ind_mmsi]  # gets current id, latitude, and longitude of column
            cur_lat = float(row[ind_lat])
            cur_lon = float(row[ind_lon])
            if not (mmsi in trajectories):  # create new trajectory for unseen mmsi
                trajectories[mmsi] = []
            trajectories[mmsi].append([cur_lat, cur_lon])  # add state to mmsi's trajectory
            # finds minimum and maximum latitude in dataset for later grid sizing
            if cur_lat > max_lat:
                max_lat = cur_lat
            elif cur_lat < min_lat:
                min_lat = cur_lat

# minimum and maximum longitude for final grid
min_lon = min(min_lons)
max_lon = max(max_lons)

# changes grid boundaries to provide some padding to each boundary, rounded to nearest degree
min_lat = float(math.floor(min_lat))
max_lat = float(math.floor(max_lat))
min_lon = float(math.floor(min_lon))
max_lon = float(math.ceil(max_lon))

# latitude and longitude boundaries for final grid
print('minimum longitude: {}, maximum longitude: {}'.format(min_lon, max_lon))
print('minimum latitude: {}, maximum latitude: {}'.format(min_lat, max_lat))

num_cols = math.ceil((max_lon - min_lon)/grid_len)  # number of columns in the resulting grid
print('number of columns in final grid: {}'.format(num_cols))

# opens output csv file
with open(out_file, 'w') as output:
    writer = csv.writer(output)
    # writes header row
    writer.writerow(out_header)
    # counter for trajectories
    i = 0
    # discretize each trajectory now that boundaries of grid are known
    for mmsi, trajectory in trajectories.items():
        print('trajectory for {}: {}'.format(mmsi, trajectory))
        cur_state = -1
        for coords in trajectory:
            cur_lat = coords[0]
            cur_lon = coords[1]
            # gets discretized state based on current coordinates, the upper left bound of the grid,
            # the number of columns, and the grid unit length
            prev_state = cur_state
            cur_state = get_state(cur_lat, cur_lon, min_lat, min_lon, num_cols, grid_len)
            if (prev_state != -1):  # if there is a valid previous state, write a line of the csv
                # infers action, implying that the system is deterministic
                cur_action = get_action(prev_state, cur_state, num_cols)
                # writes SAS line of csv
                writer.writerow([i, prev_state, cur_action, cur_state])
                print('traj: {}, prev: {}, action: {}, cur: {}'.format(i, prev_state, cur_action, cur_state))
        i += 1  # increment i for each trajectory

# TODO: visualize resulting trajectories on matplotlib

# TODO: convert each step of this process to a Jupyter notebook