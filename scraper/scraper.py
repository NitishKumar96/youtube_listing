#!/usr/bin/python

import os
import sys
from datetime import datetime, timedelta
import time
import psycopg2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

################################################# GLOABL VARIABLES
SCRAPE_INTERVAL = int(os.getenv('scrape_interval', 30))
RETRY_DELAY = int(os.getenv('retry_delay', 10))
QUERY = os.getenv('query', 'new')
#  DATABSE VARIABLES
DB_NAME = os.getenv('db_name', None)
DB_USER = os.getenv('db_user', None)
DB_PASS = os.getenv('db_pass', None)
FILL_EMPTY_DB = False
# API VARIABLES
API_KEY_FILE = os.getenv('api_file', None)
API_KEY = os.getenv('api_key', None)
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
################################################# support functions
def scrape_youtube(publishedAfter,api_key,query='new',maxResults=50):

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=api_key)

    # Call the search.list method to retrieve results matching the specified query 
    search_response = youtube.search().list(
                        q               = query,
                        part            = 'id,snippet',
                        type            = 'video',
                        publishedAfter  = publishedAfter,
                        maxResults      = maxResults            # 50 is max 
                        ).execute()
    print( " Search results found:",str(search_response['pageInfo']))
    # total number of records found
    result_count = search_response['pageInfo']['totalResults']
    # convert the return data into a list
    row_list=[]
    for result in search_response.get('items',[]):
        if result['id']['kind']=='youtube#video':
            row = (
                      result['id']['videoId']
                    , result['snippet']['title']
                    , result['snippet']['channelId']
                    , result['snippet']['channelTitle']
                    , result['snippet']['description']
                    , result['snippet']['thumbnails']['medium']['url']
                    , result['snippet']['publishTime']
                    )
            row_list.append(row)
    return (row_list,result_count)

def get_key(new=False):
    if API_KEY_FILE != None and new ==True:
        # todo process file to get api key
        pass
    else:
        return API_KEY
################################################# main 
def main():
    print('Starting scraper..')
    # make database connection
    # while True:
    #     print('Trying to connect to database ..')
    #     try:
    #         # TODO connect to db
    #         pass
    #     except Exception as e:
    #         # not able to connect to db retry
    #         print("Error while connecting to database: "+str(e))
    #         if RETRY_DELAY > -1:
    #             time.sleep(RETRY_DELAY)
    #         else:
    #             # if delay is -1, exit the code 
    #             sys.exit('Failed to make connection with database')
    #     else:
    #         print("Database connected.")
    #         # if connection is maid 
    #         break


    # if we have to fill empty db
    if FILL_EMPTY_DB ==True:
        # TODO
        # check if any old record are present or not
        pass
    
    # start time with gap of one inerval
    last_scrap_time = datetime.now() - timedelta(seconds=SCRAPE_INTERVAL*10)
    retry = False
    key_invalid = True # get new key for the 1st time
    while True:
        data=[]
        try:
            #  process key
            if key_invalid== True:
                key = get_key(new=key_invalid)
                key_invalid=False   
                if key== None:
                    sys.exit("Key not present.")

            data,_ = scrape_youtube( publishedAfter=last_scrap_time.isoformat("T")+'Z'
                                     ,api_key=key
                                     ,query=QUERY
                                    )
        except HttpError as e:
            print('HttpError in scraping: ', e._get_reason())
            if 'API_KEY_INVALID' in str(er.content): # key error, have to get new key
                key_invalid = True
            print('Retrying in ', RETRY_DELAY,'s')
            time.sleep(RETRY_DELAY)

        else:
            try:
                if len(data)>0:
                    # TODO INSERT INTO DB
                    print(data)
            except Exception as e:
                print("Error while storing new data, ",e)
                print('Retrying in ', RETRY_DELAY,'s')
                time.sleep(RETRY_DELAY)   
            else:
                # udpate last time before going to sleep
                last_scrap_time=datetime.now()
                time.sleep(SCRAPE_INTERVAL)
            
    # TODO
    # close db connection before exiting

    return

print('calling main')
main()
