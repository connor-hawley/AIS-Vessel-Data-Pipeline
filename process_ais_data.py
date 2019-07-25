"""Preprocesses AIS data.

To obtain the needed AIS data, see (and run) ``get_raw.sh``.

Uses information specified in the ``config_file`` to chew through available AIS csv data to generate an output csv file
with the discretized states, inferred actions, and records the resulting grid parameters in the ``meta_file``.
"""
import yaml
import os
import csv
import math
import datetime
import numpy as np


def main():
    """Driver code to run the big steps of pre-processing the data.

    First, all the script parameters are loaded by reading the ``.yaml`` ``config_file`` and this config is unpacked.
    All the csv files within a specified directory are found and returned as ``csv_files``, along with each file's
    year, month, and zone in ``all_files_meta``. Then, these csv files are read and organized into a large
    set of trajectories ordered by id (mmsi). Finally, these trajectories are discretized before being written into
    an output csv containing only rows of id-state-action-state transitions. Another yaml file is written to
    ``meta_file`` to specify the final grid parameters, output directories, and the year, month, and zone of
    all the files read in.
    """
    # file containing important options, directories, parameters, etc.
    config_file = 'config.yaml'

    # file to access final grid_params and the csv files' respective years, months, and zones
    meta_file = 'meta_data.yaml'

    # gets the config dictionary and unpacks it
    config = get_config(config_file)
    options = config['options']
    directories = config['directories']
    csv_indices = config['csv_indices']
    meta_params = config['meta_params']
    grid_params = config['grid_params']

    # gets the csv files available and their metadata
    csv_files, all_files_meta = collect_csv_files(options, directories, meta_params)

    # reads the collected csv files and assembles trajectories
    trajectories, grid_params = read_data(csv_files, options, csv_indices, grid_params)

    # processes (fits to grid) trajectories and writes generates sequences to output file
    write_data(trajectories, options, directories, grid_params)

    # writes file metadata, paths, and grid parameters to ``meta_file``
    directories_out = {'in_dir_path': directories['out_dir_path'], 'in_dir_data': directories['out_dir_file']}
    out_dict = {'all_files_meta': all_files_meta, 'directories': directories_out, 'grid_params': grid_params}
    with open(meta_file, 'w') as outfile:
        yaml.dump(out_dict, outfile, default_flow_style=False)


def get_config(config_file):
    """Helper function to get dictionary of script parameters.

    Mostly boilerplate code to read in ``config_file`` as a ``.yaml`` file that specifies important script parameters.
    Upon success, this config dictionary is returned to main to be unpacked.

    Args:
        config_file: The name of the ``.yaml`` file containing the script configuration parameters, located in the
            directory the script is run.

    Returns:
        A dictionary of script configuration parameters.
    """
    with open(config_file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def collect_csv_files(options, directories, meta_params):
    """Traverses the directory containing the decompressed AIS data to get the CSV names for further processing.

    Uses the os library to find all csv files within the directory defined by ``directories``, populating the
    ``csv_files`` list for later reading of all valid csvs found and logging file metadata in ``all_files_meta``.

    Args:
        options: the options specified by the user in ``config_file`` on how to run the script.
        directories: The directories specified by the user in ``config_file`` on where to look for input data, where to
            write output data, and what those files should be named.
        meta_params: The parameters specified by the user in ``config_file`` to define time and zone range for the
            AIS data.

    Returns:
        csv_files: A list of paths to all valid csv files found.
        all_files_meta: A dictionary listing the year, month, and zone corresponding to each csv file's data.
    """
    # initialize a list that will be filled with all csv file names from root
    csv_files = []
    all_files_meta = {}
    for root, dirs, files in os.walk(directories['in_dir_path'] + directories['in_dir_data']):
        for file in files:
            if file.endswith(".csv"):
                year, month, zone = get_meta_data(file)  # finds the data year, month, and zone based on the file name
                # only considers valid years and months if time is bounded and valid zones if zones are bounded
                if (not options['bound_time'] or (meta_params['min_year'] <= year <= meta_params['max_year'])) and \
                   (not options['bound_zone'] or (meta_params['min_zone'] <= zone <= meta_params['max_zone'])):
                    if (not options['bound_time'] or (not year == meta_params['min_year'] or month >= meta_params['min_month'])) and \
                       (not options['bound_time'] or (not year == meta_params['max_year'] or month <= meta_params['max_month'])):
                        # csv_files will contain file locations relative to current directory
                        csv_files.append(os.path.join(root, file))
                        # create dictionary to describe file characteristics
                        file_meta = {'year': year, 'month': month, 'zone': zone}
                        all_files_meta[file] = file_meta
    return csv_files, all_files_meta


def read_data(csv_files, options, csv_indices, grid_params):
    """Iterate through each csv file to segregate each trajectory by its mmsi id.

    Reads each csv in ``csv_files`` to obtain coordinates and timestamp series associated with each mmsi id encountered.
    Optionally, the boundaries of the grid later specified can be inferred by calculating the minimum and maximum
    longitudes and latitudes by setting ``options['bound_lon']`` and ``options['bound_lat']`` to False, respectively
    in the ``config_file``. It can also be specified to only read the first ``options['MAX_ROWS']`` of each csv file by
    setting ``options['limit_rows']`` to True in the ``config_file``.

    Args:
        csv_files: A list of paths to all valid csv files found.
        options: The options specified by the user in ``config_file`` on how to run the script.
        csv_indices: AIS csv file row lookup indices for input data of interest.
        grid_params: Specifies the minimum and maximum latitudes and longitudes in the dataset. Will be updated to fit
            dataset if ``options['bound_lon']`` or ``options['bount_lat']`` is False in the ``config_file``.

    Returns:
        trajectories: A dictionary mapping mmsi ids to lists of coordinate-timestamp triplets.
        grid_params: Specifies the minimum and maximum latitudes and longitudes in the dataset. Will be updated to fit
            dataset if ``options['bound_lon']`` or ``options['bount_lat']`` is False in the ``config_file``.
    """
    # overwrite hard boundaries on longitude and latitude if not bounded in config.yaml
    if not options['bound_lon']:
        grid_params['min_lon'] = 180
        grid_params['max_lon'] = -180
    if not options['bound_lat']:
        grid_params['min_lat'] = 90
        grid_params['max_lat'] = -90

    # initialize dictionary that will be filled with all trajectories
    trajectories = {}
    for csv_file in csv_files:
        with open(csv_file, 'r') as fh:  # boilerplate to read in csv file
            reader = csv.reader(fh)
            next(reader)  # discards header of csv
            for i, row in enumerate(reader):
                # only reads first MAX_ROWS if limit_rows is true
                if options['limit_rows'] and i >= options['MAX_ROWS']:
                    break

                # gets current id, time, longitude, and latitude of column
                mmsi = row[csv_indices['mmsi']]
                cur_sec = get_time(row[csv_indices['time']])
                cur_lon = float(row[csv_indices['lon']])
                cur_lat = float(row[csv_indices['lat']])

                # create new trajectory for unseen mmsi
                if not (mmsi in trajectories):
                    trajectories[mmsi] = []

                # only adds to trajectory if (bound_lat => in lat bounds) and (bound_lon => in lon bounds)
                if (not options['bound_lon'] or (grid_params['min_lon'] <= cur_lon <= grid_params['max_lon'])) and \
                        (not options['bound_lat'] or (grid_params['min_lat']) <= cur_lat <= grid_params['max_lat']):
                    trajectories[mmsi].append([cur_lon, cur_lat, cur_sec])

                # finds minimum and maximum latitudes and longitudes in dataset for later grid sizing
                if not options['bound_lon'] and cur_lon < grid_params['min_lon']:
                    grid_params['min_lon'] = cur_lon
                if not options['bound_lon'] and cur_lon > grid_params['max_lon']:
                    grid_params['max_lon'] = cur_lon
                if not options['bound_lat'] and cur_lat < grid_params['min_lat']:
                    grid_params['min_lat'] = cur_lat
                if not options['bound_lat'] and cur_lat > grid_params['max_lat']:
                    grid_params['max_lat'] = cur_lat

    # changes grid boundaries to provide some padding to each boundary, rounded to nearest degree
    if not options['bound_lon']:
        grid_params['min_lon'] = float(math.floor(grid_params['min_lon']))
        grid_params['max_lon'] = float(math.ceil(grid_params['max_lon']))
    if not options['bound_lat']:
        grid_params['min_lat'] = float(math.floor(grid_params['min_lat']))
        grid_params['max_lat'] = float(math.ceil(grid_params['max_lat']))
    # number of columns in the resulting grid
    grid_params['num_cols'] = math.ceil((grid_params['max_lon'] - grid_params['min_lon']) / grid_params['grid_len'])

    return trajectories, grid_params


def write_data(trajectories, options, directories, grid_params):
    """Writes all trajectories to an output csv file using a discretized state and action grid.

    Uses the trajectories variable to look at each id-state-action-state transition to discretize all states and to
    interpolate actions if specified. These discretized states with interpolated or arbitrary actions are then written
    to the output csv specified by ``options['out_dir'] + options['out_file']``. Each trajectory is also sorted by
    its timestamp.

    The trajectories have their ids aliased by ``i``, a counter variable that only increments whenever a trajectory is
    going to appear in the final csv. Self-transitions are discarded, and because of the huge grid size, most
    trajectories will be discarded since they will never transition between grid squares.

    Args:
        trajectories: A dictionary mapping mmsi ids to lists of coordinate-timestamp triplets.
        options: The options specified by the user in ``config_file`` on how to run the script.
        directories: The directories specified by the user in ``config_file`` on where to look for input data, where to
            write output data, and what those files should be named.
        grid_params: Specifies the minimum and maximum latitudes and longitudes in the dataset.
    """
    # opens output csv file
    with open(directories['out_dir_path'] + directories['out_dir_file'], 'w') as output:
        writer = csv.writer(output)
        # writes header row
        writer.writerow(['sequence_id', 'from_state_id', 'action_id', 'to_state_id'])
        # counter for trajectories
        i = 0
        # discretize each trajectory now that boundaries of grid are known
        for mmsi, trajectory in trajectories.items():
            # checks that trajectory contains more than one entry (otherwise is not trajectory)
            if len(trajectory) < options['MIN_STATES']:
                continue

            # sorts trajectory based on timestamp - looks like timestamps are out of order
            trajectory.sort(key=lambda x: x[2])
            cur_state = -1
            cur_time = -1
            has_action = False  # will become true if there is at least one transition with non-zero action

            for coords in trajectory:
                # gets discretized state based on current coordinates, the bottom left bound of the grid,
                # the number of columns, and the grid unit length
                cur_lon = coords[0]
                cur_lat = coords[1]
                prev_time = cur_time
                cur_time = coords[2]
                prev_state = cur_state
                cur_state = get_state(cur_lon, cur_lat, grid_params)

                # only considers valid non-self transitions
                if prev_state != -1 and prev_state != cur_state:
                    quads = get_action(i, prev_state, cur_state, grid_params['num_cols'], options)
                    for isas in quads:
                        writer.writerow(isas)
                    if not has_action:  # the trajectory has at least one transition, so become true
                        has_action = True
            if has_action:
                i += 1  # increment i for each trajectory that has at least 1 non-self transition


def get_bounds(zone):
    """Helper function to get longitude boundaries corresponding to zone.

    Calculates the minimum and maximum longitudes corresponding to an integer zone
    representing a Universal Transverse Mercator coordinate system zone. Each zone is
    6 degrees wide, dividing the Earth into 60 zones, starting with zone 1 at 180 deg W. This function
    also wraps the zone with a modulo operator, so zone -1 would map to zone 58.

    Args:
        zone: An integer representing the Universal Transverse Mercator coordinate system zone.

    Returns:
        A tuple ``(min_lon, max_lon)`` of floats corresponding to the minimum and maximum longitudes
        of the zone passed in.
    """
    min_lon = (6. * ((zone - 1) % 60)) - 180.  # counts 6 degrees per zone, offset by -180
    return min_lon, (min_lon + 6.)


def get_meta_data(file_name):
    """Helper function to retrieve a given file name's year, month, and zone.

    Takes a string file_name formatted as ``'AIS_yyyy_mm_Zone##.csv'`` and returns the numerical
    values of ``yyyy, mm, ##`` corresponding to year, month, and zone number as a tuple.

    Args:
        file_name: a string formatted as ``'AIS_yyyy_mm_Zone##.csv'``.

    Returns:
        A tuple ``(year, month, zone)`` of integers corresponding the year, month, and zone of the file passed in.
    """
    meta_file_data = file_name.split('_')  # splits csv file on '_' character, which separates relevant file info
    year = int(meta_file_data[-3])  # third to last element of file is the year
    month = int(meta_file_data[-2])  # second to last element of file is the month

    # get zone number for csv file being read
    ending_raw = meta_file_data[-1]  # gets last part of the file, with format "ZoneXX.csv"
    ending_data = ending_raw.split('.')  # splits last part of file on '.' character
    zone_raw = ending_data[0]  # gets "ZoneXX" string
    zone_data = zone_raw[-2:]  # gets last 2 characters of "ZoneXX" string - will be the zone number
    zone = int(zone_data)
    return year, month, zone


def get_time(time_str):
    """Uses the datetime library to calculate a timestamp object from a ``time_str``.

    Takes in a timestamp string, breaks it down into its components, and then calls the datetime library
    to construct a datetime object for easier manipulation and time calculations between data entries.

    Args:
        time_str: A timestamp string formatted as 'YYYY-MM-DDTHH:MM:SS'.

    Returns:
        A timestamp object corresponding exactly to the timestamp string passed in.
    """
    date, time = time_str.split('T')
    year, month, day = date.split('-')
    hour, minute, second = time.split(':')
    dt = datetime.datetime(int(year), int(month), int(day), hour=int(hour), minute=int(minute), second=int(second))
    return dt.timestamp()


def get_state(cur_lon, cur_lat, grid_params):
    """Discretizes a coordinate pair into its state space representation in a Euclidean grid.

    Takes in a coordinate pair ``cur_lon, cur_lat`` and grid parameters ``min_lon, min_lat, num_cols, grid_len``
    to calculate the integer state representing the given coordinate pair. This coordinate grid is always row-major.
    ``min_lon, min_lat`` represent the bottom-left corner of the grid.

    For example, a 3 x 4 grid would have the following state enumeration pattern:

    8 9 10 11      (min_lon, min_lat + grid_len)              (min_lon + grid_len, min_lat + grid_len)
    4 5 6 7                        |
    0 1 2 3              (min_lon, min_lat) ---------------------- (min_lon + grid_len, min_lon)

    In this example, the top left of state 0's boundaries would be the point ``min_lon, min_lat``, and the total area
    mapping to state 0 would be the square with ``min_lon, min_lat`` as the top left corner and each side of the
    square with length ``grid_len``. The inclusive parts of the square's boundaries mapping to zero are solid lines.

    Args:
        cur_lon: the longitude of the data point represented as a float.
        cur_lat: the latitude of the data point represented as a float.
        grid_params: Specifies the minimum and maximum latitudes and longitudes in the dataset.

    Returns:
        An integer state corresponding to the discretized representation of cur_lon, cur_lat according to the
        grid parameters passed in.
    """
    # normalize lat and lon to the minimum values
    cur_lon -= grid_params['min_lon']
    cur_lat -= grid_params['min_lat']
    # find the row and column position based on grid_len
    col = cur_lon // grid_params['grid_len']
    row = cur_lat // grid_params['grid_len']
    # find total state based on num_cols in final grid
    return int(row * grid_params['num_cols'] + col)


def get_action(traj_num, prev_state, cur_state, num_cols, options):
    """Wrapper function for other ``get_action`` functions.

    Calls the correct ``get_action`` variant based on the options input and returns the resulting output.

    Args:
        traj_num: the trajectory id number represented as an integer.
        prev_state: the state that preceded the current state represented as an integer.
        cur_state: the state that the system is currently in represented as an integer.
        num_cols: the number of columns in each row on the grid represented as an integer.
        options: The options specified by the user in ``config_file`` on how to run the script.

    Returns:
        A list of id-state-action-state transitions that interpolate between ``prev_state`` and ``cur_state``.
    """
    if not options['interp_actions']:
        return get_action_arb(traj_num, prev_state, cur_state, num_cols)
    if options['allow_diag']:
        return get_action_interp_with_diag(traj_num, prev_state, cur_state, num_cols)
    return get_action_interp_reg(traj_num, prev_state, cur_state, num_cols)


def get_action_arb(traj_num, prev_state, cur_state, num_cols):
    """Calculates an arbitrary action from the previous state to current state relative to the previous state.

    First, the relative offset between the current and previous state in rows and columns is calculated.
    The action is then calculated according to a spiral rule beginning with the previous state, so self-transitions
    are defined as 0 as an initial condition. Spiral inspired by the polar function r = theta.

    For example, if ``prev_state = 5``, ``cur_state = 7``, and ``num_cols = 4``, then our state grid is populated
    as follows:

    8  9 10 11
    4  p  6  c
    0  1  2  3

    Where p represents the location of the previous state, and c represents the location of the current state.
    Then the current state's position relative to the previous state is ``rel_row = 0``, ``rel_col = 2``. Our action
    spiral then looks like this:

    15 14 13 12 11      15 14 13 12 11
    16  4  3  2 10      16  4  3  2 10
    17  5  0  1  9  ->  17  5  p  1  c
    18  6  7  8 24      18  6  7  8 24
    19 20 21 22 23      19 20 21 22 23

    Thus, this algorithm will return 9 as the action.

    Args:
        traj_num: the trajectory id number represented as an integer.
        prev_state: the state that preceded the current state represented as an integer.
        cur_state: the state that the system is currently in represented as an integer.
        num_cols: the number of columns in each row on the grid represented as an integer.

    Returns:
        A list of id-state-action-state transitions that interpolate between ``prev_state`` and ``cur_state``.
    """
    # gets row, column decomposition for previous and current states
    prev_row = prev_state // num_cols
    prev_col = prev_state % num_cols
    cur_row = cur_state // num_cols
    cur_col = cur_state % num_cols
    # calculates current state's position relative to previous state
    rel_row = cur_row - prev_row
    rel_col = cur_col - prev_col

    # simple routine to calculate a spiral set of actions
    # the sequence defined by layer corresponds to the total number of grid squares in each spiral layer
    action_num = x = y = i = 0
    layer = (2 * i + 1) ** 2  # sets breakpoint for when to increment i
    while not(x == rel_col and y == rel_row):
        if action_num == layer - 1:
            i += 1  # move to next spiral
            x = i
            layer = (2 * i + 1) ** 2  # calculate breakpoint for next spiral
        elif x == i and y < i:  # traverses from beginning of layer to top right corner
            y += 1
        elif x > -i and y == i:  # traverses from top right to top left corner
            x -= 1
        elif x == -i and y > -i:  # traverses from top left to bottom left corner
            y -= 1
        elif x < i and y == -i:  # traverses from bottom left to bottom right corner
            x += 1
        elif x == i and y < 0:  # traverses from bottom left corner to end of layer
            y += 1
        action_num += 1

    # return output as one id-state-action-state list within another list for compatibility with other methods
    return [[traj_num, prev_state, action_num, cur_state], ]


def get_action_interp_with_diag(traj_num, prev_state, cur_state, num_cols):
    """Calculates the actions taken from the previous state to reach the current state, interpolating if necessary.

        First, the relative offset between the current and previous state in rows and columns is calculated.
        Then the sign of ``rel_row`` and ``rel_col`` are then used to iteratively describe a sequence of actions
        from the previous state to current state, breaking up state transitions with multiple actions if
        the states are not adjacent (including diagonals, resulting in 9 possible actions). This interpolation
        assumes a deterministic system.

        For example, if ``prev_state = 5``, ``cur_state = 7``, and ``num_cols = 4``, then our state grid is populated
        as follows:

        8  9 10 11
        4  p  6  c
        0  1  2  3

        output: ``[]``

        Where p represents the location of the previous state, and c represents the location of the current state.
        Then the current state's position relative to the previous state is ``rel_row = 0``, ``rel_col = 2``. Our
        action spiral then looks like this:

        4  3  2      4  3  2
        5  0  1  ->  5  p  1  c
        7  8  9      6  7  8

        output: ``[[traj_num, prev_state, 1, prev_state + 1]]``

        Because the current state is not adjacent (including diagonals), we interpolate by taking the action that
        brings us closest to the current state: action 1, resulting in a new action spiral and a new previous state.

        4  3  2      4  3  2
        5  0  1  ->  5  p  c
        7  8  9      6  7  8

        output: ``[[traj_num, prev_state, 1, prev_state + 1], [traj_num, prev_state + 1, 1, cur_state]]``

        Now, our new previous state is adjacent to the current state, so we can take action 1, which updates our
        previous state to exactly match the current state, so the algorithm terminates and returns the list of
        state-action-state transitions.

        Args:
            traj_num: the trajectory id number represented as an integer.
            prev_state: the state that preceded the current state represented as an integer.
            cur_state: the state that the system is currently in represented as an integer.
            num_cols: the number of columns in each row on the grid represented as an integer.

        Returns:
            A list of id-state-action-state transitions that interpolate between ``prev_state`` and ``cur_state``.
    """
    # gets row, column decomposition for previous and current states
    prev_row = prev_state // num_cols
    prev_col = prev_state % num_cols
    cur_row = cur_state // num_cols
    cur_col = cur_state % num_cols
    # calculates current state's position relative to previous state
    rel_row = cur_row - prev_row
    rel_col = cur_col - prev_col

    # write output rows until rel_row and rel_col are both zero
    out_rows = []
    while not(rel_row == 0 and rel_col == 0):
        # selects action to minimize rel_row and rel_col
        action = -1
        if rel_row > 0 and rel_col > 0:
            action = 2
        elif rel_row > 0 and rel_col == 0:
            action = 3
        elif rel_row > 0 and rel_col < 0:
            action = 4
        elif rel_row == 0 and rel_col > 0:
            action = 1
        elif rel_row == 0 and rel_col < 0:
            action = 5
        elif rel_row < 0 and rel_col > 0:
            action = 8
        elif rel_row < 0 and rel_col == 0:
            action = 7
        elif rel_row < 0 and rel_col < 0:
            action = 6

        # moves rel_row and rel_col in the opposite directions of their signs
        row_diff = -np.sign(rel_row)
        col_diff = -np.sign(rel_col)

        # updates states and relative row, column based on action selected
        rel_row += row_diff
        rel_col += col_diff
        temp_row = prev_row - row_diff
        temp_col = prev_col - col_diff
        temp_state = temp_row * num_cols + temp_col
        prev_state = prev_row * num_cols + prev_col

        # adds another state-action-state interpolation to the trajectory
        out_rows.append([traj_num, prev_state, action, temp_state])
        prev_row = temp_row
        prev_col = temp_col

    return out_rows


def get_action_interp_reg(traj_num, prev_state, cur_state, num_cols):
    """Calculates the actions taken from the previous state to reach the current state, interpolating if necessary.

        First, the relative offset between the current and previous state in rows and columns is calculated.
        Then the sign of ``rel_row`` and ``rel_col`` are then used to iteratively describe a sequence of actions
        from the previous state to current state, breaking up state transitions with multiple actions if
        the states are not adjacent (only actions are right, left, up, down, and none). This interpolation
        assumes a deterministic system.

        For example, if ``prev_state = 5``, ``cur_state = 7``, and ``num_cols = 4``, then our state grid is populated
        as follows:

        8  9 10 11
        4  p  6  c
        0  1  2  3

        output: ``[]``

        Where p represents the location of the previous state, and c represents the location of the current state.
        Then the current state's position relative to the previous state is ``rel_row = 0``, ``rel_col = 2``. Our action
        spiral then looks like this:

           2            2
        3  0  1  ->  3  p  1  c
           4            4

        output: ``[[traj_num, prev_state, 1, prev_state + 1]]``

        Because the current state is not adjacent, we interpolate by taking the action that brings us closest to
        the current state: action 1, resulting in a new action spiral and a new previous state.

           2            1
        3  0  1  ->  2  p  c
           4            4

        output: ``[[traj_num, prev_state, 1, prev_state + 1], [traj_num, prev_state + 1, 1, cur_state]]``

        Now, our new previous state is adjacent to the current state, so we can take action 1, which updates our
        previous state to exactly match the current state, so the algorithm terminates and returns the list of
        state-action-state transitions.

        Args:
            traj_num: the trajectory id number represented as an integer.
            prev_state: the state that preceded the current state represented as an integer.
            cur_state: the state that the system is currently in represented as an integer.
            num_cols: the number of columns in each row on the grid represented as an integer.

        Returns:
            A list of id-state-action-state transitions that interpolate between ``prev_state`` and ``cur_state``.
    """
    # gets row, column decomposition for previous and current states
    prev_row = prev_state // num_cols
    prev_col = prev_state % num_cols
    cur_row = cur_state // num_cols
    cur_col = cur_state % num_cols
    # calculates current state's position relative to previous state
    rel_row = cur_row - prev_row
    rel_col = cur_col - prev_col

    # write output rows until rel_row and rel_col are both zero
    out_rows = []
    while not(rel_row == 0 and rel_col == 0):
        # selects action to reduce the largest of rel_row and rel_col
        action = -1
        if rel_row > 0 and rel_col > 0:
            action = 2 if rel_row > rel_col else 1
        elif rel_row > 0 and rel_col == 0:
            action = 2
        elif rel_row > 0 and rel_col < 0:
            action = 2 if rel_row > -rel_col else 3
        elif rel_row == 0 and rel_col > 0:
            action = 1
        elif rel_row == 0 and rel_col < 0:
            action = 3
        elif rel_row < 0 and rel_col > 0:
            action = 4 if -rel_row > rel_col else 1
        elif rel_row < 0 and rel_col == 0:
            action = 4
        elif rel_row < 0 and rel_col < 0:
            action = 4 if -rel_row > -rel_col else 3

        # moves rel_row and rel_col in the opposite directions of their signs
        row_diff = -np.sign(rel_row) if (action == 2 or action == 4) else 0
        col_diff = -np.sign(rel_col) if (action == 1 or action == 3) else 0

        # updates states and relative row, column based on action selected
        rel_row += row_diff
        rel_col += col_diff
        temp_row = prev_row - row_diff
        temp_col = prev_col - col_diff
        temp_state = temp_row * num_cols + temp_col
        prev_state = prev_row * num_cols + prev_col

        # adds another state-action-state interpolation to the trajectory
        out_rows.append([traj_num, prev_state, action, temp_state])
        prev_row = temp_row
        prev_col = temp_col

    return out_rows


if __name__ == '__main__':
    main()
