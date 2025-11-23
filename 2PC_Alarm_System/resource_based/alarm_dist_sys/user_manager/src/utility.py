import requests

ALARM_URL = "http://alarm_manager:5001/alarms"
NOTIFICATIONS_URL = "http://notification_manager:5003/notifications"

def delete_alarms_for_user(user_id: int):
    response = requests.delete(f"{ALARM_URL}", params={"user_id": user_id})
    if not response.ok:
        print(f"[User Manager] Failed to delete alarms for user {user_id}: {response.status_code}")

def delete_notifications_for_user(user_id: int):
    response = requests.delete(f"{NOTIFICATIONS_URL}", params={"user_id": user_id})
    if not response.ok:
        print(f"[User Manager] Failed to delete alarms for user {user_id}: {response.status_code}")