from flask import Flask, request, jsonify, make_response, json, send_from_directory, redirect, url_for
import pymongo
import json
import sys
#import database1
import pika
import logging
import warnings
import bcrypt

# packages for swagger
from flasgger import Swagger
from flasgger import swag_from

# setup flask app
app = Flask(__name__)

# setup swagger online document
swagger = Swagger(app)

# setup logger
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
warnings.filterwarnings("ignore", category=DeprecationWarning)

data = {"key":"this is defualt"}
db_add = "mongodb://192.168.0.40:27017/"

@app.route('/listuser',methods=['GET'])
@swag_from('apidocs/api_list_user.yml')
def listuser():
    myclient = pymongo.MongoClient("mongodb://192.168.0.40:27018/")
    mydb = myclient["UserList"]
    users = mydb["User"]

    
    user1 = []
    for x in users.find():
        user1.append({'id':str(x['_id']),'Username' : x['Username'],'Tokens' : x['Tokens']})
    return jsonify(user1)


@app.route('/')
def index():
    return 'Web App with Python Flask!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
