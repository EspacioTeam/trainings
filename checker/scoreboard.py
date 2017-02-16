from flask import Flask, redirect
from flask import render_template
from flask import jsonify
from flask import request
import hashlib
import sys
import datetime

import sqlite3
from flask import g
DATABASE = 'scoreboard.db'

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert(table, fields=(), values=()):
    # g.db is the database connection
    db = get_db()
    query = 'INSERT INTO %s (%s) VALUES (%s)' % (
        table,
        ', '.join(fields),
        ', '.join(['?'] * len(values))
    )
    db.cursor().execute(query, values)
    db.commit()

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    #cur = get_db().cursor()
    users = []
    for user in query_db('select * from users ORDER BY score DESC'):
        users.append(user)
    #print(users, file=sys.stderr)
    return render_template('index.html', users=users, round="1")

@app.route('/reg', methods=['POST'])
def reg():
    if(len(request.form['username']) > 2):
        #cur = get_db().cursor()
        check = query_db('select guid FROM users WHERE username=?', [request.form['username']], one=True)
        if check is None:
            #print ('No such user')
            now = datetime.datetime.now()
            user = {}
            user['username'] = request.form['username']
            user['token'] = hashlib.sha512(str(now).encode('utf-8')).hexdigest()
            user['date'] = str(now)
            #print(type(user.keys()), file=sys.stderr)
            insert('users', list(user.keys()), list(user.values()))
            return render_template('reg.html', token=user['token'])
        else:
            return redirect('/')


app.debug = True
app.run(host="0.0.0.0", port=9000, threaded=True)
