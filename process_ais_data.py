# IMPORTANT: run ./get_raw.sh with desired parameters to obtain the actual CSVs
# on your local machine before running this file
import os
import csv
import math
import datetime
import plotly.plotly as py
import plotly.graph_objs as go

import pandas as pd


# set number of rows to read of each CSV file since reading > 3 GB is going to take forever
MAX_ROWS = 100000
# set minimum number of states in a trajectory necessary to qualify it for the output file
MIN_STATES = 2
# sets the side length of the square being used to discretize the grid, in degrees
grid_len = 0.5
# specifies output file name (should be .csv)
out_file = 'ais_data_output.csv'
# specifies header row of output csv file
out_header = ['sequence_id', 'from_state_id', 'action_id', 'to_state_id']
# specifies output file for metadata
out_meta = 'ais_meta_output.csv'
# specifies the metadata that will be entered as one row
out_meta_header = ['grid_len', 'num_cols', 'min_lat', 'max_lat', 'min_lon', 'max_lon']

# row indices to be accessed later in case other data does not have same row order
ind_mmsi = 0
ind_time = 1
ind_lat = 2
ind_lon = 3


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


def get_time(time_str):
    # uses the datetime library to calculate a timestamp and returns it
    date, time = time_str.split('T')
    year, month, day = date.split('-')
    hour, minute, second = time.split(':')
    dt = datetime.datetime(int(year), int(month), int(day), hour=int(hour), minute=int(minute), second=int(second),
                           tzinfo=datetime.timezone.utc)
    return dt.timestamp()


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
        # print('x: {}, y: {}, action_num: {}'.format(x, y, action_num))

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
# keeps record of which csv files were processed
csv_file_meta = []
# min_lat and min_lon will keep track of the maximum and minimum longitudes in the dataset over all csvs
min_lat = 90
max_lat = -90
# these lists will keep track of minimum and maximum longitudes for all the zones seen
# minimum of minimum longitudes and maximum of maximum longitudes will be used for final grid
min_lon = 180
max_lon = -180

# iterate through each csv_file to build trajectories
for csv_file in csv_files:
    print('reading csv file: {}'.format(csv_file))
    year, month, zone = get_meta_data(csv_file)  # finds the data year, month, and zone based on the file name
    print('year: {}, month: {}, zone: {}'.format(year, month, zone))
    csv_file_meta.append([year, month, zone])  # not currently used, but might be useful later
    # min_lon, max_lon = get_bounds(zone)  # finds longitude boundaries based on the zone number
    with open(csv_file, 'r') as fh:  # boilerplate to read in csv file
        reader = csv.reader(fh)
        header = next(reader)  # retrieves header of csv
        print('csv header: {}'.format(header))
        for i in range(MAX_ROWS):
            try:
                row = next(reader)  # get new row of the data
            except StopIteration:
                break
        # for row in reader:  # placeholder for complete code
            mmsi = row[ind_mmsi]  # gets current id, latitude, and longitude of column
            cur_lat = float(row[ind_lat])
            cur_lon = float(row[ind_lon])
            cur_sec = get_time(row[ind_time])
            if not (mmsi in trajectories):  # create new trajectory for unseen mmsi
                trajectories[mmsi] = []
            trajectories[mmsi].append([cur_lat, cur_lon, cur_sec])  # add state to mmsi's trajectory
            # finds minimum and maximum latitudes and longitudes in dataset for later grid sizing
            if cur_lat > max_lat:
                max_lat = cur_lat
            elif cur_lat < min_lat:
                min_lat = cur_lat
            if cur_lon > max_lon:
                max_lon = cur_lon
            if cur_lon < min_lon:
                min_lon = cur_lon

# changes grid boundaries to provide some padding to each boundary, rounded to nearest degree
min_lat = float(math.floor(min_lat))
max_lat = float(math.ceil(max_lat))
min_lon = float(math.floor(min_lon))
max_lon = float(math.ceil(max_lon))

# latitude and longitude boundaries for final grid
print('minimum longitude: {}, maximum longitude: {}'.format(min_lon, max_lon))
print('minimum latitude: {}, maximum latitude: {}'.format(min_lat, max_lat))

num_cols = math.ceil((max_lon - min_lon)/grid_len)  # number of columns in the resulting grid
print('number of columns in final grid: {}'.format(num_cols))

# keeps track of time differences in seconds
d_time = []

# opens output csv file
with open(out_file, 'w') as output:
    writer = csv.writer(output)
    # writes header row
    writer.writerow(out_header)
    # counter for trajectories
    i = 0
    # discretize each trajectory now that boundaries of grid are known
    for mmsi, trajectory in trajectories.items():
        # checks that trajectory contains more than one entry (otherwise is not trajectory)
        if len(trajectory) < MIN_STATES:
            continue
        print('trajectory for {}: {} states'.format(mmsi, len(trajectory)))
        # sorts trajectory based on timestamp - looks like timestamps are out of order
        trajectory.sort(key=lambda x: x[2])
        cur_state = -1
        cur_time = -1
        has_action = False  # will become true if there is at least one transition with non-zero action
        for coords in trajectory:
            cur_lat = coords[0]
            cur_lon = coords[1]
            # just for time
            prev_time = cur_time
            cur_time = coords[2]
            # gets discretized state based on current coordinates, the upper left bound of the grid,
            # the number of columns, and the grid unit length
            prev_state = cur_state
            cur_state = get_state(cur_lat, cur_lon, min_lat, min_lon, num_cols, grid_len)
            if prev_state != -1:  # if there is a valid previous state, write a line of the csv
                # infers action, implying that the system is deterministic
                cur_action = get_action(prev_state, cur_state, num_cols)
                # writes SAS line of csv if the action is nonzero
                if cur_action != 0:
                    writer.writerow([i, prev_state, cur_action, cur_state])
                    # print('traj: {}, prev: {}, action: {}, cur: {}'.format(i, prev_state, cur_action, cur_state))
                    # logs time difference between states
                    if prev_time != -1:
                        d_time.append(cur_time - prev_time)
                        if not has_action:  # the trajectory has at least one transition, so become true
                            has_action = True
        if has_action:
            i += 1  # increment i for each trajectory that has at least 1 non-self transition

out_meta_data = [grid_len, num_cols, min_lat, max_lat, min_lon, max_lon]
with open(out_meta, 'w') as output:
    writer = csv.writer(output)
    # writes header row for metadata file
    writer.writerow(out_meta_header)
    # writes metadata row
    writer.writerow(out_meta_data)

