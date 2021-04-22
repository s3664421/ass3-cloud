
import os
import boto3
from consolemenu import *
from consolemenu.items import *
import sys
import json
import requests
from decimal import Decimal
 


song_table = None
image_bucket_name = 'image-bucket-s3664421-ass2'
region = 'us-east-1'

def create_bucket(bucket_name = image_bucket_name, region = None):
	
	screen = Screen()
	try:
		s3_client = boto3.client('s3', region_name = region)
		response = s3_client.list_buckets()
		if bucket_name not in response['Buckets']:
			if region is None:
				s3_client.create_bucket(Bucket = bucket_name)
			else:
				location = {'LocationConstraint': region}
				s3_client.create_bucket(Bucket = bucket_name, CreateBucketConfiguration=location,)
			screen.println("Bucket Created %s" % bucket_name)
		else:
			screen.println("Bucket already exists")
			
	except Exception as e:
		screen.println(e)
		screen.println("name: %s" % bucket_name)
		screen.println("location: %s" % region)
	
	
	PromptUtils(screen).enter_to_continue()
	
	


def delete_song_table(endpoint):
	dynamodb = None
	screen = Screen()
	if not dynamodb:
		dynamodb = boto3.resource('dynamodb',  endpoint_url = endpoint)
	
	try:
		result = dynamodb.Table('Songs')
		if result is None:
			screen.println("Table does not exist")
		else:
			result.delete()
			screen.println("Table deleted..")
		screen.println(result)
	except Exception as e:
		screen.println("Error occoured %s" % e)
	finally:
		
		PromptUtils(screen).enter_to_continue()


def download_images_to_s3(bucket_name = "Image_Bucket", region = 'us-east-1'):

	screen = Screen()
	try:
		s3_client = boto3.client('s3', region_name = region)
		response = s3_client.list_buckets()
		if bucket_name not in response['Buckets']:
			screen.println("Storage bucket as does not exist: %s" % bucket_name)
		else:
			create_bucket()
			
			
	except ClientError as e:
		screen.println(e)
	
	PromptUtils(screen).enter_to_continue()	

def create_user_table(endpoint):
	dynamodb = None
	table_created = False

	if not dynamodb:
		dynamodb = boto3.resource('dynamodb', endpoint_url = endpoint )
		
	try:

		table = dynamodb.create_table(
			TableName = 'Users',
			KeySchema=[
				{
					'AttributeName': 'email',
					'KeyType' : 'HASH'
				}       
			],
			AttributeDefinitions=[
				{
					'AttributeName': 'email',
					'AttributeType': 'S'
				},
			],
			ProvisionedThroughput = {
				'ReadCapacityUnits': 10,
				'WriteCapacityUnits': 10
			}
		)
		table_created = True
		
	except Exception as e:
		print("exception: %s" % e)
			
	
	screen = Screen()
	try:
		if table_created:
			screen.println("\n\n TTable Created")
			
		else:
			screen.println("\n\n Table Already Exists")
		
	except Exception as e:
		screen.println("Error occoured %s" % e)
	finally:
		PromptUtils(screen).enter_to_continue()

def create_song_table(endpoint):
	dynamodb = None
	song_table = None
	table = None
	table_created = False

	if not dynamodb:
		dynamodb = boto3.resource('dynamodb', endpoint_url = endpoint )
	
	

	try:

		table = dynamodb.create_table(
			TableName = 'Songs',
			KeySchema=[
				{
					'AttributeName': 'artist',
					'KeyType' : 'HASH'
				},
				{  'AttributeName': 'title',
					'KeyType' : 'RANGE' 
				}          
			],
			AttributeDefinitions=[
				{
					'AttributeName': 'artist',
					'AttributeType': 'S'
				},
				{
					'AttributeName': 'title',
					'AttributeType': 'S'
				},
			],
			ProvisionedThroughput = {
				'ReadCapacityUnits': 10,
				'WriteCapacityUnits': 10
			}
		)
		table_created = True
		
	except Exception as e:
		print("exception: %s" % e)
		song_table = dynamodb.Table('Songs')
			
	
	screen = Screen()
	try:
		if song_table == table:
			screen.println("\n\n TTable Created")
			screen.println("Table Status: ", song_table.table_status)
		else:
			screen.println("\n\n Table Already Exists")
			screen.println("Table Status: ", song_table.table_status)
	except Exception as e:
		screen.println("Error occoured %s" % e)
	finally:
		PromptUtils(screen).enter_to_continue()

def create_sub_table(endpoint):
	dynamodb = None
	sub_table = None
	table = None
	table_created = False

	if not dynamodb:
		dynamodb = boto3.resource('dynamodb', endpoint_url = endpoint )
	
	try:

		table = dynamodb.create_table(
			TableName = 'Subs',
			KeySchema=[
				{
					'AttributeName': 'email',
					'KeyType' : 'HASH'
				}     
			],
			AttributeDefinitions=[
				{
					'AttributeName': 'email',
					'AttributeType': 'S'
				}
			],
			ProvisionedThroughput = {
				'ReadCapacityUnits': 10,
				'WriteCapacityUnits': 10
			}
		)
		table_created = True
		
	except Exception as e:
		print("exception: %s" % e)
		sub_table = dynamodb.Table('Songs')
			
	
	screen = Screen()
	try:
		if sub_table == table:
			screen.println("\n\n TTable Created")
			screen.println("Table Status: ", song_table.table_status)
		else:
			screen.println("\n\n Table Already Exists")
			screen.println("Table Status: ", song_table.table_status)
	except Exception as e:
		screen.println("Error occoured %s" % e)
	finally:
		PromptUtils(screen).enter_to_continue()




def load_data_from_json(endpoint, upload_image = False):
	dynamodb = None
	s3_client = None
	screen = Screen()	
	with open("data/a2.json") as json_file:
		song_list = json.load(json_file, parse_float=Decimal)

	if not dynamodb:
		dynamodb  = boto3.resource('dynamodb',  endpoint_url = endpoint)
	
	screen = Screen()
	try:
		song_table = dynamodb.Table('Songs')
		screen.println("Table Exists..")
	except Exception as e:
		screen.println("Error occoured %s" % e)
		return
	finally:
		PromptUtils(screen).enter_to_continue()	


	try:
		s3_client = boto3.client('s3', region_name = region)
		response = s3_client.list_buckets()
		if image_bucket_name not in response['Buckets']:
			screen.println("Storage bucket as does not exist: %s" % image_bucket_name)
			create_bucket()
			
		else:	
			pass
	except Exception as e:
			screen.println(e)

	for song in song_list['songs']:

		image_name = song['artist']+'-'+song['title']+'-'+song['year']+'.jpg'
		song.update({'bucket_image_name': image_name})
		if upload_image is True:
			r = requests.get(song['img_url'], stream = True)
			s3_client.upload_fileobj(r.raw, image_bucket_name, image_name)

		response = song_table.put_item(Item=song)
		print(response)
		print("\n")
		
	PromptUtils(screen).enter_to_continue()	



def main(argv):
	DATABASE_ENPOINT_URL = None
	for arg in argv:
		if arg == '-l':
			DATABASE_ENPOINT_URL = 'http://localhost:8000'
			print("Running on Local Database")
		elif arg == '-o':
			DATABASE_ENPOINT_URL = None
			print("Running on Live Database")


	d_menu_title = "Assigment 2 Data Loader\n"
	d_menu_items = [ "Create Song Table","Load From JSON", "Load Json And Images to S3", "Create Users", "Delete Song Table", "Create Sub Table"]
	d_menu_exit = False

	menu = ConsoleMenu(title =d_menu_title, show_exit_option=True)
	function_0 = FunctionItem(text=d_menu_items[0], function=create_song_table,args=[DATABASE_ENPOINT_URL])
	function_1 = FunctionItem(text=d_menu_items[1], function=load_data_from_json, args =[DATABASE_ENPOINT_URL])
	function_2 = FunctionItem(text=d_menu_items[2], function=load_data_from_json, args =[DATABASE_ENPOINT_URL, True])
	function_3 = FunctionItem(text=d_menu_items[3], function=create_user_table, args = [DATABASE_ENPOINT_URL])
	function_4 = FunctionItem(text=d_menu_items[4], function =delete_song_table, args =[DATABASE_ENPOINT_URL])
	function_5 = FunctionItem(text=d_menu_items[5], function = create_sub_table, args = [DATABASE_ENPOINT_URL])


	menu.append_item(function_0)
	menu.append_item(function_1)
	menu.append_item(function_2)
	menu.append_item(function_3)
	menu.append_item(function_4)
	menu.append_item(function_5)

	menu.show()
		
	

if __name__ == '__main__':
	main(sys.argv[1:])

