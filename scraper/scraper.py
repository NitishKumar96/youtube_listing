#!/usr/bin/python

import os
import sys
from datetime import datetime, timedelta
import time
import psycopg2 as psql
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

################################################# GLOABL VARIABLES
SCRAPE_INTERVAL = int(os.getenv('scrape_interval', 30))
RETRY_DELAY = int(os.getenv('retry_delay', 10))
QUERY = os.getenv('search_keyword', 'new')
#  DATABSE VARIABLES
DB_NAME = os.getenv('db_name', None)
DB_USER = os.getenv('db_user', None)
DB_PASS = os.getenv('db_pass', None)
DB_HOST = os.getenv('db_host', None)
DB_PORT = os.getenv('db_port', None)
FILL_EMPTY_DB = False
# API VARIABLES
API_KEY_FILE = os.getenv('api_key_file', None)
API_KEY = os.getenv('api_key', None)
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# QUERY STATEMET FOR INSERTS
insert_sql = 'INSERT INTO listing("videoId","title","channelId","channelTitle","description","thumbnail","publishTime","db_entry_time") VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING; '

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
            row = (   result['id']['videoId']
                    , result['snippet']['title']
                    , result['snippet']['channelId']
                    , result['snippet']['channelTitle']
                    , result['snippet']['description']
                    , result['snippet']['thumbnails']['medium']['url']
                    , result['snippet']['publishTime']
                    , datetime.now().isoformat("T")+'Z'
                    )
            row_list.append(row)
    return (row_list,result_count)

key_counter=0   # used to represent number of key used in the file
def get_key():
    if API_KEY_FILE not in [None,''] :
        # todo process file to get api key
        global key_counter
        line_pointer=0
        with open(API_KEY_FILE,'r') as key_file:
            for key in key_file:
                if line_pointer == key_counter:
                    key_counter+=1
                    print('using key :',key)
                    return key
                line_pointer+=1
        # if the key_counter exceeds, either file doesnot has keys or we have used all of them
        return None # this will stop the code
    else:
        return API_KEY


################################################# main 
def main():
    print('Starting scraper..')
    # make database connection
    while True:
        print('Trying to connect to database ..')
        try:
            print('variables beeing used ',DB_NAME
                    , DB_USER
                    , DB_PASS
                    , DB_HOST
                    , DB_PORT)
            # connect to db
            db_conn = psql.connect( database = DB_NAME
                                    , user= DB_USER
                                    , password= DB_PASS
                                    , host= DB_HOST
                                    , port= DB_PORT
                                   )
            pass
        except Exception as e:
            # not able to connect to db retry, MOST PROBABLY DATABASE IS STILL STARTING 
            print("Error while connecting to database: "+str(e))
            if RETRY_DELAY > -1:
                time.sleep(RETRY_DELAY)
            else:
                # if delay is -1, exit the code 
                sys.exit('Failed to make connection with database')
        else:
            print("Database connected.")
            db_cursor = db_conn.cursor()
            break
    

    # TODO if we have to fill empty db
    # if FILL_EMPTY_DB ==True:
    #     # TODO
    #     # check if any old record are present or not
    #     pass
    
    # start time with gap of one inerval or more
    last_scrap_time = datetime.now() - timedelta(seconds=SCRAPE_INTERVAL*10)
    retry = False
    key_invalid = True # get new key for the 1st time
    while True:
        data=[]
        try:
            #  process key
            if key_invalid== True:
                key = get_key()
                key_invalid=False   
                if key == None:
                    sys.exit("Error, Key not present.")

            data,_ = scrape_youtube( publishedAfter=last_scrap_time.isoformat("T")+'Z'
                                     ,api_key=key
                                     ,query=QUERY
                                    )
        except HttpError as e:
            print('HttpError in scraping: ', e._get_reason())
            # NOTE: add error when we have to get new key in this list
            key_errors=['API_KEY_INVALID','quotaExceeded'] # posible key error, have to get new key
            if any([error for error in key_errors if error in str(e.content)]):
                key_invalid = True
            print('Retrying in ', RETRY_DELAY,'s')
            time.sleep(RETRY_DELAY)

        else:
            # INSERT INTO DB
            try:
                if len(data)>0:
                    db_cursor.executemany(insert_sql,data)
                    db_conn.commit()
                    print(len(data),' Rows inserted into database.')
            except Exception as e:
                print("Error while storing new data, ",e.ds)
                print('Retrying in ', RETRY_DELAY,'s')
                time.sleep(RETRY_DELAY)   
            else:
                # udpate last time before going to sleep
                last_scrap_time=datetime.now()
                print('Going for sleep: ',SCRAPE_INTERVAL,'s')
                time.sleep(SCRAPE_INTERVAL)
            
    # close db connection before exiting
    db_conn.commit()
    db_conn.close()
    return

# START THE MAIN FUNCTION
main()
