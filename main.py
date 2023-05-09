# import relevant modules
# flask - to set up the server
# os - to get environmental variables
# json - to work with json format
from flask import Flask, request
import os
import json

# to allow cors, if else the client would get a cors error
from flask_cors import CORS, cross_origin

# Setup the server
app = Flask(__name__)

# allow cors on all of the routes
CORS(app, resources={
     r"/*": {"origins": ["https://client-production-00c5.up.railway.app"]}})

# fjernes når vi føler for det
@app.route('/', methods=['GET'])
def test():
    return 'Hei'

if __name__ == '__main__':
    app.run("0.0.0.0", debug=True, port=os.getenv("PORT", default=5000))
