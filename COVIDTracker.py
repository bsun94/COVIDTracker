"""
Created on Sat Aug  1 15:18:20 2020

@author: Brian Sun

Tracks developments in COVID around the world and produces updated data visualizations
"""

import pandas as pd
import requests
import os
import folium
import json
import numpy as np
from datetime import datetime
from selenium import webdriver as wd
import sys

class COVID(object):
    
    # Don't let users pass urls into object - store them as defaults; remaining code cleaning up data is specific to formats of the sources
    # Further, good, freely-available COVID data sources are less prevalent than one'd think
    COVID_URL     = 'https://covid.ourworldindata.org/data/owid-covid-data.csv'
    GEOJSON_URL   = 'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'
    CENTROIDS_URL = 'http://developers.google.com/public-data/docs/canonical/countries_csv/'
    os.chdir(os.getcwd())
    
    def __init__(self, year=None, month=None, day=None, map_type='Cases'):
        """
        Notably error-checks the year, month, day and map_type attribute values passed. If date value is invalid, defaults to current date;
        if map_type is neither 'Cases' or 'Deaths', exits the scripts.
        """
        self.covid_df            = pd.DataFrame([])
        self.geo_data            = pd.DataFrame([])
        self.name_iso2_mapping   = {}
        self.countries_centroids = pd.DataFrame([])
        
        try:
            self.date = datetime(year=year, month=month, day=day)
        except:
            print('Invalid date entry (year, month, day take valid int inputs)! Date defaulted to today.')
            self.date = datetime.today()
        
        if self.date > datetime.today():
            print('Can\'t input future date! Date defaulted to today.')
            self.date = datetime.today()
        
        if map_type not in ['Cases', 'Deaths']:
            sys.exit('Please specify either "Cases" or "Deaths" as map type!')
        else:
            self.map_type = map_type
    
    def webScraper(self):
        """
        Cases data maintained as a personal project by an individual; GeoJSON data source found in folium's documentation.
        Exits if any 1 of the 3 online data inputs is unavailable. Also checks if date inputted falls outside of the date range present in
        Our World in Data csv file - exits the script in this scenario.
        """
        try:
            self.covid_df = pd.read_csv(self.COVID_URL)
        except:
            sys.exit('COVID data is unavailable at source.')
            
        latest_date   = self.covid_df['date'].max()
        earliest_date = self.covid_df['date'].min()
        self.covid_df = self.covid_df[self.covid_df['date'] == self.date.strftime('%Y-%m-%d')]
        
        if self.covid_df.empty:
            exit_string = 'Requested date not available. Latest date available is ' + latest_date + ' while earliest is ' + earliest_date
            sys.exit(exit_string)
        else:
            self.covid_df = self.covid_df[self.covid_df['location'] != 'World']
        
        try:
            self.countries_centroids = pd.read_html(self.CENTROIDS_URL, header=0, index_col='country')[0]
        except:
            sys.exit('Central coordinates data for countries unavailable from Google developers.')
        
        try:
            self.geo_data = requests.get(self.GEOJSON_URL).json()
        except:
            sys.exit('GeoJSON data unavailable to draw country polygons.')
    
    def writeCountryCodeFile(self):
        """
        Meant to run independently to create a country name-to-ISO2 code mapping on a one-time basis to save on future computation.
        Exits if online geoJSON data is unavailable.
        """
        try:
            geojson = requests.get(self.GEOJSON_URL).json()
        except:
            sys.exit('GeoJSON data unavailable at source.')
        
        country_mapping = {}
        for country in geojson['features']:
            iso_2        = country['properties']['ISO_A2']
            country_name = country['properties']['ADMIN']
            country_mapping.update({country_name: iso_2})
        
        with open('countryNameISO2.json', 'w') as file:
            json.dump(country_mapping, file)
    
    def updateCountryNames(self):
        """
        Matches country names from COVID data to spelling/references in GeoJSON data.
        Exits if the countryNameMapping file is unavailable in the current directory. If the countryNameISO2 file is unavailable, it creates the file
        in the current directory.
        """
        try:
            with open('countryNameMapping.json', 'r') as file:
                name_mapping = json.loads(file.read())
        except:
            sys.exit('countryNameMapping.json file is unavailable in current directory.')
        
        for key, value in name_mapping.items():
            self.covid_df.replace(key, value, inplace=True)
        
        try:
            with open('countryNameISO2.json', 'r') as file:
                self.name_iso2_mapping = json.loads(file.read())
        except:
            print('countryNameISO2.json file is unavailable in current directory, creating file...')
            self.writeCountryCodeFile()
            print('Re-importing required JSONs...')
            self.updateCountryNames()
    
    def generateFileName(self):
        """
        Makes naming map file easier for code later on.
        """
        return 'Covid' + self.map_type + '.html'
    
    def unitsDetector(self, num):
        """
        Recognizes if a number is in units, thousands, millions, billions. Forces floats into ints using int().
        Exits if num is not an int or a float. While method uses len of argument instead of the argument itself, the check more so ensures
        the user is not misusing this method.
        """
        try:
            num = int(num)
        except:
            sys.exit('Invalid input! Method only takes ints or floats.')
        
        if len(str(num)) % 3 == 0:
            digits = len(str(num)) - 3
        else:
            digits = len(str(num)) - (len(str(num)) % 3)
        
        units = {9: 'B', 6: 'M', 3: 'K', 0: ''}[digits]
        
        return 10 ** digits, units
    
    def drawMap(self):
        """
        Plot choropleth map for total COVID cases/deaths, marking top 10 countries.
        """
        world_map     = folium.Map(location=[25, 10], zoom_start=3)
        totals_column = 'total_' + self.map_type.lower()
        top10         = self.covid_df.sort_values(totals_column, axis=0, ascending=False)['location'][:10]
        scale, units  = self.unitsDetector(self.covid_df[totals_column].max())
        
        color_scheme  = {'Cases': 'YlOrRd', 'Deaths': 'PuRd'}[self.map_type]
        bins          = list(np.linspace(0, np.ceil(self.covid_df[totals_column].max() / scale) * scale, 6))
        legend_name   = 'Total Number of COVID-19 ' + self.map_type
        map_file_name = self.generateFileName()
        
        folium.Choropleth(geo_data=self.geo_data,
                          data=self.covid_df,
                          columns=['location', totals_column],
                          key_on='feature.properties.ADMIN',
                          fill_color=color_scheme,
                          bins=bins,
                          legend_name=legend_name,
                          highlight=True
                          ).add_to(world_map)
        
        for i in range(10):
            country = top10.iloc[i]
            cases   = self.covid_df[self.covid_df['location'] == country][totals_column] / scale
            
            # Centroid coordinates for each country labelled by its ISO-2 code
            lat   = self.countries_centroids.loc[self.name_iso2_mapping[country]]['latitude']
            long  = self.countries_centroids.loc[self.name_iso2_mapping[country]]['longitude']
            popup = f"{country}: {cases.values[0]:.2f}{units} total {self.map_type.lower()}"
            
            folium.Marker(location=[lat, long],
                          popup=folium.Popup(popup, 
                                             max_width=1000)
                          ).add_to(world_map)
            
            world_map.save(map_file_name)
    
    def displayMap(self):
        """
        Displays the html file created of the choropleth map in a Firefox browser window.
        Exits if either the map html file or if Firefox does not exist.
        """
        filepath = os.getcwd() + '/' + self.generateFileName()
        
        if not os.path.exists(filepath):
            sys.exit('Desired map has not yet been created! Did you change map type midway?')
        
        try:
            browser = wd.Firefox()
            browser.get('file:///' + filepath)
            browser.maximize_window()
        except:
            sys.exit('Install Firefox!')


maps1 = COVID(year=2020, month=8, day=1)
maps1.webScraper()
maps1.updateCountryNames()
maps1.drawMap()
maps1.displayMap()