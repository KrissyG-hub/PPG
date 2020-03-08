## Function to get the crew from the Starships api and upload it to excel and the Wordpress database
## Also creates a data frame of the data EXACTLY as returned by the api

## inputs: none
## outputs: crew_data  (dataframe, one row for each crew, one column for each stat in the api)

# ----- Packages ------------------------------------------------------
import csv
import datetime
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree
import pandas as pd
import numpy as np

import mysql.connector
from sqlalchemy import create_engine

PSS_CHARS_RAW_FILE = 'pss-chars-raw.txt'
MAXIMUM_CHARACTERS = 1900


# ----- Utility functions for api intake ------------------------------
def save_raw_text(raw_text, filename):
    try:
        with open(filename, 'w') as f:
            f.write(raw_text)
    except:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(raw_text)

def get_data_from_url(url):
    data = urllib.request.urlopen(url).read()
    return data.decode('utf-8')

def load_data_from_url(filename, url, refresh='auto'):
    if os.path.isfile(filename) and refresh != 'true':
        if refresh == 'auto':
            if is_old_file(filename, max_seconds=3600):
                raw_text = get_data_from_url(url)
                save_raw_text(raw_text, filename)
                return raw_text
        with open(filename, 'r') as f:
            raw_text = f.read()
    else:
        raw_text = get_data_from_url(url)
        save_raw_text(raw_text, filename)
    return raw_text

def xmltree_to_dict2(raw_text, key=None):
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        d = {}
        for cc in c:
            if key is None:
                d = cc.attrib
            else:
                d[cc.attrib[key]] = cc.attrib
    return d

def xmltree_to_dict3(raw_text, key):
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        for cc in c:
            d = {}
            for ccc in cc:
                d[ccc.attrib[key]] = ccc.attrib
    return d


def create_reverse_lookup(d, new_key, new_value):
    """Creates a dictionary of the form:
    {'new_key': 'new_value'}"""
    rlookup = {}
    for key in d.keys():
        item = d[key]
        rlookup[item[new_key]] = item[new_value]
    return rlookup


def get_production_server():
    url = 'https://api.pixelstarships.com/SettingService/GetLatestVersion3?languageKey=en&deviceType=DeviceTypeAndroid'
    raw_text = get_data_from_url(url)
    d = xmltree_to_dict2(raw_text, key=None)
    return d['ProductionServer']


def request_new_char_sheet():
    # Download Character Sheet from PSS Servers
    url = base_url + 'CharacterService/ListAllCharacterDesigns?languageKey=en'
    data = urllib.request.urlopen(url).read()
    return data.decode()


def get_char_sheet(refresh='auto'):
    url = base_url + 'CharacterService/ListAllCharacterDesigns?languageKey=en'
    raw_text = load_data_from_url(PSS_CHARS_RAW_FILE, url, refresh=refresh)
    ctbl = xmltree_to_dict3(raw_text, 'CharacterDesignId')
    return ctbl


# ----- Get data from api -------------------------------------------------

def main():
    # ------------------------------- Take from api    
    ctbl = get_char_sheet(refresh='true')
    print('Pulled crew data from Pixel Starships API.')
    
    # ------------------------------- Print to excel
    # start with excel file headers
    txt = ('CharacterDesignId,CharacterDesignName,RaceType,FinalHp,FinalPilot,FinalAttack,FinalRepair,'
    'FinalWeapon,FinalScience,FinalEngine,FireResistance,Rarity,SpecialAbilityType,SpecialAbilityFinalArgument,'
           'WalkingSpeed,RunSpeed,TrainingCapacity,EquipmentMask,CollectionDesignId,Flags,CharacterHeadPartId,CharacterBodyPartId,'
           'CharacterLegPartId,CharacterDesignDescription\n')

    # Add character stats
    for k in ctbl.keys():
        item=ctbl[k]
            
        txt += f"{item['CharacterDesignId']},"
        txt += f"{item['CharacterDesignName']},"
        txt += f"{item['RaceType']},"
        txt += f"{item['FinalHp']},"
        txt += f"{item['FinalPilot']},"
        txt += f"{item['FinalAttack']},"
        txt += f"{item['FinalRepair']},"
        txt += f"{item['FinalWeapon']},"
        txt += f"{item['FinalScience']},"
        txt += f"{item['FinalEngine']},"
        txt += f"{item['FireResistance']},"
        txt += f"{item['Rarity']},"
        txt += f"{item['SpecialAbilityType']},"
        txt += f"{item['SpecialAbilityFinalArgument']},"
        txt += f"{item['WalkingSpeed']},"
        txt += f"{item['RunSpeed']},"
        txt += f"{item['TrainingCapacity']},"
        txt += f"{item['EquipmentMask']},"
        txt += f"{item['CollectionDesignId']},"
        txt += f"{item['Flags']},"
        txt += f"{item['CharacterHeadPartId']},"       
        txt += f"{item['CharacterBodyPartId']},"
        txt += f"{item['CharacterLegPartId']},"
        
        desc = item['CharacterDesignDescription'].replace(",", "").encode('ascii', 'replace').decode()
        txt += desc + '\n'
        
    with open('characters_fulldata.csv', 'w', encoding='utf-8') as f:
        f.write(txt)
        
    print('Wrote data to excel file.')
        
    # --------------------------- Set up in a dataframe
    crew_df = pd.read_csv('characters_fulldata.csv')
    
    # HACK hack HACK - drop the common Michelle, since there are two crew named Michelle =/
    row = crew_df.query('CharacterDesignName=="Michelle" & Rarity=="Common"').index
    crew_df.drop(row, axis=0, inplace=True)
    
    # -------------------------- Write to wordpress
    engine = create_engine('mysql://pixelpg4_rigging:PIXs@tt03fl@162.241.219.104/pixelpg4_crew', echo=False)    
    crew_df.to_sql('crew_stats', con=engine, if_exists='replace', index = False) 
    engine.dispose()
    
    print('Wrote data to Wordpress db.')
    
    # -------------------------- Return dataframe
    print("Here's your data frame!")
    return crew_df;
    
    
    
base_url = 'http://{}/'.format(get_production_server())
if __name__== "__main__":
    main()