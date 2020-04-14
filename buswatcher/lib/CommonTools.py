import time
import geopy.distance
import os

def timeit(f):
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print ('func:%r took: %2.4f sec' % \
          (f.__name__, te-ts))
        return result
    return timed

def get_config_path():
    if os.getcwd() == "/":  # docker
        prefix = "/buswatcher/buswatcher/"
    elif "Users" in os.getcwd():
        prefix = ""
    else:
        prefix = ""
    path = (prefix + "config/")
    return path

def distance (p_prev, p):
    coords_1 = (p_prev.lat, p_prev.lon)
    coords_2 = (p.lat,p.lon)
    return geopy.distance.vincenty(coords_1, coords_2).feet


