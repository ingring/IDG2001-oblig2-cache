# import relevant modules
from flask import Flask, request
from flask import jsonify
import os
import json
from dotenv import load_dotenv
# from database import db
# to allow cors, if else the client would get a cors error
from flask_cors import CORS
import redis
import requests

#expiration times
short_expiration = 100
one_day_expiration = 86400
default_expire_100 = 100

#limit for when to save in redis
default_req_limit = 4

#max limit before the cache will update
default_req_update_limit = 20

load_dotenv()
# Setup the server
app = Flask(__name__)

API_KEY = os.getenv('API_KEY')
print(API_KEY)


# Checks if it is the right key
def check_api_key():
    # Checks if it exists a key variable at all
    if not API_KEY:
        raise ValueError("API_KEY environment variable not set")

    key = request.args.get("key")
    print("dotenv", repr(API_KEY))
    print("key", repr(key))

    if key is None:
        print("API key is missing")
        return "API key is missing"

    if key != API_KEY:
        print("Invalid API key")
        return "Invalid API key"

    return

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


# get all contacts in vcard format from the database + handle cache
@app.route('/contacts/vcard', methods=['GET'])
def get_all_contacts_vcard():
    error = check_api_key()
    if error:
        return jsonify(error)
    URL = f'https://idg2001-oblig2-api.onrender.com/contacts/vcard?key={API_KEY}'

    # increase the request count and reset the expiration --> print current count
    redis_client.incr('contact_vcard_requests')
    redis_client.expire('contact_vcard_requests', default_expire_100)
    print('request count is now: ', redis_client.get('contact_vcard_requests'))
    contact_request_count = int(
            redis_client.get('contact_vcard_requests') or 0)

    # check if "contacts" key exists in Redis
    if redis_client.exists('contacts_vcard'):
        print('Vcard contacts exists in redis')
        if contact_request_count > default_req_update_limit:
            #updating the redis since there are many request since the last update
            try:
                print('------updating redis')
                # Get contacts from API
                req = requests.get(URL)
                contacts_json = json.loads(req.content)
                contacts = contacts_json['message']
                # save the contacts in Redis with variable-set expiration
                dump_contacts = json.dumps(contacts)
                redis_client.setex(
                    'contacts_vcard', short_expiration, dump_contacts)
                redis_client.setex('contact_vcard_requests', default_expire_100, 1)
                print('Vcard contacts are now saved in redis...')
                print('Vcard contacts sent through database')
                return json.loads(dump_contacts)
            except Exception as e:
                return {'message': f'Error: {e}'}, 500
        # if yes, get the value and decode it from JSON
        contacts_json = redis_client.get('contacts_vcard')
        redis_client.expire('contacts_vcard', default_expire_100)
        print('Vcard contacts sent through redis')
        contacts = json.loads(contacts_json)
        return contacts
    else:
        print('contacts vcard does not exist')


        # check if there have been more than 4 contact requests in the last hour

        if contact_request_count > default_req_limit:

            try:
                print('line 76')
                # Get contacts from API
                req = requests.get(URL)
                contacts_json = json.loads(req.content)
                contacts = contacts_json['message']
                dump_contacts = json.dumps(contacts)
                # save the contacts in Redis with variable-set expiration
                redis_client.setex(
                    'contacts_vcard', short_expiration, dump_contacts)
                print('Vcard contacts are now saved in redis...')
                print('Vcard contacts sent through database')
                return json.loads(dump_contacts)
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
    error = check_api_key()
    if error:
        return jsonify(error)
    URL = f'https://idg2001-oblig2-api.onrender.com/contacts?key={API_KEY}'

    # Increase the request count and reset the expiration, then print the current count
    redis_client.incr('contact_requests')
    redis_client.expire('contact_requests', default_expire_100)
    print('request count is now: ', redis_client.get('contact_requests'))
    contact_request_count = int(redis_client.get('contact_requests') or 0)

    # Check if "contacts" key exists in Redis
    if redis_client.exists('contacts'):
        if int(contact_request_count or 0) > default_req_update_limit:
            try:
                print('Updating redis...')
                # Get contacts from API with API key in the headers
                req = requests.get(URL)
                contacts = req.content
                # Save the contacts in Redis with a variable-set expiration
                redis_client.setex('contacts', default_expire_100, contacts)
                redis_client.setex('contact_requests', default_expire_100, 1)
                print('Contacts are now saved in Redis...')
                print('Contacts sent through Redis')
                return contacts
            except Exception as e:
                return {'message': f'Error: {e}'}, 500
        print('Contacts exist')
        # If yes, get the contacts value and decode it from JSON
        contacts_json = redis_client.get('contacts')
        redis_client.expire('contacts', default_expire_100)
        print('Contacts sent through Redis')
        contacts = json.loads(contacts_json)
        return contacts
    #contacts does not exist
    ('contacts does not exist')
    # get the current count of contact requests
    # Check if there have been more than default request limit (4) contact requests in the last hour
    if int(contact_request_count or 0) > default_req_limit:
        try:
            print('Line 76')
            # Get contacts from API with API key in the headers
            req = requests.get(URL)
            contacts = req.content
            # Save the contacts in Redis with a variable-set expiration
            redis_client.setex('contacts', default_expire_100, contacts)
            print('Contacts are now saved in Redis...')
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


# Send a POST request to the main API to create new contacts
@ app.route('/contacts', methods=['POST'])
def set_new_contacts():
    error = check_api_key()
    if error:
        return jsonify(error)
    try:
        URL = f'https://idg2001-oblig2-api.onrender.com/contacts?key={API_KEY}'
        headers = {'Content-Type': 'application/json'}
        data = request.get_json()  # Get the new contacts from the request body
        response = requests.post(URL, headers=headers, json=data)

        if response.status_code == 200:
            print('test', response.content)
            response_data = response.json()  # Read the response data

            json_data = response_data['json']
            vcard_data = response_data['vcard']
            # Extracting the 'vcard' value

            # Save the new contacts in Redis with default_expire_100 as the expiration
            redis_client.setex(
                'contacts', default_expire_100, json_data)
            redis_client.setex(
                'contacts_vcard', default_expire_100, vcard_data)
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
    error = check_api_key()
    if error:
        return jsonify(error)
    URL = f'https://idg2001-oblig2-api.onrender.com/contacts/{id}?key={API_KEY}'
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
            f'contact_{id}', default_expire_100, contact)
        return json.loads(contact)
    except Exception as e:
        return {'message': f'Error: {e}'}, 500


# GET contact by id and visualize in vcard format inside a JSON structure
@app.route("/contacts/<id>/vcard", methods=["GET"])
def get_contact_vcard_route(id):
    error = check_api_key()
    if error:
        return jsonify(error)
    URL = f'https://idg2001-oblig2-api.onrender.com/contacts/{id}/vcard?key={API_KEY}'
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
            f'contact_vcard_{id}', default_expire_100, json.dumps(contact))
        return contact
    except Exception as e:
        return {'message': f'Error: {e}'}, 500

    # run server
if __name__ == '__main__':
    app.run("0.0.0.0", debug=True, port=os.getenv("PORT", default=5000))
