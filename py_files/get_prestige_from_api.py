## Function to get prestige options from the Starships api and upload it to excel and the Wordpress database
## Also creates a data frame of the data EXACTLY as returned by the api

## inputs: crew_ids (list of ids to import prestige data for)
## outputs: prestige_data  (dataframe, one row for each combination)

# ----- Packages ------------------------------------------------------
import csv
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
def get_data_from_url(url):
    data = urllib.request.urlopen(url).read()
    return data.decode('utf-8')

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

def get_production_server():
    url = 'https://api.pixelstarships.com/SettingService/GetLatestVersion3?languageKey=en&deviceType=DeviceTypeAndroid'
    raw_text = get_data_from_url(url)
    d = xmltree_to_dict2(raw_text, key=None)
    return d['ProductionServer']



def get_prestige_data_from_url(char_id, action):
    if action == 'to':
        url = base_url + 'CharacterService/PrestigeCharacterTo?characterDesignId={}'.format(char_id)
        attrib = 'PrestigeCharacterTo'
    elif action == 'from':
        url = base_url + 'CharacterService/PrestigeCharacterFrom?characterDesignId={}'.format(char_id)
        attrib = 'PrestigeCharacterFrom'
    else:
        print('action = "{}" is invalid'.format(action))
        return None
    txt = get_data_from_url(url)
    return txt, url


def prestigedata_to_df(raw_text):
    df = pd.DataFrame()
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root.findall('PrestigeCharacterFrom'):
        timestamp = c.attrib
        for cc in c.findall('Prestiges'):
            for i, p in enumerate(cc.findall('Prestige')):
                row = pd.DataFrame(p.attrib, index=[i])
                df = df.append(row)
    return df


# ----------------- MAIN
def main(char_ids):
    
    # ---------------------------------------- Download prestige data from api
    print('Downloading prestige data...')
    df = pd.DataFrame()
    
    for char_id in char_ids:
        data, _ = get_prestige_data_from_url(char_id, 'from')
        assert isinstance(data, str)
        row_df = prestigedata_to_df(data)
        df = df.append(row_df)

    df.CharacterDesignId1 = df.CharacterDesignId1.astype(int)
    df.CharacterDesignId2 = df.CharacterDesignId2.astype(int)
    df.ToCharacterDesignId = df.ToCharacterDesignId.astype(int)


    # ------------------------------------------ Sort the table (char1 < char 2) and remove duplicates
    print('Setting up data frame...')
    for row in range(len(df)):
        c1 = df['CharacterDesignId1'].values[row]
        c2 = df['CharacterDesignId2'].values[row]
        
        if c2 < c1:
            df['CharacterDesignId1'].values[row] = c2
            df['CharacterDesignId2'].values[row] = c1
               
    df.drop_duplicates(keep='first', inplace = True)
    
    # ------------------------------------------- Save to wordpress database
    print('Saving to wordpress database...')
    engine = create_engine('mysql://pixelpg4_rigging:PIXs@tt03fl@162.241.219.104/pixelpg4_crew', echo=False)    
    df.to_sql('crew_prestige', con=engine, if_exists='replace', index = False) 
    engine.dispose()
    
    print('Done!')
    
    return df

base_url = 'http://{}/'.format(get_production_server())
if __name__== "__main__":
    main()