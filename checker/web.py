#!/usr/bin/python2
from base64 import b64decode
from flask import abort, Flask, Response, render_template, make_response, request
import random
import argparse
import MySQLdb
from hashlib import sha512
import random

app = Flask(__name__,static_folder="/templates")
app.secret_key = str(random.getrandbits(2048))

def run_web(host, port, db_host, db_user, db_pwd):
  print("### WEB ###")

  app.config['db_host'] = db_host
  app.config['db_user'] = db_user
  app.config['db_pwd'] = db_pwd
  app.config['db'] = MySQLdb.connect(
      host=app.config['db_host'],
      user=app.config['db_user'],
      passwd=app.config['db_pwd'],
      db='ctf')
  app.run(host=host, port=port)


@app.route("/cookie.js")
def script1():
  with open("templates/cookie.js", "r") as r:
    return Response(r.read(), mimetype="text/javascript")

@app.route("/")
def index():
  title = "InnoCTF"
  cursor = app.config['db'].cursor()
  res = cursor.execute("select name, score, regdate from user;")
  participants = cursor.fetchall()
  sorted(participants, key=lambda x: x[1])
  participants = [(name,score,regdate.strftime("%Y-%m-%d %H:%M:%S")) for name,score,regdate in participants]

  if request.cookies:
    token = request.cookies['token']
    if len(token) != 128:
      resp = make_response(render_template('index.html', 
        title=title
      ))
      resp.set_cookie('token', '', expires=0)
      return resp
    
    resp = make_response(render_template('index.html',  
      title=title,
      token=token,
      participants=participants,
      registered=True
    ))
    return resp
  else:
    resp = make_response(render_template('index.html', 
        title=title,
        registered=False,
        participants=participants
      ))
    return resp

@app.route("/register", methods=["POST"])
def register():
  try:
    name = request.form["name"]
    if len(name) == 0 or len(name) > 45:
      abort(400)

    name = b64decode(name)

    secret = str(random.getrandbits(1024)) + str(name)
    secret = sha512(secret).hexdigest()
    
    cursor = app.config['db'].cursor()
    try:
      cursor.execute("insert into user(token, name) values(%s, %s);", (str(secret), str(name),))
      app.config['db'].commit()
    except Exception as e:
      print(e)
      app.config['db'].rollback()
      abort(make_response("This user already exists", 400))
    cursor.close()

    return secret
  except Exception as e:
    print(e)
    abort(make_response("Something terrible happened", 400))


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Scoreboard')
  
  ## web settings
  parser.add_argument('host', type=str, default='0.0.0.0', help='default is 0.0.0.0')
  parser.add_argument('port', type=int, default=8080, help='default is 8080')

  ## db settings
  parser.add_argument('db_host', default='127.0.0.1', type=str,
                      help='default is 127.0.0.1')
  parser.add_argument('db_user', default='root', type=str,
                      help='mysql user, default root')
  parser.add_argument('db_password', type=str, 
                      help='mysql password')
  args = parser.parse_args()

  run_web(
    args.host, 
    args.port,
    args.db_host,
    args.db_user,
    args.db_password
  )
  