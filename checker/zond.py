#!/usr/bin/python3

import subprocess
import threading
import schedule
import time
import MySQLdb
import random
import string

STATUS_CODE = {
    'SUCCESS': 101,
    'CORRUPT': 102,
    'MUMBLE':  103,
    'DOWN':    104,
    'UNKNOWN': 110
}

BASE_PATH = "./zond_target"
FLAG_POINT = 100
hosts = []
conn = MySQLdb.connect(user="root", password="lMKMdiEJodCwIFXfGgvYnXcbfQwQDb", host="172.17.0.3", db="ctf")

def mysql_query(query, args=(), one=True, is_destructive=False):
    assert(isinstance(query, str))
    assert(isinstance(args, tuple))
    try:
        cursor = conn.cursor()
        cursor.execute(query, args)
        if is_destructive:
            conn.commit()
        if one:
            return cursor.fetchone()
        else:
            return cursor.fetchall()
    finally:
        cursor.close()

def generate_flags():
    flag = ''.join(random.choice(string.ascii_uppercase
    + string.ascii_lowercase
    + string.digits) for x in range(33))
    flag += '='

    return flag

def check(hostname):
    code = 110
    #print("CHECK: {}".format(time.time() - start))
    outs = "Internal error"
    args = (BASE_PATH, "check", hostname)
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    try:
        outs, errs = popen.communicate(timeout=2)
        code = popen.returncode
    except subprocess.TimeoutExpired as e:
        #print(e)
        code = 104
        outs = "Host unreachable"
        popen.kill()
    return outs, code

def put(hostname, flag):
    #print("PUT: {}".format(time.time() - start))
    code = 110
    outs = "Internal error"
    args = (BASE_PATH, "put", hostname, flag)
    popen = subprocess.Popen(args)
    try:
        outs, errs = popen.communicate(timeout=2)
        code = popen.returncode
    except subprocess.TimeoutExpired as e:
        #print(e)
        code = 104
        outs = "Host unreachable"
        popen.kill()
    #print("{}: {}".format(hostname, code))
    exit(0)
    #return outs, code

def get(hostname, flag):
    code = 110
    outs = "Internal error"
    args = (BASE_PATH, "get", host, flag)
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    try:
        outs, errs = popen.communicate(timeout=2)
        code = popen.returncode
    except subprocess.TimeoutExpired as e:
        #print(e)
        code = 104
        outs = "Host unreachable"
        popen.kill()
    return outs, code


def putall():
    _hosts = []
    for i in hosts:
        flag = generate_flags()
        mysql_query("INSERT INTO flag (flag, points) VALUES (%s, %s)", (flag, FLAG_POINT,), is_destructive=True)
        t = threading.Thread(target=put, args=[i, flag])
        t.start()
        _hosts.append(t)
    for i in _hosts:
        i.join()
    return 0

def checkall():
    for i in hosts:
        t = threading.Thread(target=check, args=[i, "KEK"])
        t.start()
        _hosts.append(t)
    for i in _hosts:
        i.join()
    return 0

schedule.every(1).minutes.do(putall)

if __name__ == '__main__':
    hosts = list(mysql_query("SELECT host FROM user"))

    while 1:
        schedule.run_pending()
        time.sleep(0.01)
