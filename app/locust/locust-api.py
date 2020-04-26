# locust -f locust-www.py --host http://0.0.0.0:5000
# view results at http://0.0.0.0:8089/
#

from locust import HttpLocust, TaskSet, task
from pyquery import PyQuery
import random

from app.lib.TransitSystem import load_system_map

routelist=list(load_system_map().get_routelist())
api_root="/api/v1/maps/"


class APIRequest(TaskSet):
    def on_start(self):
        pass

    def gen_rt(self):
        rt = random.choice(routelist)
        rt = '?rt='+rt
        return rt

    def gen_layer(self):
        layer=random.choice(['vehicles', 'waypoints', 'stops'])
        return layer

    @task(1)
    def vehicles(self):
        rt = self.gen_rt()
        layer=self.gen_layer()
        page_request = self.client.get(api_root+layer+rt)


class PoundOnAPI(HttpLocust):
    task_set = APIRequest
    min_wait = 1000
    max_wait = 5000
