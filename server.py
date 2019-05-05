import os
import mysql.connector
import geopy.distance
from mysql.connector import Error
from mysql.connector import errorcode
from hashlib import md5
from flask import Flask, abort, request, jsonify, g, url_for



# initialization
app = Flask(__name__)
dbconx = None



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
        self.password_hash = md5(password.encode('utf-8')).hexdigest()

    def verify_password(self, password):
        return md5(password.encode('utf-8')).hexdigest() == self.password_hash
    
    @staticmethod
    def search_user(email):
        #DB QUERY ---------------------------------------------------------------
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
#   |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   |   Some shitty helper functions
def parse_dbresponse(cursor):
    response = []
    records = cursor.fetchall()
    for row in records:
        d = {e2[0]: e1 for e1,e2 in zip(row, cursor.description)}
        response.append(d)
    return response

def verify_type_password(solution, answer):
    return answer.upper() == solution.upper()

def verify_geocoords(solution, longitude, latitude):
    coords = solution.split(',')
    c_long = float(coords[0])
    c_lat = float(coords[1])
    delta = float(coords[2])

    distance = geopy.distance.geodesic((c_lat, c_long),(latitude,longitude)).m

    return distance <= delta


#   |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@app.route('/lyon_quest/game/routes/', methods = ['GET'])
def get_all_routes():
    #DB QUERY ---------------------------------------------------------------
        cursor = dbconx.cursor()
        query = "SELECT * FROM route"
        cursor.execute(query)
        records = parse_dbresponse(cursor)
        routes = []
        for row in records:

            specific_query = " \
                SELECT plays.email, plays.user_comment, plays.user_rating \
                FROM plays \
                WHERE plays.route_id = '" + str(row['route_id']) + "' \
            "

            cursor.execute(specific_query)
            specific_records = parse_dbresponse(cursor)
            ratings_sum = 0
            number_of_ratings = 0
            avg = -1
            comments = []
            """
            for rt in specific_records:
                user_rating = int(rt['user_rating'])
                if(user_rating >= 0):
                    comments.append({'email' : rt['email'] , 'score' : user_rating, 'comment' : rt['user_comment']})
                    ratings_sum = ratings_sum + user_rating
                    number_of_ratings = number_of_ratings + 1
                
                
            if number_of_ratings > 0:
                avg = ratings_sum / number_of_ratings
            */
            """

            route = {
                'route_id' : row['route_id'],
                'title' : row['title'],
                'description' : row['description'],
                'avg_rating' : 4,
                'number_of_votes' : 23,
                'comments' : comments
            }

            routes.append(route)
        cursor.close()
        return jsonify({'routes' : routes})
    #DB QUERY END ------------------------------------------------------------

@app.route('/lyon_quest/game/user_route/', methods = ['POST'])
def get_user_current_route():
    #DB QUERY ---------------------------------------------------------------
        cursor = dbconx.cursor()
       
        email = request.json['email']
        query = "   SELECT *    \
                    FROM route NATURAL JOIN plays NATURAL JOIN users    \
                    WHERE current_status = 'started' AND email = '" + email + "' \
                "
        cursor.execute(query)
        records = parse_dbresponse(cursor)
        cursor.close()
        game = {
                'title' : records[0]['title'],
                'description' : records[0]['description'],
                'current_riddle' : records[0]['current_riddle']
        }
        return jsonify(game)
    #DB QUERY END ------------------------------------------------------------

@app.route('/lyon_quest/game/riddle/', methods = ['POST'])
def get_riddle_by_number():
    #DB QUERY ---------------------------------------------------------------
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
        records = parse_dbresponse(cursor)
        cursor.close()
        row = records[0]
        riddle = {
            'description' : row['description'],
            'type' : row['type']
        }
        return jsonify(riddle)
    #DB QUERY END ------------------------------------------------------------


@app.route('/lyon_quest/game/user_start_route/', methods = ['POST'])
def user_start_route():
    #DB QUERY ---------------------------------------------------------------
        cursor = dbconx.cursor()
       
        route_id = str(request.json['route_id'])
        email = request.json['email']

        delete_query = "\
                    DELETE FROM plays\
                    WHERE email = '" + email + "' AND route_id = '" + route_id + "' \
                "
        cursor.execute(delete_query)        
        
        insert_query = "\
                    INSERT INTO plays (email, route_id)\
                    VALUES ( '" + email + "', '" + route_id + "') \
                    "
        cursor.execute(insert_query)
        dbconx.commit()

        get_first_riddle_query = "\
                                SELECT * FROM riddle\
                                WHERE riddle_number = '1' AND \
                                route_id = '" + route_id + "'\
                            "

        cursor.execute(get_first_riddle_query)
        records = parse_dbresponse(cursor)
        cursor.close()
        row = records[0]

        riddle = {
            'description' : row['description'],
            'type' : row['type']
        }

        return jsonify(riddle)
    #DB QUERY END ------------------------------------------------------------

@app.route('/lyon_quest/game/verify_riddle/', methods = ['POST'])
def verifiy_riddle():
    email = request.json['email']
    route_id = str(request.json['route_id'])
    riddle_status = 'started'
    result = {}
    #DB QUERY ---------------------------------------------------------------
    cursor = dbconx.cursor()
    first_query = "\
                        SELECT riddle.riddle_number, riddle.type, riddle.solution\
                        FROM plays NATURAL JOIN route JOIN riddle\
                        WHERE plays.current_status = 'started' AND\
                            riddle.route_id = route.route_id AND\
                            riddle.riddle_number = plays.current_riddle AND\
                            plays.email = '" + email + "' AND\
                            riddle.route_id = '" + route_id + "' \
                    "
    cursor.execute(first_query)
    records = parse_dbresponse(cursor)
    row = records[0]
    riddle_number = int(row['riddle_number'])
    riddle_type = row['type']
    riddle_solution = row['solution']
    #DB QUERY END ------------------------------------------------------------
    correct = False
    if (riddle_type == 'password'):
        answer = request.json['solution']
        correct = verify_type_password(riddle_solution, answer)
    elif riddle_type == 'geocoords':
        lat = float(request.json('lat'))
        lon = float(request.json('lon'))
        correct = verify_geocoords(solution, lon, lat)
        
    if (correct):
        result['status'] = 'success'
        verify_next_riddle_query = " \
                SELECT riddle.description, riddle.type \
                FROM riddle \
                WHERE riddle.route_id = '" + route_id + "' AND \
                riddle.riddle_number = '" + str(riddle_number + 1) + "' \
            "
        cursor.execute(verify_next_riddle_query)
        records = parse_dbresponse(cursor)
        if (len(records) == 0):
            riddle_status = 'finished'
            result['finished'] = 'true'
        else:
            result['finished'] = 'false'
            result['type'] = records[0]['type']
            result['description'] = records[0]['description']
            
        
        update_user_progress_query = "\
            UPDATE plays \
            SET \
                current_status = '" + riddle_status + "', \
                current_riddle = '" + str(riddle_number + 1) + "' \
            WHERE \
                route_id = '" + route_id + "' AND \
                email = '" + email + "' \
        "

        cursor.execute(update_user_progress_query)
        dbconx.commit()
        cursor.close()

    else:
        result['status'] = 'failure'
    
    return jsonify(result)

@app.route('/lyon_quest/game/rate_route/', methods = ['POST'])
def rate_route():
     #DB QUERY ---------------------------------------------------------------
        cursor = dbconx.cursor()
        route_id = request.json['route_id']
        score = ''
        comment = ''
        if 'score' in request.json:
            score = str(request.json['score'])
        if 'comment' in request.json:
            comment = request.json['comment']

        query = " \
                UPDATE plays \
                SET \
                    user_rating = " + score + ", \
                    user_comment = '" + comment + "' \
                WHERE \
                    email = '" + request.json['email'] + "' AND\
                    route_id = '" + str(route_id) + "'\
        "

        cursor.execute(query)
        dbconx.commit()
        cursor.close()

        return jsonify({'status' : 'success'})
    #DB QUERY END ------------------------------------------------------------
@app.route('/lyon_quest/game/add_route/', methods = ['POST'])
def add_route():
    route_title = request.json['name']
    route_description = request.json['description']

    create_route_query = "\
        INSERT INTO route (title, description)\
        VALUES \
        ('" + route_title + "', '" + route_description + "') \
    "

    curosor = dbconx.cursor()
    curosor.execute(create_route_query)
    dbconx.commit()
    route_id = str(curosor.lastrowid)
    riddle_number = 1
    create_riddles_query = "INSERT INTO riddle (riddle_number, route_id , description, type, solution) VALUES"

    for riddle in request.json['riddles']:
        riddle_type = riddle['type']
        riddle_description = riddle['text']
        riddle_solution = riddle['solution']
        create_riddles_query += "(" + str(riddle_number) + ", " + route_id + ", '" + riddle_description + "', '" + riddle_type + "', '" + riddle_solution + "'),"
        riddle_number = riddle_number + 1
    curosor.execute(create_riddles_query[:-1])
    dbconx.commit()
    curosor.close()
    return jsonify({'statu' : 'success'})
##------------------------------------------------------------------------



@app.route('/lyon_quest/resource/', methods = ['GET'])
def get_resource():
    return jsonify({'data': 'Hello there!'})





if __name__ == '__main__':
    try:
        dbconx = mysql.connector.connect(host='localhost',
                                            database = 'smart',
                                            user = 'flask',
                                            password = 'flaskpass')
    except mysql.connector.Error as error :
        print("Error : {}".format(error))

    app.run(host = '0.0.0.0', port = 5000)

