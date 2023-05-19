# import relevant modules
# flask - to set up the server
# os - to get environmental variables
# json - to work with json format
from flask import Flask, request
from flask import jsonify
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
default_expire_100 = 100

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


@app.route('/contacts/vcard', methods=['GET'])
def get_all_contacts_vcard():
    URL = 'https://idg2001-oblig2-api.onrender.com/contacts/vcard'
    # increase the request count and reset the expiration --> print current count
    redis_client.incr('contact_vcard_requests')
    redis_client.expire('contact_vcard_requests', default_expire_100)
    print('request count is now: ', redis_client.get('contact_vcard_requests'))

    # check if "contacts" key exists in Redis
    if redis_client.exists('contacts_vcard'):
        print('Vcard contacts exists in redis')
        # if yes, get the value and decode it from JSON
        contacts_json = redis_client.get('contacts_vcard')
        redis_client.expire('contacts_vcard', default_expire_100)
        print('Vcard contacts sent through redis')
        contacts = json.loads(contacts_json)
        return contacts
    else:
        print('contacts vcard does not exist')
        # get the current count of contact requests
        contact_request_count = int(
            redis_client.get('contact_vcard_requests') or 0)

        # check if there have been more than 4 contact requests in the last hour
        if contact_request_count > 4:
            try:
                print('line 76')
                # Get contacts from API
                req = requests.get(URL)
                contacts_json = json.loads(req.content)
                contacts = contacts_json['message']
                # save the contacts in Redis with variable-set expiration
                redis_client.setex(
                    'contacts_vcard', contacts_expiration, json.dumps(contacts))
                print('Vcard contacts are now saved in redis...')
                print('Vcard contacts sent through database')
                return json.loads(contacts)
            except Exception as e:
                return {'message': f'Error: {e}'}, 500
        else:
            try:
                print('Vcard contacts sent through database')
                # convert ObjectId values to strings
                req = requests.get(URL)
                print(req.status_code)
                contacts_json = json.loads(req.content)
                # json_array = json.loads(req.content)
                contacts = contacts_json['message']
                return contacts
            except Exception as e:
                return {'message': f'Error: {e}'}, 500

# get all contacts from the database + handle cache


@ app.route('/contacts', methods=['GET'])
def get_all_contacts():
    URL = 'https://idg2001-oblig2-api.onrender.com/contacts'
    # Increase the request count and reset the expiration, then print the current count
    redis_client.incr('contact_requests')
    redis_client.expire('contact_requests', default_expire_100)
    print('request count is now: ', redis_client.get('contact_requests'))

    # Check if "contacts" key exists in Redis
    if redis_client.exists('contacts'):
        print('Contacts exist')
        # If yes, get the contacts value and decode it from JSON
        contacts_json = redis_client.get('contacts')
        redis_client.expire('contacts', contacts_expiration)
        print('Contacts sent through Redis')
        contacts = json.loads(contacts_json)
        return contacts
    else:
        ('contacts does not exist')
        # get the current count of contact requests
        contact_request_count = int(redis_client.get('contact_requests') or 0)

    # Check if there have been more than 4 contact requests in the last hour
    if int(contact_request_count or 0) > 4:
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

    else:
        try:
            print('Contacts sent through the database')
            # Convert ObjectId values to strings
            req = requests.get(URL)
            contacts = req.content
            return json.loads(contacts)
        except Exception as e:
            return {'message': f'Error: {e}'}, 500


@ app.route('/contacts', methods=['POST'])
def set_new_contacts():
    # Send a POST request to the main API to create new contacts
    try:
        URL = 'https://idg2001-oblig2-api.onrender.com/contacts'
        headers = {'Content-Type': 'application/json',
                   'Authorization': f'Bearer {API_KEY}'}
        data = request.get_json()  # Get the new contacts from the request body
        response = requests.post(URL, headers=headers, json=data)

        if response.status_code == 200:
            print('test', response.content)
            response_data = response.json()  # Read the response data

            json_data = response_data['json']

            # Extracting the 'vcard' value
            vcard_data = response_data['vcard']
            print('json', json_data)
            print('---------------------------')
            print('vcard', vcard_data)
            # Save the new contacts in Redis with default_expire_100 as the expiration
            redis_client.setex(
                'contacts', contacts_expiration, json_data)
            redis_client.setex(
                'contacts_vcard', contacts_expiration, vcard_data)
            print('---------hh-------')
            # return vcard_data
            return {'message': 'Contacts created successfully'}, 200
        else:
            print('oops')
            return response.json(), response.status_code

    except Exception as e:
        return {'message': f'Error: {e}'}, 500


# GET one contacts in JSON format
@app.route("/contacts/<id>", methods=["GET"])
def get_contact_JSON_route(id):
    URL = f'https://idg2001-oblig2-api.onrender.com/contacts/{id}'
    print(URL)
    if redis_client.exists(f'contact_{id}'):
        print('Contacts exist')
        contact = redis_client.get(f'contact_{id}')
        return json.loads(contact)
    try:
        req = requests.get(URL)
        contact = req.content
        print(contact)
        redis_client.setex(
            f'contact_{id}', contacts_expiration, contact)
        return json.loads(contact)
    except Exception as e:
        return {'message': f'Error: {e}'}, 500

# GET contact by id and visualize in vcard format inside a JSON structure
@app.route("/contacts/<id>/vcard", methods=["GET"])
def get_contact_vcard_route(id):
    URL = f'https://idg2001-oblig2-api.onrender.com/contacts/{id}/vcard'
    print(URL)
    if redis_client.exists(f'contact_vcard_{id}'):
        print('Contacts exist')
        contact = redis_client.get(f'contact_vcard_{id}')
        return json.loads(contact)
    try:
        req = requests.get(URL)
        contact_json = json.loads(req.content)
        contact = contact_json['message']
        print(contact)
        redis_client.setex(
            f'contact_vcard_{id}', contacts_expiration, json.dumps(contact))
        return contact
    except Exception as e:
        return {'message': f'Error: {e}'}, 500

    # run server
if __name__ == '__main__':
    app.run("0.0.0.0", debug=True, port=os.getenv("PORT", default=5000))
