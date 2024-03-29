from locust import HttpUser, between, task


class Quick(HttpUser):
    wait_time = between(1, 2)

    @task
    def hello_world(self):
        self.client.get("/")
