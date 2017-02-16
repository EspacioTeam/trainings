#!/usr/bin/env python

from datetime import datetime
import select
import socket
import sys
import threading
import sqlite3
DATABASE = 'scoreboard.db'

class Server:
    _database = None

    @staticmethod
    def get_db():
        db = getattr(Server, '_database', None)
        if db is None:
            db = Server._database = sqlite3.connect(DATABASE)
        return db

    @staticmethod
    def init_db():
        with app.app_context():
            db = Server.get_db()
            db.commit()

    @staticmethod
    def query_db(query, args=(), one=False):
        cur = Server.get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
  
    @staticmethod
    def insert(table, fields=(), values=()):
        # g.db is the database connection
        db = Server.get_db()
        query = 'INSERT INTO %s (%s) VALUES (%s)' % (
            table,
            ', '.join(fields),
            ', '.join(['?'] * len(values))
        )
        db.cursor().execute(query, values)
        db.commit()

    @staticmethod
    def make_dicts(cursor, row):
        return dict((cursor.description[idx][0], value)
                    for idx, value in enumerate(row))

    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 14900
        self.backlog = 5
        self.size = 1024
        self.server = None
        self.threads = []

    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.host,self.port))
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.listen(10)

        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print ">> Could not open socket: " + message
            self.port += 1
            self.open_socket()

    def run(self):
        self.open_socket()
        input = [self.server,sys.stdin]
        running = 1
        print '>> listen on {} port'.format(self.port)
        while running:
            try:
                inputready,outputready,exceptready = select.select(input,[],[])
                for s in inputready:

                    if s == self.server:
                        # handle the server socket
                        c = Client(self.server.accept())
                        c.start()
                        self.threads.append(c)
                        print '>> new connection, thread {}.'.format(c.name)
            except KeyboardInterrupt:
                print '>> Exit from keyboard. Shut down server'
                running = 0
        # close all threads
        self.server.close()
        for c in self.threads:
            c.join()

    def chat_msg_sending(self,msg,msg_sender):
        for c in self.threads:
            if c.client != msg_sender.client:
                c.client.send( str(msg) )



class Client(threading.Thread):
    def __init__(self, (client,address) ):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.db = Server.get_db()
        self.token = "0"
        self.size = 1024
        self.points = 0

    def run(self):
        self.client.send('Welcome! \n Enter your token: \n')
        login = 0
        running = 1
        while running:
            try:
                data = self.client.recv(128)
                if data:
                    #print data.decode('utf-8')
                    if self.token is "0" :
                        check = Server.query_db('select guid FROM users WHERE token=?', data, one=True)
                        print check
                        if check:
                            self.client.send("Authorized as %s\n, Enter your flags, one per line:\n" % data)
                            while True:
                                try:
                                    flag = self.recv(2**30)
                                    flags = flag.split("\n")
                                    for flag in flags:
                                        check = query_db('select * FROM flags WHERE flag=?', [flag], one=True)
                                        print check
                                        if check:
                                            self.points += 1
                                            self.client.send("+\n")
                                        else:
                                            self.client.send("-\n")
                                            
                                except:
                                    self.client.send("bad flag\n")



                else:
                    print '>> user {} disconnect'.format(self.name)
                    server.threads.remove(self)
                    self.client.close()
                    running = 0
            except socket.error, ex:
                print ("104: Connection closed by peer")
                server.threads.remove(self)
                self.client.close()
                running = 0

if __name__ == "__main__":
    server = Server()
    server.run()
