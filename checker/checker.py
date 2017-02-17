#!/usr/bin/python2
import MySQLdb
import threading
import socket
import sys
import argparse
import re
import thread

class Checker(object):
    def __init__(self, host, port, db_host, db_username, db_pwd):
        print("### CHECKER ###")
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

        # connect to mysql
        self.db = MySQLdb.connect(
            host=db_host,
            user=db_username,
            passwd=db_pwd,
            db='ctf')

        print("[+] Connected to MySQL")


    def listen(self):
        self.sock.listen(5)
        print("[+] Listening on {0}:{1}".format(self.host, self.port))
        while True:
            try:
                client, address = self.sock.accept()
                client.settimeout(10)
                print("[+] Got connection from {0}".format(address))
                threading.Thread(target = self.listenToClient,args = (client,address)).start()
            except KeyboardInterrupt:  
                print("[+] i am dying, kill and reload me (x_x)")
                thread.exit()
                exit(1)



    def mysql_query(self, query, args=(), one=True, is_destructive=False):
        assert(isinstance(query, str))
        assert(isinstance(args, tuple))
        try:
            cursor = self.db.cursor()
            cursor.execute(query, args)
            if is_destructive:
                self.db.commit()
            if one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
        finally:
            cursor.close()


    def listenToClient(self, client, address):
        try:
            client.send("Welcome! Send me your token (sha512 string):\n")
            # authorization
            token = client.recv(128) # bytes
            if not re.match("[a-zA-Z0-9\\+//]{128}", token):
                client.send("wrong token format\n")
                self.close_client(client, address)

            user = self.mysql_query("select id, name, score from user where token = %s;", (token,))
            if user:
                user_id, username, score = user
                client.send("Welcome {0}. Your score is {1}. \nSend your flags, one per line:\n".format(username, score))
                print("{0} authorized".format(username))
                self.recv_flags(client, user_id, username, token)
                self.close_client(client, address)
            else:
                client.send("No such user\n")
                self.close_client(client, address)

        except socket.timeout:
            client.send("timeout\n")
            client.close()
            print("{0} timed out".format(address))
            

    def close_client(self, client, addr):
        try:
            client.close()
            raise Exception("{0} closed".format(addr))
        except:
            print("{0} exited".format(addr))

    def recv_flags(self, client, user_id, username, token):
        receive = True
        while receive:
            flag = client.recv(256)
            if not flag:
                client.send("empty line\n")
                client.close()
                receive = False
                break

            f = self.check_flag(client, flag)
            if f: # flag is valid, and was not submitted before
                flag_id, flag, points = f

                points = int(points)
                flag_id = int(flag_id)
                user_id = int(user_id)

                self.mysql_query("update user set score=score+%s where token=%s;", (points, token,), is_destructive=True)
                self.mysql_query("insert into submissions(user_id,flag_id) VALUES (%s, %s);", (user_id, flag_id,), is_destructive=True)
                client.send("+{0} points\n".format(points))


    def check_flag(self, client, flag):
        # if flag format is base64
        flag = flag.replace("\n", "")
        if len(flag) > 0 and re.match("[a-zA-Z0-9=+/]+", flag):
            f = self.mysql_query("select id, flag, points from flag where flag=%s;", (flag,))
            if f: # flag exists
                flag_id, flag, points = f

                f = self.mysql_query("select user_id, date from submissions where flag_id=%s;", (flag_id,))
                if f: # flag was submitted before
                    client.send("flag was submitted by other team\n")
                    return None
                else: # flag was NOT submitted before
                    return flag_id, flag, points

            else:
                client.send("incorrect flag\n")
                return None

        else:
            return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Checker')
    ## checker settings
    parser.add_argument('checker_host', type=str, default='0.0.0.0', help='default is 0.0.0.0')
    parser.add_argument('checker_port', type=int, default=14900, help='default is 14900')

    ## db settings
    parser.add_argument('db_host', default='127.0.0.1', type=str,
                        help='default is 127.0.0.1')
    parser.add_argument('db_user', default='root', type=str,
                        help='mysql user, default root')
    parser.add_argument('db_password', type=str, 
                        help='mysql password')
    args = parser.parse_args()

    Checker(
        args.checker_host, 
        args.checker_port, 
        args.db_host, 
        args.db_user, 
        args.db_password
    ).listen()