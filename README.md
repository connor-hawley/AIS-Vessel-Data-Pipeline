# AIS-Vessel-Data
Preprocessing data based on https://marinecadastre.gov/ais/

## Description
This repository is dedicated to downloading, extracting, and preprocessing the Coast Guard AIS dataset for use in machine learning algorithms. Data are available for all months of the years 2015 - 2017, and for UTM zones 1 - 20.

# Getting Started
This guide assumes that you have installed python 3.x on your machine, preferably python 3.7 and above.
## Option 1: Pipenv
This repository is intended to be run using ``pipenv`` to manage package dependencies. 

If you do not have ``pipenv`` installed, try calling <br/><br/>
``pip install pipenv``

If you have ``pip`` installed, or install it using your OS package manager (details: https://github.com/pypa/pipenv). Once ``pipenv`` has been installed, run the following commands from the repository home directory, unless you have an environment that runs python 3.7 already, in which case just activate that environment and skip this command. <br/><br/>
``pipenv --python 3.7``

Once an environment running python 3.7 is available and pipenv is installed in that environment, just run this command to install all dependencies. <br/><br/>
``pipenv install``

If the above command runs successfully, you should be ready to run the programs in the worflow.

## Option 2: Pip
If you have pip installed and can easily run python 3, then installing required packages with requirements.txt should work okay. <br/><br/>
``pip install -r requirements.txt``

If the above command runs successfully, you should be ready to run the programs in the worflow.

# Workflow
- ``get_raw.sh`` - run this file first to download and unzip the dataset. A command line argument may be used to specify the year, month, and zone, or without a command line argument, all files within the year, month, and zone ranges will be downloaded, according to the boundaries specified in the file. Optionally, the output directory path can be specified as another command line argument, either by itself or preceding the year, month, and zone arguments. Read the top of the file for more details on what each parameter does.
- ``process_ais_data.py`` - once ``get_raw.sh`` has finished downloading and unzipping the desired files, ``process_ais_data.py`` processes all the desired csv files to condense them into a final sequence file that can be used as an input to algorithms. ``process_ais_data.py`` has flexibility in how it pre-processes the data, which is described in ``config.yaml``. The coordinate grid can be bounded, certain time and zone ranges can be specified, and more. See ``config.yaml`` and ``process_ais_data.py`` for more details on what all the options and functionality are.
- ``AIS_demo_data.ipynb`` - once ``get_raw.sh`` and ``process_ais_data.py`` have been run as desired, this Jupyter Notebook uses pandas and plotly to map trajectories on an interactive map to demonstrate how the pipeline has processed the data. If you are unfamiliar with Jupyter notebooks, run ``jupyter notebook`` and select this file to run it interactively.

## Workflow options
### ``get_raw.sh``
- ``DELETE_ZIPPED`` - specify whether or not to delete zipped files that are downloaded during execution.
- ``CLEAR_BEFORE_DOWNLOAD`` - specify whether or not to clear files already extracted before downloading new ones.
- ``YEAR_BEGIN``, ``MONTH_BEGIN`` - the earliest data to download, inclusive. e.g. ``YEAR_BEGIN=2016, MONTH_BEGIN=3`` would download files beginning with March 2016.
- ``YEAR_END``, ``MONTH_END`` - the latest data to download, inclusive. e.g. ``YEAR_END=2016, MONTH_END=3`` would download files ending with March 2016.
- ``ZONE_BEGIN``, ``ZONE_END`` - the zone range to download (inclusive). Zone description: 1 - 9 -> Alaska, 4 - 5 -> Hawaii, 9 - 20 -> continental US. See ``get_raw.sh`` for more information.
- ``OUTPUT_DIR`` - the directory where the downloaded files should live once the script completes. The output files will be in the folder ``AIS_ASCII_BY_UTM_Month`` in the specified directory.

### ``process_ais_data.py``
All options for this file are specified in ``config.yaml``, not the file itself.
#### ``options``
The main options that can be specified for script.
- ``limit_rows`` - specifies whether to only read the first ``max_rows`` of each csv.
- ``max_rows`` - when ``limit_rows`` is true, specifies the number of rows to read of each CSV file.
- ``bound_lon`` - specifies whether to use specified hard longitude boundaries instead of inferring them. Boundaries are read from ``grid_params``.
- ``bound_lat`` - specifies whether to use specified hard latitude boundaries instead of inferring them. Boundaries are read from ``grid_params``.
- ``bound_time`` - specifies whether to bound the times considered. Boundaries are read from ``meta_params``.
- ``bound_zone`` - specifies whether to bound the zones being read. Boundaries are read from ``meta_params``.
- ``interp_actions`` - specifies whether to interpolate actions if state transitions are not adjacent, otherwise actions can be arbitrarily large.
- ``allow_diag`` - when ``interp_actions`` is true, specifies whether to allow for diagonal grid actions.
- ``append_coords`` - specifies whether to add raw latitude, longitude values as columns to the output csv. This will also add an extra row to each trajectory containing just the final state and its original coordinates. When interpolating, the coordinates of the interpolated states will just be the center of the grid squares they represent.
- ``prec_coords`` - specifies the precision of coordinates in output as the number of decimal places to round each coordinate to.
- ``min_states`` - specifies the minimum number of sequentially unique discretized states needed to qualify a trajectory for final output, e.g. if ``min_states=3`` then the state trajectory ``1, 2, 1`` would qualify whereas ``1, 1, 2`` would not. In other words, the minimum number of states in a trajectory that were not reached via self-transition.
#### ``directories``
The input and output directory specification for the script.
- ``in_dir_path`` - specifies the directory where input data is located.
- ``in_dir_data`` - specifies the folder name containing all the data in the input directory.
- ``out_dir_path`` - specifies the directory where output data files should be written.
- ``out_dir_file`` - specifies output file name (should be .csv).
#### ``meta_params`` 
Specifies the same time and zone boundary controls available in ``get_raw.sh``, only considering files within those boundaries. Data are available between 2015 - 2017, January - December, zones 1 - 20.
####``grid_params``
When hard boundaries are set in ``options``, those grid boundaries are specified here, except ``grid_len``, which matters regardless.
- ``grid_len`` - the length of one side of one grid square, in degrees.

## Workflow example
### Getting the data
To get the data, we use ``get_raw.sh``. Let's assume that we want all the data in zone 10 between November 2016 and January 2017 in a file that already exists in our working directory called ``data``. We have 4 options for how to do this:

Option 1: specify everything in command line: <br/>
``./get_raw.sh data 2016 11 10; ./get_raw.sh data 2016 12 10; ./get_raw.sh data 2017 1 10`` <br/><br/>
Option 2: specify files in command line but specify output directory using ``OUTPUT_DIR=data`` in the file: <br/>
``./get_raw.sh 2016 11 10; ./get_raw.sh 2016 12 10; ./get_raw.sh 2017 1 10`` <br/><br/>
Option 3 specify output directory in command line but specify files using ``BEGIN_{YEAR=2016, MONTH=11, ZONE=10}, END_{YEAR=2017, MONTH=1, ZONE=10}`` in the file: <br/>
``./get_raw.sh data 2016 11 10; ./get_raw.sh data 2016 12 10; ./get_raw.sh data 2017 1 10`` <br/><br/>
Option 4: specify everything in the file, combining options 2 and 3: <br/>
``./get_raw.sh`` <br/><br/>

Once the data finishes downloading and inflating, we are ready to preprocess the data.

### Preprocessing the data
To preprocess the data, we use ``process_ais_data.py``. To use the script, ``config.yaml`` should be configured first.<br/><br/>

First, because we put our data in the ``data`` folder in our current directory, we need to change ``directories:in_dir_path``  to ``./data`` to reflect this.<br/><br/>

We'd like to make use of all the data we just downloaded, so we should read the whole file for each csv and set ``options: limit_rows`` to ``False``.<br/><br/>

Next, because one longitudinal zone is a much smaller range than its latitude range, we would like to bound the latitude we consider by setting ``options:bound_lat`` to ``True`` and then setting our ``min_lat`` and ``max_lat`` to our desired values. Values between 35 N  and 45 N latitude seem like reasonable values, so we'll set ``min_lat : 35.0`` and ``max_lat : 45.0``.<br/><br/>

We'd also like to make use of all the data we just downloaded, so we need to set the ``meta_params`` accordingly to consider the right data when preprocessing. Assuming ``options: bound_time`` is ``True``, we'll need to set ``meta_params: min_year=2016, min_month=11, max_year=2017, max_month=1`` to consider data in the time period we just downloaded. Assuming ``options: bound_zone`` is ``True``, we'll need to set ``meta_params: min_zone: 10, max_zone: 10`` to consider data in the zone we just downloaded. If any of ``options: bound_time, bound_zone`` is ``False``, then their corresponding ``meta_params`` won't be evaluated.<br/><br/>

For interpolating actions, we'd like to limit the actions to just up, down, left, right, and none so we will set ``options: interp_actions`` to ``True``, and ``options: allow_diag`` to ``False``.<br/><br/>

Since we'd like to get a ``csv`` with just the ``id-state-action-state`` entries for each row, we will set ``options: append_coords`` to ``False``. If we had instead set this to ``True``, then the output would have two extra columns specifying the longitude and latitude for each state in each row (just the first state in the row), and an extra row would be appended to each trajectory with just the last state and its coordinates for easier plotting. If actions are being interpolated, then the latitude and longitude will be written as the middle coordinates of the corresponding interpolated state.<br/><br/>

For our purposes, let's assume that 3 decimal places of precision are sufficient for our coordinates, so we'll set ``options: prec_coords=3``.<br/><br/>

Lastly, since we'd like the final grid to have a manageable number of states (< 1000), we will size the grid accordingly. The one zone we downloaded (10) has a width of 6 degrees longitude, and we specified the latitude boundaries to be between 35 and 45 degrees north, so now if we choose ``grid_params: grid_len=0.5``, then we will have ``6/.5 = 12`` columns and ``10/0.5 = 20`` rows in our final grid, resulting in a grand total of 240 states in our final grid.<br/><br/>

Now that our script is configured to our liking, we are finally ready to just run the script:<br/>
``python process_ais_data.py``<br/><br/>

Once the script finishes (hopefully without error), the output csv will be in the current directory as ``ais_data_output.csv`` and ready for further processing.

# Input Output Specification

## Dataset csv file columns detail
The csv files obtained have the following data available:
- **MMSI** - Maritime Mobile Service Identity value (integer as text)
- **BaseDateTime** - Full UTC date and time (YYYY-MM-DDTHH:MM:SS)
- **LAT** - Latitude (decimal degrees as double)
- **LON** - Longitude (decimal degrees as double)
- SOG - Speed Over Ground (knots as float)
- COG - Course Over Ground (degrees as float)
- Heading - True heading angle (degrees as float)
- VesselName - Name as shown on the station radio license (text)
- IMO - International Maritime Organization Vessel number (text)
- CallSign - Call sign as assigned by FCC (text)
- VesselType - Vessel type as defined in NAIS specifications (int)
- Status - Navigation status as defined by the COLREGS (text)
- Length - Length of vessel (see NAIS specifications) (meters as float)
- Width - Width of vesses (see NAIS specifications) (meters as float)
- Draft - Draft depth of vessel (see NAIS specification and codes) (meters as float)
- Cargo - Cargo type (SEE NAIS specification and codes) (text)
- TransceiverClass - Class of AIS transceiver (text) (unavailable in 2017 dataset)

This preprocessing program only makes use of the bolded columns above. MMSI maps to ``sequence_id``, and (LAT, LON) tuples map to ``state_id``s. ``action_id`` is inferred by looking at sequential ``state_id``s when data are sorted by BaseDateTime.

## Output csv file columns detail
- ``sequence_id`` - the unique identifier of the ship, represented as integers ascending from 0, an alias for MMSI
- ``from_state_id`` - the coordinate grid square the ship started in for a given transition, represented as an integer
- ``action_id`` - the direction and length a ship went to transition between states, represented as an integer. See ``process_ais_data.py`` for more detail
- ``to_state_id`` - the coordinate grid square the ship ended in for a given transition, represented as an integer
