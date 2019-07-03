# AIS-Vessel-Data
Preprocessing data based on https://marinecadastre.gov/ais/

The csv files obtained have the following data available:
- MMSI - Maritime Mobile Service Identity value (integer as text)
- BaseDateTime - Full UTC date and time (YYYY-MM-DDTHH:MM:SS)
- LAT - Latitude (decimal degrees as double)
- LON - Longitude (decimal degrees as double)
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