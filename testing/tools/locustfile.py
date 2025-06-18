from locust import HttpUser, task, between

class FutureSocialUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def index(self):
        self.client.get("/")
    
    @task(3)
    def view_user(self):
        user_id = 1  # This would be randomized in a real test
        self.client.get(f"/users/{user_id}")
    
    @task(2)
    def view_posts(self):
        self.client.get("/posts")