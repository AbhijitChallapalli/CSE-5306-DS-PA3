from locust import HttpUser, task, between, events
import random
import gevent
from gevent.lock import Semaphore
from datetime import datetime, timedelta, timezone

class APIUser(HttpUser):
    wait_time = between(1, 3)  # simulate user think time

    def on_start(self):
        """ 
        Worker startup routine
            Consists of simulating user logging in and keeps track
            of notifications and alarms created along with creating
            the first alarm. Also spawns gevents to simulate the app
            polling for alarms and notifications for the user.
        """
        self.user_id = None
        self.notif_lock = Semaphore()
        self.alarm_lock = Semaphore()

        # Create a new user
        username = f"user_{random.randint(1, 100000)}"
        password = "password123"

        # Keep looping until logged in
        while self.user_id is None:
            with self.client.post(
                "/users/register",
                json={"username": username, "password": password},
                catch_response=True
            ) as response:    
                if response.status_code in (200, 201):
                    self.user_id = response.json()["id"]
                    self.username = username
                    self.password = password
                    response.success()
                elif response.status_code == 409:
                    with self.client.post(
                        "/users/authenticate",
                        json={"username": username, "password": password},
                        catch_response=True
                    ) as response:
                        if response.status_code in (200, 201):
                            self.user_id = response.json()["id"]
                            response.success()
                        else:
                            response.failure(f"Failed to authenticate user {username}: {response.status_code}")
                else:
                    response.failure(f"Failed to register user {username}: {response.status_code}")

            gevent.sleep(1)

        # store alarm and notification IDs created during this session
        self.alarms = []
        self.notifications = []
        self.create_alarm()
        # Simulate frontend polling to get notifications and alarms
        self.alarm_greenlet = gevent.spawn(self.fetch_alarms)
        self.notif_greenlet = gevent.spawn(self.fetch_notifications)
    
    def on_stop(self):
        """ Kills the continuous polling """
        if hasattr(self, "alarm_greenlet"):
            self.alarm_greenlet.kill()
        if hasattr(self, "notif_greenlet"):
            self.notif_greenlet.kill()
    
    def fetch_alarms(self):
        """ Simulates the frontend app polling alarms every 0.5s """
        while True:
            with self.client.get(
                f"/alarms?user_id={self.user_id}",
                name="GET alarms/",
                catch_response=True
            ) as response:
                self.handle_response(response, "Get Alarm Request")
            gevent.sleep(1)
    
    def fetch_notifications(self):
        """ Simulates the frontend app polling notifications every 0.5s """
        while True:
            with self.notif_lock:
                with self.client.get(
                    f"/notifications?user_id={self.user_id}",
                    name="GET notifications/",
                    catch_response=True
                ) as response:
                    if self.handle_response(response, "Get Notification Request"):
                        notifs = response.json()
                        self.notifications = [notif["id"] for notif in notifs]
            gevent.sleep(1)

    def generate_alarm_time(self):
        """ Generates a time within the next 5 minutes """
        now = datetime.now(timezone.utc)
        delta = timedelta(minutes=random.randint(1, 5)) # 
        return (now + delta).isoformat()

    def handle_response(self, response, name="Request"):
        """ Wrapper function to handle responses and report failures """
        if response.status_code in (200, 201, 404):
            response.success()
            return True
        else:
            response.failure(f"{name} failed with status {response.status_code}: {response.text}")
            return False

    @task(10)
    def create_alarm(self):
        """ Simulates the user creating an alarm """
        alarm_time = self.generate_alarm_time()
        message = f"Test Alarm for user {self.user_id}"
        with self.alarm_lock:
            with self.client.post(
                "/alarms",
                json={
                    "user_id": self.user_id,
                    "time": alarm_time,
                    "message": message,
                    "status": "pending"
                },
                name="POST alarms/",
                catch_response=True
            ) as response:
                if self.handle_response(response, "Create Alarm Request"):
                    alarm_id = response.json().get("id")
                    if alarm_id:
                        self.alarms.append(alarm_id)

    @task(5)
    def delete_specific_alarm(self):
        """ Simulates the user deleting an alarm """
        if self.alarms:
            with self.alarm_lock:
                alarm_id = random.choice(self.alarms)
                with self.client.delete(
                    f"/alarms/{alarm_id}",
                    name="DELETE alarms/",
                    catch_response=True
                ) as response:
                    if self.handle_response(response, "Delete Alarm Request"):
                        if alarm_id in self.alarms:
                            self.alarms.remove(alarm_id)

    @task(5)
    def update_alarm(self):
        """ Simulates the user updating an alarm """
        if self.alarms:
            with self.alarm_lock:
                alarm_id = random.choice(self.alarms)
                new_message = f"Updated Alarm for user {self.user_id} [{random.randint(1, 100000)}]"
                alarm_time = self.generate_alarm_time()

                with self.client.put(
                    f"/alarms/{alarm_id}",
                    json={
                        "message": new_message,
                        "time": alarm_time
                    },
                    name="PUT alarms/",
                    catch_response=True
                ) as response:
                    self.handle_response(response, "Update Alarm Request")
                
    @task(5)
    def delete_notification(self):
        """ Simulates the user removing notifications """
        if self.notifications:
            with self.notif_lock:
                notification_id = random.choice(self.notifications)
                with self.client.delete(
                    f"/notifications/{notification_id}",
                    name="DELETE notifications/",
                    catch_response=True
                ) as response:
                    if self.handle_response(response, "Delete Notification Request"):
                        if notification_id in self.notifications:
                            self.notifications.remove(notification_id)


