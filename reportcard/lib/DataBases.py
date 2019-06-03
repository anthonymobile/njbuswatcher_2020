# -*- coding: utf-8 -*-
import datetime, sys
from sqlalchemy import inspect, create_engine, ForeignKeyConstraint, Index, Date, Column, Integer, DateTime, Float, String, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from . import BusAPI
from . import DBconfig

#####################################################
# base
#####################################################
Base = declarative_base()

class SQLAlchemyDBConnection(object):
    def __init__(self):
        # self.connection_string = 'sqlite:///jc_buswatcher.db'  # TESTING, WORKS
        self.connection_string = DBconfig.connection_string # replaces 'localhost' with 'db' for development        self.session = None

    def __enter__(self):
        engine = create_engine(self.connection_string)
        Session = sessionmaker()
        self.session = Session(bind=engine)
        Base.metadata.create_all(bind=engine)
        return self

    def __relax__(self):
        self.session.execute('SET FOREIGN_KEY_CHECKS = 0;')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.execute('SET FOREIGN_KEY_CHECKS = 1;')
        self.session.close()


#####################################################
# CLASS Trip
#####################################################

class Trip(Base):

    def __init__(self, source, route, v, run, pid):
        self.source = source
        self.rt = route
        self.v = v
        self.run = run
        self.pid = pid
        self.date = datetime.datetime.today().strftime('%Y%m%d')
        self.trip_id=('{v}_{run}_{date}').format(v=v,run=run,date=self.date)

        # create a corresponding set of ScheduledStop records for each new Trip
        # and populate the self.stoplist and self.coordinates_bundle

        with SQLAlchemyDBConnection() as db:
            self.db = db
            self.stop_list = []
            routes, self.coordinates_bundle = BusAPI.parse_xml_getRoutePoints(
                BusAPI.get_xml_data(self.source, 'routes', route=self.rt))
            self.routename = routes[0].nm
            for path in routes[0].paths:
                if path.id == self.pid:
                    for point in path.points:
                        if isinstance(point, BusAPI.Route.Stop):
                            this_stop = ScheduledStop(self.trip_id, self.v, self.run, self.date, point.identity,
                                                      point.st, point.lat, point.lon)
                            self.stop_list.append((point.identity, point.st))
                            for stop in self.stop_list:
                                self.db.session.add(this_stop)
                else:
                    pass
            self.db.__relax__() # relax so we dont trigger the foreign key constraint
            self.db.session.commit()

    __tablename__ = 'trip_log'
    __table_args__ = {'extend_existing': True}

    trip_id = Column(String(127), primary_key=True, index=True, unique=True)
    source = Column(String(8))
    rt = Column(Integer())
    v = Column(Integer())
    run = Column(String(8))
    pid = Column(Integer())
    date = Column(Date())
    coordinate_bundle = Column(Text())

    # relationships
    # children_ScheduledStop = relationship("ScheduledStop", back_populates='parent_Trip')
    # children_BusPosition = relationship("BusPosition", back_populates='parent_Trip')


################################################################
# CLASS ScheduledStop
################################################################

class ScheduledStop(Base):

    def __init__(self, trip_id,v,run,date,stop_id,stop_name,lat,lon):
        self.trip_id = trip_id
        self.v = v
        self.run = run
        self.date = date
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.lat = lat
        self.lon = lon

    __tablename__ = 'scheduledstop_log'


    pkey = Column(Integer(), primary_key=True)
    run = Column(String(8))
    v = Column(Integer())
    date = Column(Date())
    stop_id = Column(Integer(), index=True)
    stop_name = Column(String(255))
    lat = Column(Float())
    lon = Column(Float())
    arrival_timestamp = Column(DateTime(), index=True)

    # foreign keys
    trip_id = Column(String(127), ForeignKey('trip_log.trip_id'), index=True)
    __table_args__ = (Index('trip_id_stop_id',"trip_id","stop_id"),{'extend_existing': True})


#####################################################
# CLASS BusPosition
#####################################################

class BusPosition(Base):

    __tablename__ ='position_log'

    pkey = Column(Integer(), primary_key=True)
    lat = Column(Float)
    lon = Column(Float)
    cars = Column(String(20))
    consist = Column(String(20))
    d = Column(String(20))
    dip = Column(String(20))
    dn = Column(String(20))
    fs = Column(String(127))
    id = Column(String(20))
    # id = Column(String(20), index=True)
    m = Column(String(20))
    op = Column(String(20))
    pd = Column(String(255))
    pdrtpifeedname = Column(String(255))
    pid = Column(String(20))
    rt = Column(String(20))
    rtrtpifeedname = Column(String(20))
    rtdd = Column(String(20))
    rtpifeedname = Column(String(20))
    run = Column(String(8))
    wid1 = Column(String(20))
    wid2 = Column(String(20))
    timestamp = Column(DateTime())

    distance_to_stop = Column(Float())
    arrival_flag = Column(Boolean())

    # foreign keys
    trip_id = Column(String(127), index=True)
    stop_id = Column(Integer(), index=True)
    __table_args__ = (ForeignKeyConstraint([trip_id, stop_id],
                                           [ScheduledStop.trip_id, ScheduledStop.stop_id]),
                                            {'extend_existing': True})