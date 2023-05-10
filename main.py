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


tools_expiration = 90
tools_request_count_expiration = 90

load_dotenv()
# Setup the server
app = Flask(__name__)

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


# get all tools from the database + handle cache
@app.route('/tools', methods=['GET'])
def get_all_tools():
    # increase the request count and reset the expiration --> print current count
    redis_client.incr('tool_requests')
    redis_client.expire('tool_requests', 100)
    print('request count is now: ', redis_client.get('tool_requests'))

    # check if "tools" key exists in Redis
    if redis_client.exists('tools'):
        print('tools exists')
        # if yes, get the value and decode it from JSON
        tools_json = redis_client.get('tools')
        redis_client.expire('tools', tools_expiration)
        print('Tools sent through redis')
        tools = json.loads(tools_json)
        return tools
    else:
        ('tools does not exist')
        # get the current count of tool requests
        tool_request_count = int(redis_client.get('tool_requests') or 0)

        # check if there have been more than 4 tool requests in the last hour
        if tool_request_count > 4:
            try:
                print('line 76')
                # Get tools from API
                req = requests.get(
                    'https://idg2001-oblig2-api.onrender.com/contacts')
                tools = req.content
                # save the tools in Redis with variable-set expiration
                redis_client.setex(
                    'tools', tools_expiration, tools)
                print('Tools are now saved in redis...')
                print('Tools sent through database')
                return json.loads(tools)
            except Exception as e:
                return {'message': f'Error: {e}'}, 500
        else:
            try:
                print('Tools sent through database')
                # convert ObjectId values to strings
                req = requests.get(
                    'https://idg2001-oblig2-api.onrender.com/contacts')
                tools = req.content
                return json.loads(tools)
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
