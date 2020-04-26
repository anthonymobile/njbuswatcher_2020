import time
import os

def timeit(f):

    def timed(*args, **kw):

        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        print ('func:%r took: %2.4f sec' % \
          (f.__name__, te-ts))
        # print ('func:%r args:[%r, %r] took: %2.4f sec' % \
        #   (f.__name__, args, kw, te-ts))
        return result

    return timed


# returns the Path to the config directory
def get_config_path():

    # docker
    if os.getcwd() == "/":  # docker
        prefix = "/app/app/"

    # osx
    elif "Users" in os.getcwd():
        prefix = ""

    # others
    else:
        prefix = ""

    path = (prefix + "config/")

    return path