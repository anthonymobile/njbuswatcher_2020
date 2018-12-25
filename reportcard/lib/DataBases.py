# ####################################################
# BUSWATCHER
#
#     -- the idea is, define the class and the table at the same time, rather than separately like in Alex's code
#     -- can probably place a lot of the methods (like get_session) in a parent class
#
# ####################################################

# -*- coding: utf-8 -*-

from sqlalchemy import Table, Column, Integer, DateTime, Numeric, String
from sqlalchemy.ext.declarative import declarative_base

# base class
Base = declarative_base()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# interim class allows for all DB classes inheriting handling methods
class DB(Base):

    def get_session():
        engine = create_engine('sqlite:///../data/jc_permits.db') # todo update engine for real mysql backend
        Session = sessionmaker(bind=engine)
        session = Session
        return session


#####################################################
# CLASS BusPosition
#####################################################
# stores raw positions for later reference
#####################################################

class BusPosition(DB):

    def __init__(self,route):
        self.route=route

    __tablename_ _ ='routelog'+self.route
    __table_args__ = {'extend_existing': True}

    pkey = Column(Integer(), primary_key=True)
    lat = Column(Numeric)
    lon = Column(Numeric)
    cars = Column(String(20))
    consist = Column(String(20))
    d = Column(String(20))
    dip = Column(String(20))
    dn = Column(String(20))
    fs = Column(String(20))
    id = Column(String(20))
    m = Column(String(20))
    op = Column(String(20))
    pd = Column(String(20))
    pdRtpiFeedName = Column(String(255))
    pid = Column(String(20))
    rt = Column(String(20))
    rtRtpiFeedName = Column(String(20))
    rtdd = Column(String(20))
    rtpiFeedName = Column(String(20))
    run = Column(String(20))
    wid1 = Column(String(20))
    wid2 = Column(String(20))
    timestamp = Column(String(20))

    def __repr__(self):
        return "Position()".format(self=self)



#####################################################
# CLASS Trip
#####################################################
# stores trip structure for a unique v, run, date
# = list of stops and call times
#####################################################

class Trip(DB):

    def __init__(self):

    __tablename_
    _ = 'trips'
    __table_args__ = {'extend_existing': True}

    trip_id = Column(String(255)) #concatenation of v_run_date = trip_id
    v = Column(Integer())
    run = Column(Integer())
    date = Column(DateTime())

    def __repr__(self):
        return "Trip()".format(self=self)

################################################################
# CLASS StopCall
################################################################
# stores arrival time only for a single, v, run, date, stop_id
################################################################

class Arrival(DB): # todo does this need to be a subclass of Trip? can it be?

    def __init__(self):

    __tablename_
    _ = 'arrivals'
    __table_args__ = {'extend_existing': True}

    trip_id = Column(String(255))  # concatenation of v_run_date = trip_id
    run = Column(Integer())
    v = Column(Integer())
    date = Column(DateTime())
    stop_id = Column(Integer())
    position = BusPosition() # nearest approach -- todo can i put an object in the database?
    timestamp = Column(DateTime())

    def __repr__(self):
        return "StopCall()".format(self=self)

