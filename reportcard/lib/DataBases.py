# ####################################################
# BUSWATCHER
# ####################################################

# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import Table, Column, Integer, DateTime, Numeric, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# base class
Base = declarative_base()

# interim class allows for all DB classes inheriting handling methods
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DB(Base):
    def get_session():
        engine = create_engine('sqlite:///../data/jc_permits.db') # todo update engine for real mysql backend
        Session = sessionmaker(bind=engine)
        session = Session
        return session

#####################################################
# CLASS Trip
#####################################################
# stores trip structure for a unique v, run, date
# = list of stops and call times
#####################################################

class Trip(DB):

    def __init__(self,v,run):
        self.v = v
        self.run = run
        self.date = datetime.datetime.today().strftime('%Y-%m-%d')
        self.trip_id=('{v}_{run}_{date}').format(v=v,run=run,date=self.date)

    __tablename__ = 'triplog'
    __table_args__ = {'extend_existing': True}

    pkey = Column(Integer(), primary_key=True)
    trip_id = Column(String(255))
    v = Column(Integer())
    run = Column(Integer())
    date = Column(DateTime())

    positions = relationship("BusPosition")
    stops = relationship("ScheduledStop")

    def __repr__(self):
        return "Trip()".format(self=self)


################################################################
# CLASS ScheduledStop
################################################################
# represents a stop on a scheduled trip
# used to store final inferred arrival time for a single, v, run, date, stop_id
################################################################
#
class ScheduledStop(DB):

    def __init__(self):
        # todo set init values for ScheduledStop
        #
        #

    __tablename__ = 'stoplog'
    __table_args__ = {'extend_existing': True}

    pkey = Column(Integer(), primary_key=True)
    trip_id = Column(String(255), ForeignKey('triplog.trip_id'))
    run = Column(Integer())
    v = Column(Integer())
    date = Column(DateTime())
    stop_id = Column(Integer())
    arrival_timestamp = Column(DateTime())

    arrivals = relationship("BusPosition")

    def __repr__(self):
        return "StopCall()".format(self=self)



#####################################################
# CLASS BusPosition
#####################################################
# stores raw positions for later reference
#####################################################

class BusPosition(DB):

    def __init__(self,route):
        self.route=route
        # todo set init values for BusPosition
        #
        #

    __tablename_ _ ='routelog'
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

    trip_id = Column(String(255), ForeignKey('triplog.trip_id'))
    stop_id = Column(String(255), ForeignKey('stoplog.stop_id'))
    distance_to_stop = Column(Numeric())
    arrival_flag = Column(Boolean())

    def __repr__(self):
        return "Position()".format(self=self)

