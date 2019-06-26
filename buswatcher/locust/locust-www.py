# locust -f locust-www.py --host http://0.0.0.0:5000
# view results at http://0.0.0.0:8089/
#

from locust import HttpLocust, TaskSet, task
from pyquery import PyQuery
import random

class BrowseCollections(TaskSet):
    def on_start(self):
        # assume all users arrive at the index page
        self.index_page()
        self.urls_on_current_page = self.toc_urls

    @task(10)
    def index_page(self):
        r = self.client.get("/")
        pq = PyQuery(r.content)
        # link_elements = pq(".toctree-wrapper a.internal") #todo pick a different element to extract
        link_elements = pq(".btn")
        self.toc_urls = [
            l.attrib["href"] for l in link_elements
        ]
        print (self.toc_urls)

    @task(50)
    def load_page(self, url=None):
        url = random.choice(self.toc_urls)
        r = self.client.get(url)
        pq = PyQuery(r.content)
        link_elements = pq("a")
        self.urls_on_current_page = [
            l.attrib["href"] for l in link_elements
        ]
        print(self.urls_on_current_page)

    @task(30)
    def load_sub_page(self):
        url = random.choice(self.urls_on_current_page)
        r = self.client.get(url)


class AwesomeUser(HttpLocust):
    task_set = BrowseCollections
    min_wait = 5000
    max_wait = 9000
