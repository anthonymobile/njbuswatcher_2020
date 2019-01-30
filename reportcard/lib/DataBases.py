# -*- coding: utf-8 -*-
import datetime, sys
from sqlalchemy import create_engine, Table, Column, Integer, DateTime, Float, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from . import BusAPI

#####################################################
# base
#####################################################
Base = declarative_base()

class DBConfig(object):
    conn_str='sqlite:///jc_buswatcher.db'

# from https://medium.com/@ramojol/python-context-managers-and-the-with-statement-8f53d4d9f87
class SQLAlchemyDBConnection(object):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.session = None
    def __enter__(self):
        engine = create_engine(self.connection_string)
        Session = sessionmaker()
        self.session = Session(bind=engine)

        try: # try to create tables, just in case they aren't there
            Base.metadata.create_all(bind=engine)
        except:
            pass

        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

#####################################################
# CLASS Trip
#####################################################

class Trip(Base):

    def __init__(self, conn_str, source, route, v, run, pid):
        self.v = v
        self.run = run
        self.pid = pid
        self.date = datetime.datetime.today().strftime('%Y%m%d')
        self.trip_id=('{v}_{run}_{date}').format(v=v,run=run,date=self.date)

        # create a corresponding set of ScheduledStop records for each new Trip
        # and populate the self.stoplist

        with SQLAlchemyDBConnection(conn_str) as db:
            self.db = db
            self.stop_list = []
            routes, coordinates_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(source, 'routes', route=route))
            for path in routes[0].paths:
                if path.id == self.pid:
                    for point in path.points:
                        if isinstance(point, BusAPI.Route.Stop):
                            this_stop = ScheduledStop(self.trip_id,self.v,self.run,self.date,point.identity)
                            self.stop_list.append(point.identity)
                            for stop in self.stop_list:
                                self.db.session.add(this_stop)
                else:
                    pass
            self.db.session.commit()

    __tablename__ = 'trip_log'
    __table_args__ = {'extend_existing': True}

    pkey = Column(Integer(), primary_key=True)
    trip_id = Column(String(255))
    v = Column(Integer())
    run = Column(Integer())
    date = Column(String)

    children_ScheduledStops = relationship("ScheduledStop", backref='trip_log')
    children_BusPositions = relationship("BusPosition", backref='trip_log')

    def __repr__(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value))
        line.sort(key=lambda x: x[0])
        out_string = ' '.join([k + '=' + str(v) for k, v in line])
        return "Trip" + '[%s]' % out_string



################################################################
# CLASS ScheduledStop
################################################################
# represents a stop on a scheduled trip
# used to store final inferred arrival time for a single, v, run, date, stop_id
################################################################
#
class ScheduledStop(Base):

    def __init__(self, trip_id,v,run,date,stop_id):
        self.trip_id = trip_id
        self.v = v
        self.run = run
        self.date = date
        self.stop_id = stop_id

    __tablename__ = 'scheduledstop_log'
    __table_args__ = {'extend_existing': True}

    pkey = Column(Integer(), primary_key=True)
    run = Column(Integer())
    v = Column(Integer())
    date = Column(String())
    stop_id = Column(Integer())
    arrival_timestamp = Column(DateTime())

    # relationships
    trip_id = Column(String(255), ForeignKey('trip_log.trip_id'))
    parent_Trip = relationship("Trip",backref='scheduledstop_log')

    def __repr__(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value))
        line.sort(key=lambda x: x[0])
        out_string = ' '.join([k + '=' + str(v) for k, v in line])
        return "ScheduledStop" + '[%s]' % out_string


#####################################################
# CLASS BusPosition
#####################################################
# stores raw positions for later reference
#####################################################

class BusPosition(Base):

    __tablename__ ='position_log'
    __table_args__ = {'extend_existing': True}

    pkey = Column(Integer(), primary_key=True)
    lat = Column(Float)
    lon = Column(Float)
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
    timestamp = Column(DateTime())

    distance_to_stop = Column(Float())
    arrival_flag = Column(Boolean())

    # relationships
    trip_id = Column(String(255), ForeignKey('trip_log.trip_id'))
    stop_id = Column(String(255), ForeignKey('scheduledstop_log.stop_id'))

    parent_Trip = relationship("Trip",backref='position_log')
    parent_ScheduledStop = relationship("ScheduledStop",backref='position_log')

    def __repr__(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value))
        line.sort(key=lambda x: x[0])
        out_string = ' '.join([k + '=' + str(v) for k, v in line])
        return "BusPosition" + '[%s]' % out_string








