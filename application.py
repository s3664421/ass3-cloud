from flask import Flask, render_template, redirect, request, url_for, session
import os
import boto3
import string
from functools import wraps
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


application = Flask(__name__)


application.secret_key = 'secret_key'
#endpoint_url_global = 'http://localhost:8000'
endpoint_url_global = None
def check_user_is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap


def authenticate_user(user_email, user_password, endpoint_url_global = None):
    dynamodb = None
    user_table = None
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url = endpoint_url_global)
      
    
    try:
        user_table = dynamodb.Table('Users')
    except Exception as e:
        print("Exception Occoured at Authenticate Users: %s" % e)
        
        return "No database connection..."
    
    try:
        response = user_table.get_item( Key = {'email' : user_email})
    except ClientError as e:
        print(e.response['Error']['Message'])
        return [], e.response['Error']['Message']
    else:
        if response['Item']['password'] == user_password:
            return response['Item'], None
        else:
            print("Incorrect Password")
            return [], 'Incorrect Login Details'
        

def search_songs(title, artist, year):
    dynamodb = None
    song_table = None

    query_title = None
    query_artist = None
    query_year = None

    search_results = []
    scan_kwargs = None

    if title != '':
        query_title = string.capwords(title)
    if artist != '':
        query_artist = string.capwords(artist)
    if year != '':
        query_year = string.capwords(year)
    
    

    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url = endpoint_url_global)
    
    try:
        song_table = dynamodb.Table('Songs')
    except Exception as e:
        print("Searching songs: %s" % e)
    
    if (query_title is None)  and (query_year is None) and (query_artist is not None):
        scan_kwargs = {
        'FilterExpression': Key('artist').begins_with(query_artist),
        'ProjectionExpression': "#ar, title, #yr, bucket_image_name",
        'ExpressionAttributeNames': {"#ar": "artist", "#yr":"year"}
        }
    if (query_title is not None)  and (query_year is None) and (query_artist is None):
        scan_kwargs = {
        'FilterExpression':  Key('title').begins_with(query_title),
        'ProjectionExpression': "#ar, title, #yr, bucket_image_name",
        'ExpressionAttributeNames': {"#ar": "artist", "#yr":"year"}
        }

    if (query_title is None)  and (query_year is not None) and (query_artist is None):
        scan_kwargs = {
        'FilterExpression':  Key('year').begins_with(query_year),
        'ProjectionExpression': "#ar, title, #yr, bucket_image_name",
        'ExpressionAttributeNames': {"#ar": "artist", "#yr":"year"}
        }

    if (query_title is not None)  and (query_year is None) and (query_artist is not None):
        scan_kwargs = {
        'FilterExpression': Key('artist').begins_with(query_artist) & Key('title').begins_with(query_title),
        'ProjectionExpression': "#ar, title, #yr, bucket_image_name",
        'ExpressionAttributeNames': {"#ar": "artist", "#yr":"year"}
        }
    
    if (query_title is None)  and (query_year is not None) and (query_artist is not None):
        scan_kwargs = {
        'FilterExpression':  Key('artist').begins_with(query_artist) & Key('year').begins_with(query_year),
        'ProjectionExpression': "#ar, title, #yr, bucket_image_name",
        'ExpressionAttributeNames': {"#ar": "artist", "#yr":"year"}
        }
    if (query_title is not  None)  and (query_year is not None) and (query_artist is None):
        scan_kwargs = {
        'FilterExpression':  Key('title').begins_with(query_title) & Key('year').begins_with(query_year),
        'ProjectionExpression': "#ar, title, #yr, bucket_image_name",
        'ExpressionAttributeNames': {"#ar": "artist", "#yr":"year"}
        }
    if (query_title is not None)  and (query_year is not None) and (query_artist is not None):
        scan_kwargs = {
        'FilterExpression':  Key('title').begins_with(query_title) & Key('year').begins_with(query_year) & Key('artist').begins_with(query_artist),
        'ProjectionExpression': "#ar, title, #yr, bucket_image_name",
        'ExpressionAttributeNames': {"#ar": "artist", "#yr":"year"}
        }
    if (query_title is None)  and (query_year is None) and (query_artist is None):
        return [], "Please enter one or more fields" 
    


    
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        r = song_table.scan(**scan_kwargs)
        search_results.append(r['Items'])
        start_key = r.get('LastEvaluatedKey', None)
        done = start_key is None
    
    if len(search_results[0]) > 0:
        print("found results")
        print(len(search_results))
        return search_results, None
    else:
        return [], "No matches found"
          
def generate_image_urls(results_array):
    for result in results_array:
        url_string = 'https://image-bucket-s3664421-ass2.s3.amazonaws.com/' + result['bucket_image_name']
        result['bucket_image_name'] = url_string
    return results_array

def add_to_subscriptions(artist, song_title):

    user_email = session['user_email']
    dynamodb = None
    sub_table = None
    
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url = endpoint_url_global)
        sub_table = dynamodb.Table('Subs')
        
    try:
        response = sub_table.get_item(Key = {'email' : user_email})
        print(response)
    except Exception as e:
        print(e.response['Error']['Message'])
    else:
        try:
            if response['Item']:
                
                for songs in response['Item']['sub_songs']:
                    if songs['artist'] == artist and songs['title'] == song_title:
                        print("song already in subscriptions..")
                        return
                response = sub_table.update_item(

                Key = {
                    'email' :  user_email
                },
                UpdateExpression= "SET #attrName = list_append(#attrName, :attrValue)",
                ExpressionAttributeNames = {
                    "#attrName" : "sub_songs"
                },
                ExpressionAttributeValues = {
                    ":attrValue" : [{

                        "artist" : artist,
                        "title"  : song_title
                    }],
                },
                )
        except Exception as e:
            new_sub = {
                   'email' : user_email,
                   'total_subs' : 0,
                   'sub_songs' :[
                       {"id": 0,
                       "artist": artist,
                       "title": song_title}]
            }
            response = sub_table.put_item(Item=new_sub)

    #print(response['Item'])


def get_user_subscriptions():

    user_subscriptions = []

    user_email = session['user_email']
    dynamodb = None
    sub_table = None
    song_table = None
    
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url = endpoint_url_global)
        sub_table = dynamodb.Table('Subs')
        song_table = dynamodb.Table('Songs')
        
    try:
        response = sub_table.get_item(Key = {'email' : user_email})
        print(response)
    except Exception as e:
        print(e.response['Error']['Message'])
    else:
        try:
            if response['Item']:
                
                for songs in response['Item']['sub_songs']:
                    response = song_table.get_item(Key = 
                    {'artist': songs['artist'],
                    'title' : songs['title']})
                    print("adding to user subs")
                    print(response['Item'])
                    user_subscriptions.append(response['Item'])
        except Exception as e:
            print("No user subscriptions...")           

    return generate_image_urls(user_subscriptions)


def remove_subscription(artist, song_title):
    user_email = session['user_email']
    dynamodb = None
    sub_table = None
    
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url = endpoint_url_global)
        sub_table = dynamodb.Table('Subs')
        
    try:
        response = sub_table.get_item(Key = {'email' : user_email})
        print(response)
    except Exception as e:
        print(e.response['Error']['Message'])
    else:
        try:
            if response['Item']:
                for i in range(len(response['Item']['sub_songs'])):
                    if response['Item']['sub_songs'][i]['artist'] == artist and response['Item']['sub_songs'][i]['title'] == song_title:
                        print("index of removal is")
                        print(i)
                        response = sub_table.update_item(
                        Key = {
                            'email' :  user_email
                        },
                        UpdateExpression= "REMOVE sub_songs["+str(i)+"]",
                        )
                        return   
        except Exception as e:
            print("exception occoured")
            print(e)
           

@application.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@application.route('/homepage', methods = ['GET', 'POST'])
@check_user_is_logged_in
def homepage():
    error = None
    
    user_subscriptions = []
    user_subscriptions = get_user_subscriptions()
    print("user subs")
    print(user_subscriptions)
    user_data = {}
    user_data['email'] = session['user_email']
    user_data['user_name'] = session['user_name']
    user_data['sub_num'] = len(user_subscriptions)

    if request.method == 'POST':
        if request.form['action'] == 'songsearch':
            song_title =  request.form['title']  
            artist =  request.form['artist']
            year =  request.form['year']    
             #search for a song

            s_result, error = search_songs(song_title, artist, year)
            if len(s_result) > 0:
                generate_image_urls(s_result[0])
                session['search_results'] = s_result[0]
        elif request.form['action'] == 'subscribe':
            song_title =  request.form['title']  
            artist =  request.form['artist']
            add_to_subscriptions(artist, song_title)
            user_subscriptions = get_user_subscriptions()
        elif request.form['action'] == 'unsubscribe':
            song_title =  request.form['title']  
            artist =  request.form['artist']
            remove_subscription(artist, song_title)
            user_subscriptions = get_user_subscriptions()


    return render_template('homepage.html', error = error, search_results = session['search_results'], user_data = user_data, user_subscriptions=user_subscriptions)


def register_user(user_email, user_name, user_password, endpoint_url_global = None):
    error = None
    dynamodb = None
    user_table = None
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1',  endpoint_url = endpoint_url_global)
    
    try:
        user_table = dynamodb.Table('Users')
    except Exception as e:
        print("Exception Occoured at Authenticate Users: %s" % e)
 
        return "No database connection..."
    
    try:
        response = user_table.get_item( Key = {'email' : user_email})
    except ClientError as e:
        print(e.response['Error']['Message'])
        return e.response['Error']['Message']
    else:
        try:
            if response['Item']['email'] ==user_email:
                return "The email already exists"
        except Exception as e:
            new_user = {
                'email' : user_email,
                'user_name' : user_name,
                'password' : user_password
            }
            user_table.put_item(Item =new_user)

            return None

    return error

@application.route('/register', methods = ['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        user_email = request.form['loginemail']
        user_username = request.form['username']
        user_password = request.form['password']

        error = register_user(user_email, user_username, user_password)
        if error is not None:
            print(error)
            return render_template('register.html', error = error)
        else:
            print("Succesfully made a new user")
            return redirect(url_for('root'))

    return render_template('register.html',
                                  error = error)

@application.route('/', methods = ['GET', 'POST'])
def root():
    error = None
    
    
    if request.method == 'POST':
        user_email = request.form['loginemail']
        user_password = request.form['password']

        user, error = authenticate_user(user_email, user_password)
        if error is not None:
            print(error)
            return render_template('index.html', error = error)
        else:
            session['user_logged_in'] = True
            session['user_email'] = user['email']
            session['user_name'] = user['user_name']
            session['search_results'] = None
            print("Login Successful")
            return redirect(url_for('homepage'))

    return render_template('index.html',
                                  error = error)
 
if __name__ == '__main__':
   # application.run(host='127.0.0.1', port=8080, debug=True)
   application.debug = True
   application.run()
