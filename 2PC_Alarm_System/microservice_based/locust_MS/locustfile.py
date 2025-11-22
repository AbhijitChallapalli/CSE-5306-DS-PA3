from locust import HttpUser, task, between
import random
import gevent
from datetime import datetime, timedelta

class DistAlarmUser(HttpUser):
    wait_time = between(1, 3)   # user will wait between 2 and 5 seconds after tasks

    def on_start(self):
        self.username = f"user{random.randint(1,50)}"  # make random signin
        login = {"username": self.username, "password": "pass"}
        status = self.client.post("/login", data=login)     # try to login
        if "/dashboard" not in status.url:
            self.client.post("/signup", data=login, name="Sign Up")         # else sign up
        self.alarm_greenlet = gevent.spawn(self.view_alarms)
        self.notif_greenlet = gevent.spawn(self.view_notifications)
    
    def on_stop(self):
        if hasattr(self, "alarm_greenlet"):
            self.alarm_greenlet.kill()
        if hasattr(self, "notif_greenlet"):
            self.notif_greenlet.kill()
    
    def view_alarms(self):
        while True:
            self.client.get("/alarms_html",  name="Get Alarms")
            gevent.sleep(1)

    def view_notifications(self):
        while True:
            self.client.get("/notifications",  name="Get Notifs")
            gevent.sleep(1)

    @task(10)
    def add_alarm(self):
        now = datetime.now()
        offset = random.randint(0, 180) # make random alarm for the next 3 minutes
        alarm_time = now + timedelta(seconds=offset)
        hhmm = alarm_time.strftime("%H:%M")
        data = {"title": f"LoadTest Alarm","hhmm": hhmm,"username": self.username}
        self.client.post("/add", data=data, name="Add Alarm")

    @task(5)
    def update_alarm(self):
        """Simulate occasionally editing an existing alarm, rescheduling it within the next 3 minutes."""
        try:
            alarm_id = random.randint(1, 20)  # simulate random existing alarm
            # pick a random new time in the next 3 minutes
            new_time = datetime.now() + timedelta(seconds=random.randint(0, 180))
            hhmm = new_time.strftime("%H:%M")
            data = {
                "title": f"Updated Alarm {alarm_id}",
                "hhmm": hhmm
            }
            self.client.post(f"/edit/{alarm_id}", data=data, name="Update Alarm")
        except Exception:
            pass

    @task(5)
    def dismiss_random_notif(self):
        notif_id = random.randint(1, 20)
        self.client.post(f"/dismiss/{notif_id}", name="Dismiss Notif")

    @task(5)
    def delete_alarm(self):
        try:
            alarm_id = random.randint(1, 20)
            self.client.post(f"/delete/{alarm_id}", name="Delete Alarm")
        except Exception:
            pass
