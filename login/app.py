from flask import Flask, render_template, request, jsonify, make_response, json, send_from_directory, redirect, url_for
from flask_restful import Api, Resource
import pymongo
import bcrypt
import numpy
import tensorflow as tf
import requests
import subprocess
import json
import pika
import publisher

app = Flask(__name__)

#client = MongoClient("mongodb://db:27017")
#db = client.IRG
#users = db["Users"]

myclient = pymongo.MongoClient('mongodb://192.168.0.40:27017/')  
mydb = myclient["UserList"]
mycol = mydb["User"]



def UserExist(username):
    if mycol.find({"Username":username}).count() == 0:
        return False
    else:
        return True

@app.route('/register', methods=['POST'])
def regis():
    #Step 1 is to get posted data by the user
    postedData = request.get_json()

    #Get the data
    username = postedData["username"]
    password = postedData["password"] #"123xyz"

#push username and password
    connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='192.168.0.40'))
    channel = connection.channel()

    if UserExist(username):
        retJson = {
            'status':301,
            'msg': 'Invalid Username'
        }
        return jsonify(retJson)

    hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

    #Store username and pw into the database
    mycol.insert({
        "Username": username,
        "Password": hashed_pw,
        "Tokens":10
    })

    retJson = {
        "status": 200,
        "msg": "You successfully signed up for the API"
    }
    return jsonify(retJson)

def verifyPw(username, password):
    if not UserExist(username):
        return False

    hashed_pw = mycol.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def generateReturnDictionary(status, msg):
    retJson = {
        "status": status,
        "msg": msg
    }
    return retJson

def verifyCredentials(username, password):
    if not UserExist(username):
        return generateReturnDictionary(301, "Invalid Username"), True

    correct_pw = verifyPw(username, password)

    if not correct_pw:
        return generateReturnDictionary(302, "Incorrect Password"), True

    return None, False

@app.route('/classify', methods=['POST'])
def classify():
    postedData = request.get_json()

    username = postedData["username"]
    password = postedData["password"]
    url = postedData["url"]

    retJson, error = verifyCredentials(username, password)
    if error:
        return jsonify(retJson)

    tokens = mycol.find({
        "Username":username
    })[0]["Tokens"]

    if tokens<=0:
        return jsonify(generateReturnDictionary(303, "Not Enough Tokens"))

    r = requests.get(url)
    retJson = {}
    with open('temp.jpg', 'wb') as f:
        f.write(r.content)
        proc = subprocess.Popen('python classify_image.py --model_dir=. --image_file=./temp.jpg', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        ret = proc.communicate()[0]
        proc.wait()
        with open("text.txt") as g:
            retJson = json.load(g)


    mycol.update({
        "Username": username
    },{
        "$set":{
            "Tokens": tokens-1
        }
    })

    return retJson

@app.route('/refill', methods=['POST'])
def refill():
    postedData = request.get_json()

    username = postedData["username"]
    password = postedData["admin_pw"]
    amount = postedData["amount"]

    if not UserExist(username):
        return jsonify(generateReturnDictionary(301, "Invalid Username"))

    correct_pw = "abc123"
    if not password == correct_pw:
        return jsonify(generateReturnDictionary(302, "Incorrect Password"))

    mycol.update({
        "Username": username
    },{
        "$set":{
            "Tokens": amount
        }
    })
    return jsonify(generateReturnDictionary(200, "Refilled"))

if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000)
