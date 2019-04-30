#!/usr/bin/env python
import os
from hashlib import md5
from flask import Flask, abort, request, jsonify, g, url_for


# initialization
app = Flask(__name__)
db = [
    {
        'username' : 'suka',
        'password_hash' : '1937f167ce4a58749368ca8e815336da' #suka
    },
    {
        'username' : 'puta',
        'password_hash' : '2309f522cab926b42f4463fc656bd87f' #madre
    }
]

def search_user(username):
    for user in db:
        if user['username'] == username:
            return User(username, user['password'])
    return None


class User:

    def __init__(self, username, password_hash = ''):
        self.username = username
        self.password_hash = password_hash

    def hash_password(self, password):
        self.password_hash = md5(password).hexdigest()

    def verify_password(self, password):
        return md5(password).hexdigest() == self.password_hash
    
    @staticmethod
    def search_user(username):
        for user in db:
            if user['username'] == username:
                return User(username, user['password_hash'])
        return None
    @staticmethod
    def add_user(user):
        db.append({
            'username' : user.username,
            'password_hash' : user.password_hash
        })
    @staticmethod
    def update_user(user):
        for idx, old_user in enumerate(db):
            if old_user['username'] == user.username:
                old_user['password_hash'] = user.password_hash  


@app.route('/lyon_quest/users/login/', methods=['POST'])
def verify_login():
    user = User.search_user(request.json['username'])
    if not user or not user.verify_password(request.json['password']):
        return jsonify({'status' : 'failure', 'error' : 'You have entered an invalid username or password'})
    g.user = user
    return jsonify({'status' : 'success'})


@app.route('/lyon_quest/users/register/', methods=['POST'])
def new_user():
    username = request.json['username']
    password = request.json['password']

    if User.search_user(username) is not None:
       return jsonify({'status' : 'failure', 'error' : 'This username is already used'})
    user = User(username = username)
    user.hash_password(password)
    User.add_user(user)
    return jsonify({'status' : 'success'})

@app.route('/lyon_quest/users/change_password/', methods=['POST'])
def change_password():
    username = request.json['username']
    old_password = request.json['old_password']
    new_password = request.json['new_password']

    user = User.search_user(username)
    if not user.verify_password(old_password):
       return jsonify({'status' : 'failure', 'error' : 'Wrong password'})

    user.hash_password(new_password)
    User.update_user(user)
    return jsonify({'status' : 'success'})


@app.route('/lyon_quest/resource/', methods = ['GET'])
def get_resource():
    return jsonify({'data': 'Hello there!'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT',33507)) # Default port
    app.run(port = port)
    
