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
- ``get_raw.sh`` - run this file first to download and unzip the dataset. A command line argument may be used to specify the year, month, and zone, or without a command line argument, all files within the year, month, and zone ranges will be downloaded, according to the boundaries specified in the file. Read the top of the file for more details on what each parameter does.
- ``process_ais_data.py`` - once ``get_raw.sh`` has finished downloading and unzipping the desired files, ``process_ais_data.py`` processes all the desired csv files to condense them into a final sequence file that can be used as an input to algorithms. ``process_ais_data.py`` has flexibility in how it pre-processes the data, which is described in ``config.yaml``. The coordinate grid can be bounded, certain time and zone ranges can be specified, and more. See ``config.yaml`` and ``process_ais_data.py`` for more details on what all the options and functionality are.
- ``AIS_demo_data.ipynb`` - once ``get_raw.sh`` and ``process_ais_data.py`` have been run as desired, this Jupyter Notebook uses pandas and plotly to map trajectories on an interactive map to demonstrate how the pipeline has processed the data. If you are unfamiliar with Jupyter notebooks, run ``jupyter notebook`` and select this file to run it interactively.

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
