from locust import HttpLocust, TaskSet, task

class UserBehavior(TaskSet):
    def on_start(self):
        # on_start is called when a Locust start before any task is scheduled
        # self.login()

    def on_stop(self):
        #  on_stop is called when the TaskSet is stopping """
        # self.logout()

    # def login(self):
    #     self.client.post("/login", {"username":"ellen_key", "password":"education"})
    #
    # def logout(self):
    #     self.client.post("/logout", {"username":"ellen_key", "password":"education"})

    @task(2)
    def index(self):
        self.client.get("/")

    @task(2)
    def index(self):
        self.client.get("/")

    @task(2)
    def index(self):
        self.client.get("/")

    @task(1)
    def profile(self):
        self.client.get("/profile")


# class BrowseDocumentationSequence(TaskSequence):
#     def on_start(self):
#         self.urls_on_current_page = self.toc_urls = None
#
#     # assume all users arrive at the index page
#     @seq_task(1)
#     def index_page(self):
#         r = self.client.get("/")
#         pq = PyQuery(r.content)
#         link_elements = pq(".toctree-wrapper a.internal")
#         self.toc_urls = [
#             l.attrib["href"] for l in link_elements
#         ]
#
#     @seq_task(2)
#     @task(50)
#     def load_page(self, url=None):
#         url = random.choice(self.toc_urls)
#         r = self.client.get(url)
#         pq = PyQuery(r.content)
#         link_elements = pq("a.internal")
#         self.urls_on_current_page = [
#             l.attrib["href"] for l in link_elements
#         ]
#
#     @seq_task(3)
#     @task(30)
#     def load_sub_page(self):
#         url = random.choice(self.urls_on_current_page)
#         r = self.client.get(url)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
