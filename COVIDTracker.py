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

os.chdir(os.getcwd())

class COVID(object):
    
    # Don't let users pass urls into object - store them as defaults; remaining code cleaning up data is specific to formats of the sources
    # Further, good, freely-available COVID data sources are less prevalent than one'd think
    def __init__(self, year=None, month=None, day=None, map_type='Cases'):
        self.COVID_URL     = 'https://covid.ourworldindata.org/data/owid-covid-data.csv'
        self.GEOJSON_URL   = 'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'
        self.CENTROIDS_URL = 'http://developers.google.com/public-data/docs/canonical/countries_csv/'
        
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
    
    # Cases data maintained as a personal project by an individual; GeoJSON data source found in 
    # folium's documentation
    def webScraper(self):
        try:
            self.covid_df = pd.read_csv(self.COVID_URL)
            self.covid_df = self.covid_df[self.covid_df['date']==self.date.strftime('%Y-%m-%d')]
            self.covid_df = self.covid_df[self.covid_df['location']!='World']
        
        except:
            sys.exit('COVID data is unavailable at source.')
        
        try:
            self.countries_centroids = pd.read_html(self.CENTROIDS_URL, header=0, index_col='country')[0]
        
        except:
            sys.exit('Central coordinates data for countries unavailable from Google developers.')
        
        try:
            self.geo_data = requests.get(self.GEOJSON_URL).json()
        
        except:
            sys.exit('GeoJSON data unavailable to draw country polygons.')
    
    # Meant to run independently to create a country name-to-ISO2 code mapping on a one-time basis to save on 
    # future computation
    def writeCountryCodeFile(self):
        try:
            geojson = requests.get(self.GEOJSON_URL).json()
        
        except:
            sys.exit('GeoJSON data unavailable at source.')
        
        country_mapping = {}
        for country in geojson['features']:
            country_name = country['properties']['ADMIN']
            iso_2 = country['properties']['ISO_A2']
            country_mapping.update({country_name: iso_2})
        
        with open('countryNameISO2.json', 'w') as file:
            json.dump(country_mapping, file)
    
    # Matches country names from COVID data to spelling/references in GeoJSON data
    def updateCountryNames(self):
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
    
    # Plot choropleth map for total COVID cases/deaths, marking top 10 countries
    def drawMap(self):
        world_map = folium.Map(location=[25, 10], zoom_start=3)
        totals_column = 'total_' + self.map_type.lower()
        
        if self.map_type == 'Cases':
            color_scheme = 'YlOrRd'
            SCALE = 10 ** 6
            UNITS = 'M'
        
        else:
            color_scheme = 'PuRd'
            SCALE = 10 ** 3
            UNITS = 'K'
        
        top10 = self.covid_df.sort_values(totals_column, axis=0, ascending=False)['location'][:10]
        bins = list(np.linspace(0, np.ceil(self.covid_df[totals_column].max() / SCALE) * SCALE, 6))
        legend_name = 'Total Number of COVID-19 ' + self.map_type
        map_file_name = 'Covid' + self.map_type + '.html'
        
        folium.Choropleth(geo_data=self.geo_data,
                          data=self.covid_df, 
                          columns=['location', totals_column],
                          key_on='feature.properties.ADMIN',
                          fill_color=color_scheme,
                          bins=bins,
                          legend_name=legend_name,
                          highlight=True
                          ).add_to(world_map)
        
        for i in range(len(top10)):
            country = top10.iloc[i]
            cases = self.covid_df[self.covid_df['location']==country][totals_column] / SCALE
            
            # Centroid coordinates for each country labelled by its ISO-2 code
            lat = self.countries_centroids.loc[self.name_iso2_mapping[country]]['latitude']
            long = self.countries_centroids.loc[self.name_iso2_mapping[country]]['longitude']
            popup = '{0:s}: {1:.2f}{2:s} total {3:s}'.format(country, cases.values[0], UNITS, self.map_type.lower())
            
            folium.Marker(location=[lat, long],
                          popup=folium.Popup(popup, 
                                             max_width=1000)
                          ).add_to(world_map)
            
            world_map.save(map_file_name)
    
    def displayMap(self):
        filepath = os.getcwd() + '/Covid' + self.map_type + '.html'
        
        if not os.path.exists(filepath):
            sys.exit('Desired map has not yet been created! Did you change map type midway?')
        
        try:
            browser = wd.Firefox()
            browser.get('file:///' + filepath)
            browser.maximize_window()
        except:
            sys.exit('Install Firefox!')


maps1 = COVID(year='Frank', month=8, day=31, map_type='Deaths')
maps1.webScraper()
maps1.updateCountryNames()
maps1.drawMap()
maps1.displayMap()
