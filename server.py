#!/usr/bin/env python
import os
from hashlib import md5
from flask import Flask, abort, request, jsonify, g, url_for


# initialization
app = Flask(__name__)
db = [
    {
        'email' : 'suka@gmail.com',
        'username' : 'suka',
        'password_hash' : '1937f167ce4a58749368ca8e815336da' #suka
    },
    {
        'email' : 'puta@gmail.com', 
        'username' : 'puta',
        'password_hash' : '2309f522cab926b42f4463fc656bd87f' #madre
    }
]

def search_user(email):
    for user in db:
        if user['email'] == email:
            return User(email, user['username'], user['password'])
    return None


class User:

    def __init__(self, email, username, password_hash = ''):
        self.email = email
        self.username = username
        self.password_hash = password_hash

    def hash_password(self, password):
        self.password_hash = md5(password).hexdigest()

    def verify_password(self, password):
        return md5(password).hexdigest() == self.password_hash
    
    @staticmethod
    def search_user(email):
        for user in db:
            if user['email'] == email:
                return User(email = email,username = user['username'], password_hash = user['password_hash'])
        return None
    @staticmethod
    def add_user(user):
        db.append({
            'email' : user.email,
            'username' : user.username,
            'password_hash' : user.password_hash
        })


@app.route('/lyon_quest/users/login/', methods=['POST'])
def verify_login():
    user = User.search_user(request.json['email'])
    if not user or not user.verify_password(request.json['password']):
        return jsonify({'status' : 'failure', 'error' : 'You have entered an invalid email or password'})
    g.user = user
    return jsonify({'status' : 'success'})


@app.route('/lyon_quest/users/register/', methods=['POST'])
def new_user():
    email = request.json['email']
    username = request.json['username']
    password = request.json['password']

    if User.search_user(email) is not None:
       return jsonify({'status' : 'failure', 'error' : 'This email is already used'})
    user = User(email = email, username = username)
    user.hash_password(password)
    User.add_user(user)
    return jsonify({'status' : 'success'})

@app.route('/lyon_quest/resource/', methods = ['GET'])
def get_resource():
    return jsonify({'data': 'Hello there!'})


if __name__ == '__main__':
    port = 5000 # Default port
    app.run(host = '0.0.0.0', port = os.environ.get('PORT', 5000))
