#!/usr/bin/env python3
# from __future__ import print_function # In python 2.7
import sys
print(sys.version)

from base64 import b64decode
from flask import abort, Flask, Response, render_template, make_response, request
import random
import argparse
import MySQLdb
from hashlib import sha512
import random

app = Flask(__name__,static_folder="/templates")
app.secret_key = str(random.getrandbits(2048))

import docker
dclient = docker.APIClient(base_url='unix://var/run/docker.sock')
# dclient.containers.run("ubuntu:latest", "echo hello world")
# dclient =docker.from_env()
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
  app.run(host=host, port=port, debug=True)


@app.route("/confirm/<name>")
def confirm(name):
  try:
    ip = request.remote_addr
    print(ip)
    cursor = app.config['db'].cursor()
    cursor.execute("select id from user where name=%s", (name,))
    ids = cursor.fetchone()
    if ids:
      cursor.execute("update user set host=%s where id=%s", (ids,))
      cursor.commit()
    cursor.close()
    return "success"

  except:
    app.config['db'].rollback()
    abort(400)

@app.route("/cookie.js")
def script1():
  with open("templates/cookie.js", "r") as r:
    return Response(r.read(), mimetype="text/javascript")

@app.route("/logout", methods=["POST"])
def logout():
    token = request.cookies.get('token')
    if token and len(token) == 64:
        container = dclient.containers.get(token)
        container.stop()
        container.remove(force=True)
        return Response("OK", content_type='application/json; charset=utf-8')
    else:
        return Response("ERR", content_type='application/json; charset=utf-8')
#    return Response("ERR", content_type='application/json; charset=utf-8')

@app.route("/")
def index():
  title = "InnoCTF"
  cursor = app.config['db'].cursor()
  res = cursor.execute("select name, score, status, host, regdate from user order by score desc;")
  participants = cursor.fetchall()
  sorted(participants, key=lambda x: x[1])
  participants = [(name,score,status,host,regdate.strftime("%Y-%m-%d %H:%M:%S")) for name,score,status,host,regdate in participants]
  
  if request.cookies:
    token = request.cookies['token']
    if len(token) != 64:
      resp = make_response(render_template('index.html', 
        title=title
      ))
      resp.set_cookie('token', '', expires=0)
      return resp
    
    # test = dclient.inspect_container(token)['NetworkSettings']['Ports']['22/tcp'][0]['HostPort']
    # print(str(test), file=sys.stderr)
    resp = make_response(render_template('index.html',  
      title=title,
      token=token,
      participants=participants,
      port=dclient.port(token, 22),
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

    container = dclient.create_container(
	image="sibirctf2015-crychat",
	cpu_shares=100,
	detach=True,
	host_config=dclient.create_host_config(
		port_bindings={'22/tcp': "5010-5050"},
		restart_policy={"Name": "always"},
		cpuset_cpus="0-3",
		mem_limit="512m"
	)
    )
    # secret = str(random.getrandbits(1024)) + str(name)
    # secret = sha512(secret).hexdigest()
    secret = container['Id']
    host = dclient.inspect_container(secret)['NetworkSettings']['IPAddress']
    port = dclient.port(secret, 22)
    print(str(secret), host, port, file=sys.stderr)
    cursor = app.config['db'].cursor()
    try:
      cursor.execute("insert into user(token, host, name) values(%s, %s, %s);", (str(secret), str(host), str(name),))
      app.config['db'].commit()
    except Exception as e:
      print(e)
      app.config['db'].rollback()
      abort(make_response("This user already exists", 400))
      container.remove(force=True)
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
  
