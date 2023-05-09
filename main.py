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


# add contact in database
@app.route('/tools', methods=['GET'])
def get_all_tools():
    print(redis_client.get('tool_requests'), 'inc')
    # check if "tools" key exists in Redis
    if redis_client.exists('tools'):
        # if yes, get the value and decode it from JSON
        tools_json = redis_client.get('tools')
        redis_client.expire('tools', tools_expiration)
        print('Tools sent through redis')
        tools = json.loads(tools_json)
        return tools
    else:

        # increment the tool request counter in Redis and set the TTL from a varibale
        redis_client.incr('tool_requests')
        redis_client.expire('tool_requests', tools_request_count_expiration)

        # get the current count of tool requests
        tool_request_count = int(redis_client.get('tool_requests') or 0)

        # check if there have been more than 4 tool requests in the last hour
        if tool_request_count > 4:
            try:
                tools = list(db['tools'].find())
                # convert ObjectId values to strings
                for tool in tools:
                    tool['_id'] = str(tool['_id'])
                # save the tools in Redis with variable-set expiration
                redis_client.setex(
                    'tools', tools_expiration, json.dumps(tools))
                print('Tools are now saved in redis...')
                print('Tools sent through database')
                return tools
            except Exception as e:
                return {'message': f'Error: {e}'}, 500
        else:
            try:
                tools = list(db['tools'].find())
                print('Tools sent through database')
                # convert ObjectId values to strings
                for tool in tools:
                    tool['_id'] = str(tool['_id'])
                return tools
            except Exception as e:
                return {'message': f'Error: {e}'}, 500


# run server
if __name__ == '__main__':
    app.run("0.0.0.0", debug=True, port=os.getenv("PORT", default=5000))
