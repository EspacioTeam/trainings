import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


class Schema:
  def __init__(self, host, user, port, pwd):
    self.host = host
    self.user = user
    self.port = port
    self.pwd  = pwd

    self.engine = create_engine("mysql+mysqldb://scott:tiger@localhost/test?charset=utf8&use_unicode=0")