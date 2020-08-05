# COVIDTracker
##### Tools to help generate choropleth maps showing viral progress.
______________________

**Dependencies - please make sure you have the following python packages installed:**
- Regular packages: pandas, os, json, numpy, datetime, sys
- Special packages: requests, folium, selenium (this last may need a separate geckodriver download)

**Please also ensure you have Mozilla Firefox installed.**

The COVIDTracker file reads virus cases and deaths data from *Our World in Data (OWID)* (provided at https://covid.ourworldindata.org/data/owid-covid-data.csv). It also reads geoJSON data, in order to draw country polygons on maps, from https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson, and centroid coordinates of countries (used in map pop-up plotting) from Google developers here: http://developers.google.com/public-data/docs/canonical/countries_csv/

Please make sure you have the **countryNameMapping** JSON file provided downloaded in your working directory. Country names are represented slightly differently between the OWID data and the geoJSON data (e.g. 'United States' vs. 'United States of America'), and this name mapping file helps reconcile this. The **countryNameISO2** file is also good to keep handy, although the script knows to re-write it for you in case it's not found in your working directory.

The script uses the folium package to produce choropleth maps of total cases and/or total deaths due to COVID in the world, with popup markers indicating the top 10 countries for both categories and thei respective case/death tolls, after which Selenium displays these interactive maps using your Firefox browser.

The COVID class object defined herein takes in four parameters: year, month and day as ints - please make sure these correspond to a data during the pandemic, starting in March 2020; and a final map_type str parameter, where the user indicates which type of map they'd like to see (for 'Cases' or 'Deaths').