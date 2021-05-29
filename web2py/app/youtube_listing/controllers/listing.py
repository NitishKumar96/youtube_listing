from datetime import datetime, timedelta
import json
import pandas as pd


def pandas_df(rows, fields, columns, cacheable):
	return pd.DataFrame.from_records(rows, columns=columns)

def home():
	# main page to display latest youtube listings, collected into db
	columns=('videoId','title','channelId','channelTitle','description','thumbnail','publishTime')
	# get data form db
	listings = db((db.listing.is_active==True)
					).select(
						db.listing.videoId,
						db.listing.title,
						db.listing.channelId,
						db.listing.channelTitle,
						db.listing.description,
						db.listing.thumbnail,
						db.listing.publishTime,
						orderby=~db.listing.publishTime,
						limitby=(0,50)
						)
	return locals()

def latest_listing():
	# get vars from request
	page_no = request.vars.page_no or None
	page_no = int( page_no) if page_no!=None else 0
	page_max = request.vars.page_max or None
	page_max = int( page_max) if page_max!=None else 0
	limit_max = request.vars.limit_max or None
	limit_max = int(limit_max) if limit_max!=None else 10
	offset = request.vars.offset or None
	offset = int(offset) if offset!=None else 0
	data_orient = request.vars.data_orient or "records"
	return_sql= request.vars.return_sql or False

	# list of required variables
	check_list=(limit_max,offset)
	if all([value != None for value in check_list]):
		if page_no >=0 and page_max>0:
			limit_max = max(page_no * page_max,0)
			offset = max(limit_max - page_max,0)
		columns=('videoId','title','channelId','channelTitle','description','thumbnail','publishTime')
		# get data form db
		listings = db((db.listing.is_active==True)
						).select(
							db.listing.videoId,
							db.listing.title,
							db.listing.channelId,
							db.listing.channelTitle,
							db.listing.description,
							db.listing.thumbnail,
							db.listing.publishTime,
							orderby=~db.listing.publishTime,
							limitby=(offset,limit_max),
						  	processor=pandas_df
							)
		# ######################### PROCCESS DATA BEFORE RETURNING
		# set proper column names
		listings.columns= columns
		# change timestamp to str, else it will give error in json dump
		listings['publishTime']=listings['publishTime'].astype('str')
		# ######################### 
		return_dict={'limit_max': limit_max
					,'offset': offset
					,'data_orient': data_orient
					,'no_records': len(listings)
					,'data': listings.to_dict(orient=data_orient)	# dataframe to dict
					}
		# to get sql used by this api
		if return_sql in ['True',True]:
			return_dict['sql_used']=db._lastsql[0]
		return json.dumps(return_dict)
	else:
		return json.dumps(dict(Error="Invalid data provided."))

def search_listing():
	# get vars from request
	# limits
	page_no = request.vars.page_no or None
	page_no = int( page_no) if page_no!=None else 0
	page_max = request.vars.page_max or None
	page_max = int( page_max) if page_max!=None else 0
	limit_max = request.vars.limit_max or None
	limit_max = int(limit_max) if limit_max!=None else 10
	offset = request.vars.offset or None
	offset = int(offset) if offset!=None else 0

	# filters
	keyword = request.vars.keyword or ''
	start_time = request.vars.start_time or None
	end_time = request.vars.end_time or None
	# return parameters
	return_sql= request.vars.return_sql or False
	data_orient = request.vars.data_orient or "records"

	# process start and end time, if value is not present or invalid new values will get generated
	try:
		datetime.fromisoformat(start_time.replace('Z',''))
	except Exception as e:
		# invalid satrt time, have to make default
		start_time = datetime.now() - timedelta(days=7)
		start_time= start_time.isoformat("T")+'Z'
	
	try:
		datetime.fromisoformat(end_time.replace('Z',''))
	except Exception as e:
		end_time = datetime.now().isoformat("T")


	if len(keyword)>0:
		if page_no >=0 and page_max>0:
			limit_max = max(page_no * page_max,0)
			offset = max(limit_max - page_max,0) 

		# generate sql 
		sql = """
				SELECT
					"listing"."videoId",
					"listing"."title",
					"listing"."channelId",
					"listing"."channelTitle",
					"listing"."description",
					"listing"."thumbnail",
					"listing"."publishTime"
				FROM
					"listing"
				WHERE 
					"listing"."is_active" = 'T'
					AND 
					(
						"listing"."title" like '%{keyword}%'
						OR 
						"listing"."channelTitle" like '%{keyword}%'
						OR
						"listing"."description" like '%{keyword}%'
					)
					AND
					"listing"."publishTime" BETWEEN '{start_time}' AND '{end_time}'
				ORDER BY
					"listing"."publishTime" DESC
				LIMIT {limit_max} OFFSET {offset};
			""".format(	 keyword=keyword
						,limit_max = limit_max
						,offset = offset
						,start_time=start_time
						,end_time=end_time
					)
		try:
			rows = db.executesql(sql)
		except Exception as e:
			return json.dums(dict(Error=str(e),info='Error while executing query.'))
	
		columns=('videoId','title','channelId','channelTitle','description','thumbnail','publishTime')
		listings = pd.DataFrame(rows,columns=columns)
		# ######################### PROCCESS DATA BEFORE RETURNING
		# change timestamp to str, else it will give error in json dump
		listings['publishTime']=listings['publishTime'].astype('str')
		# ######################### 
		return_dict={'limit_max': limit_max
					,'offset': offset
					,'data_orient': data_orient
					,'no_records': len(listings)
					,'data': listings.to_dict(orient=data_orient)	# dataframe to dict
					}
		# to get sql used by this api
		if return_sql in ['True',True]:
			return_dict['sql_used']=sql
		return json.dumps(return_dict)
	else:
		return json.dumps(dict(error='Invalid keyword for search'))
