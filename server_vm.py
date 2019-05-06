#!/usr/bin/env python
import os
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
from hashlib import md5
from flask import Flask, abort, request, jsonify, g, url_for


# initialization
app = Flask(__name__)
dbconx = None


#to call each time we connect to MySQL data-base
def connect_db():
    try:
        global dbconx
        dbconx = mysql.connector.connect(host='localhost',
                                         database = 'smart',
                                         user = 'flask',
                                         password = 'flaskpass')
    except mysql.connector.Error as error :
        print("Failed inserting record into python_users table {}".format(error))


##------------------------------------------------------------------------
#   |   This section is dedicated for services responsible for users managment
#   |
#   |
#   |

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
        #DB QUERY ---------------------------------------------------------------
        
        global dbconx # to have access to the global instance of dbconx
        if dbconx is None:
            connect_db() # connect to the DB
        
        cursor = dbconx.cursor()
        cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
        records = cursor.fetchall()
        cursor.close()
        #DB QUERY END ------------------------------------------------------------
        for user in records:
            if user[0] == email:
                return User(email = email,username = user[1], password_hash = user[2])
        return None
    @staticmethod
    def add_user(user):
        #DB QUERY ---------------------------------------------------------------
        
        global dbconx # to have access to the global instance of dbconx
        if dbconx is None:
            connect_db() # connect to the DB
        
        cursor = dbconx.cursor()
        query = "INSERT INTO users (email, username, pass_hash)\
            VALUES(\
                '" + user.email + "','" + user.username + "','" + user.password_hash +"'\
            )"
        cursor.execute(query)
        dbconx.commit()
        cursor.close()
        #DB QUERY END ------------------------------------------------------------

@app.route('/lyon_quest/users/login/', methods=['POST'])
def verify_login():
    user = User.search_user(request.json['email'])
    if not user or not user.verify_password(request.json['password']):
        return jsonify({'status' : 'failure', 'error' : 'You have entered an invalid email or password'})
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


##------------------------------------------------------------------------
#   |   This section is dedicated for services responsible for routes and riddles managment
#   |
#   |
#   |


@app.route('/lyon_quest/game/routes/', methods = ['GET'])
def get_all_routes():
    #DB QUERY ---------------------------------------------------------------
        
        global dbconx # to have access to the global instance of dbconx
        if dbconx is None:
            connect_db() # connect to the DB
        
        cursor = dbconx.cursor()
        query = "SELECT * FROM route"
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        routes = []
        for row in records:
            route = {
                'route_id' : row[0],
                'title' : row[1],
                'description' : row[2]
            }

            routes.append(route)
        return jsonify({'routes' : routes})
    #DB QUERY END ------------------------------------------------------------

@app.route('/lyon_quest/game/user_route/', methods = ['POST'])
def get_user_current_route():
    #DB QUERY ---------------------------------------------------------------
        
        global dbconx # to have access to the global instance of dbconx
        if dbconx is None:
            connect_db() # connect to the DB
        
        cursor = dbconx.cursor()
       
        email = request.json['email']
        query = "   SELECT *    \
                    FROM route NATURAL JOIN plays NATURAL JOIN users    \
                    WHERE current_status = 'started' AND email = '" + email + "' \
                "
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        game = {
                'title' : records[0][2],
                'description' : records[0][3],
                'current_riddle' : records[0][4]
        }
        return jsonify(game)
    #DB QUERY END ------------------------------------------------------------

@app.route('/lyon_quest/game/riddle/', methods = ['POST'])
def get_riddle_by_number():
    #DB QUERY ---------------------------------------------------------------
        
        global dbconx # to have access to the global instance of dbconx
        if dbconx is None:
            connect_db() # connect to the DB
        
        cursor = dbconx.cursor()
       
        riddle_number = request.json['riddle_number']
        route = request.json['route_id']
        query = "SELECT * \
                FROM route JOIN riddle WHERE \
                route.route_id = riddle.route_id AND\
                route.route_id = '" + route + "' \
                AND riddle_number = '" + riddle_number + "'\
                "
        cursor.execute(query)
        records = cursor.fetchall()
        row = records[0]
        riddle = {
            'description' : row[5],
            'type' : row[6]
        }
        return jsonify(riddle)
    #DB QUERY END ------------------------------------------------------------


@app.route('/lyon_quest/game/user_start_route/', methods = ['POST'])
def user_start_route():
    #DB QUERY ---------------------------------------------------------------
        
        global dbconx # to have access to the global instance of dbconx
        if dbconx is None:
            connect_db() # connect to the DB
        
        cursor = dbconx.cursor()
       
        route_id = str(request.json['route_id'])
        email = request.json['email']

        delete_query = "\
                    DELETE FROM plays\
                    WHERE email = '" + email + "' AND route_id = '" + route_id + "' \
                "
        print delete_query
        cursor.execute(delete_query)        
        
        insert_query = "\
                    INSERT INTO plays (email, route_id)\
                    VALUES ( '" + email + "', '" + route_id + "') \
                    "
        print insert_query
        cursor.execute(insert_query)
        dbconx.commit()

        get_first_riddle_query = "\
                                SELECT * FROM riddle\
                                WHERE riddle_number = '1' AND \
                                route_id = '" + route_id + "'\
                            "

        cursor.execute(get_first_riddle_query)
        records = cursor.fetchall()
        row = records[0]

        riddle = {
            'description' : row[2],
            'type' : row[3]
        }

        print riddle
        return jsonify(riddle)
    #DB QUERY END ------------------------------------------------------------

##------------------------------------------------------------------------



@app.route('/lyon_quest/resource/', methods = ['GET'])
def get_resource():
    return jsonify({'data': 'Hello there!'})

# no need for '__main__' when online
