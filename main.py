# import relevant modules
# flask - to set up the server
# os - to get environmental variables
# json - to work with json format
from flask import Flask, request
import os
import json
from dotenv import load_dotenv
from database import db
# to allow cors, if else the client would get a cors error
from flask_cors import CORS, cross_origin
import redis
import requests


contacts_expiration = 90
contacts_request_count_expiration = 90

load_dotenv()
# Setup the server
app = Flask(__name__)

API_KEY = os.getenv('API_KEY')

if os.environ.get('RAILWAY_ENV'):
    redis_url = os.environ.get('REDIS_URL')
    print(f"Connecting to Redis at {redis_url} (railway)")
    redis_client = redis.from_url(redis_url)
else:
    redis_client = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv(
        'REDIS_PORT'), db=os.getenv('REDIS_DB'))
    print(
        f"Connecting to Redis at {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')} with DB {os.getenv('REDIS_DB')}")


# allow cors on all of the routes
CORS(app, resources={
     r"/*": {"origins": ["*"]}})


@app.route('/', methods=['GET'])
def test():
    return 'Hei'


@app.route('/render', methods=['GET'])
def get_tools_from_api():
    req = requests.get('https://idg2001-oblig2-api.onrender.com/contacts')
    print(req.content)
    return req.content


# get all contacts from the database + handle cache
@app.route('/contacts', methods=['GET'])
def get_all_contacts():
    URL = 'https://idg2001-oblig2-api.onrender.com/contacts'
    # Increase the request count and reset the expiration, then print the current count
    redis_client.incr('contact_requests')
    redis_client.expire('contact_requests', 100)
    print('Request count is now:', redis_client.get('contact_requests'))

    # Check if "contacts" key exists in Redis
    if redis_client.exists('contacts'):
        print('Contacts exist')
        # If yes, get the contacts value and decode it from JSON
        contacts_json = redis_client.get('contacts')
        redis_client.expire('contacts', contacts_expiration)
        print('Contacts sent through Redis')
        contacts = json.loads(contacts_json)
        return contacts

    # Check if there have been more than 4 contact requests in the last hour
    if int(redis_client.get('contact_requests') or 0) > 4:
        try:
            print('Line 76')
            # Get contacts from API with API key in the headers
            headers = {'Authorization': f'Bearer {API_KEY}'}
            req = requests.get(URL, headers=headers)
            contacts = req.content
            # Save the contacts in Redis with a variable-set expiration
            redis_client.setex('contacts', contacts_expiration, contacts)
            print('Contacts are now saved in Redis...')
            print('Contacts sent through the database')
            return json.loads(contacts)
        except Exception as e:
            return {'message': f'Error: {e}'}, 500

    try:
        print('Contacts sent through the database')
        # Convert ObjectId values to strings
        req = requests.get(URL)
        contacts = req.content
        return json.loads(contacts)
    except Exception as e:
        return {'message': f'Error: {e}'}, 500


# POST
    # 1: sende post request til mainApi
    # 2:
        # if(200). (main API må sende tilbake oppdatert tools).
            # Lagre disse tools i redis
            # Sende tilbake 200 ok
        # if(400) returnere failemdelingen som kom fra main


# run server
if __name__ == '__main__':
    app.run("0.0.0.0", debug=True, port=os.getenv("PORT", default=5000))
