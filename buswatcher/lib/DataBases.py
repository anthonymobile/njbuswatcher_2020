import datetime, time
from sqlalchemy import create_engine, ForeignKeyConstraint, Index, Date, Column, Integer, DateTime, Float, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from . import NJTransitAPI, DBconfig

Base = declarative_base()

class SQLAlchemyDBConnection(object):

    def __init__(self):
        # self.connection_string = 'sqlite:///jc_buswatcher.db'  # TESTING, WORKS
        self.connection_string = DBconfig.connection_string # replaces 'localhost' with 'db' for development        self.session = None

    def __enter__(self):
        engine = create_engine(self.connection_string)
        Session = sessionmaker()

        self.session = Session(bind=engine)

        while True:
            try:
                Base.metadata.create_all(bind=engine)
            except OperationalError:
                print ('lib.DataBases Cant connect to db, waiting 5s then retrying...')
                time.sleep(5)
                continue
            break

        return self

    def __relax__(self):
        self.session.execute('SET FOREIGN_KEY_CHECKS = 0;')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.execute('SET FOREIGN_KEY_CHECKS = 1;')
        self.session.close()

class Trip(Base):
    #####################################################
    # CLASS Trip
    #####################################################

    def __init__(self, source, system_map, route, v, run, pd, pid):
        self.source = source
        self.rt = route
        self.v = v
        self.run = run
        self.pd = pd
        self.pid = pid
        self.date = datetime.datetime.today().strftime('%Y%m%d')
        self.trip_id=('{v}_{run}_{date}').format(v=v,run=run,date=self.date)
        self.stop_list = self.get_stoplist()

    def get_stoplist(self):
        # create a corresponding set of Stop records for each new Trip
        # and populate the self.stoplist and self.coordinates_bundle

        with SQLAlchemyDBConnection() as db:

            self.db = db
            self.stop_list = dict()
            routes, self.coordinates_bundle = system_map.get_single_route_paths_and_coordinatebundle(self.rt)

            self.routename = routes[0].nm
            trip_stop_sequence=0
            for path in routes[0].paths:
                if path.id == self.pid:
                    for point in path.points:
                        if isinstance(point, NJTransitAPI.Route.Stop):
                            trip_stop_sequence =+ 1
                            this_stop = Stop(self.trip_id, trip_stop_sequence, self.v, self.run, self.date, point.identity,
                                             point.st, point.lat, point.lon)
                            self.stop_list.append((point.identity, point.st))
                            for stop in self.stop_list:
                                self.db.session.add(this_stop)
                else:
                    pass
            self.db.__relax__() # relax so we dont trigger the foreign key constraint
            self.db.session.commit()
            return

    __tablename__ = 'trips'
    __table_args__ = {'extend_existing': True}

    trip_id = Column(String(127), primary_key=True, index=True, unique=True)
    source = Column(String(8))
    rt = Column(Integer())
    v = Column(Integer())
    run = Column(String(8))
    pd = Column(String(127))
    pid = Column(Integer())
    date = Column(Date())
    stoplist = Column(JSON)

    # relationships
    # children_ScheduledStop = relationship("Stop", back_populates='parent_Trip')
    # children_BusPosition = relationship("BusPosition", back_populates='parent_Trip')

    def __repr__(self):
        return '[Trip: \trt {} \ttrip_id {}]'.format(self.rt, self.trip_id)

class Stop(Base):
    ################################################################
    # CLASS Stop
    ################################################################

    def __init__(self, trip_id,trip_stop_sequence, v,run,date,stop_id,stop_name,lat,lon):
        self.trip_id = trip_id
        self.trip_stop_sequence = trip_stop_sequence
        self.v = v
        self.run = run
        self.date = date
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.lat = lat
        self.lon = lon

    __tablename__ = 'stops'


    pkey = Column(Integer(), primary_key=True)
    run = Column(String(8))
    v = Column(Integer())
    date = Column(Date())
    stop_id = Column(Integer(), index=True)
    stop_name = Column(String(255))
    lat = Column(Float())
    lon = Column(Float())
    arrival_timestamp = Column(DateTime(), index=True)
    interpolated_arrival_flag = Column(Boolean())

    # foreign keys
    trip_id = Column(String(127), ForeignKey('trips.trip_id'), index=True)
    __table_args__ = (Index('trip_id_stop_id',"trip_id","stop_id"),{'extend_existing': True})

    def __repr__(self):
        return '[Stop: \ttrip_id {} \tstop_id {} \tarrival_timestamp {} \tinterpolated_arrival_flag {}]'.format(self.trip_id, self.stop_id, self.arrival_timestamp, self.interpolated_arrival_flag)

class BusPosition(Base):
    #####################################################
    # CLASS BusPosition
    #####################################################

    __tablename__ ='positions'

    pkey = Column(Integer(), primary_key=True)
    lat = Column(Float)
    lon = Column(Float)
    cars = Column(String(20))
    consist = Column(String(20))
    d = Column(String(20))
    # dip = Column(String(20))
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
                                           [Stop.trip_id, Stop.stop_id]),
                                            {'extend_existing': True})

    def __repr__(self):
        return '[BusPosition: \trt \ttrip_id {} \tstop_id \tdistance \tarrival_flag {}]'.format(self.rt,self.trip_id,self.stop_id,self.distance_to_stop,self.arrival_flag)
