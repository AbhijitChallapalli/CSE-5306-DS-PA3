import asyncio
from datetime import datetime, timezone
import aiohttp

ALARM_URL = "http://alarm_manager:5001/alarms"
NOTIFY_URL = "http://notification_manager:5003/notifications"

session: aiohttp.ClientSession | None = None
POLL_INTERVAL = .5  # 500ms

async def process_alarm(alarm: dict):
    """ Processes alarms and updates their status """
    try:
        alarm_time = datetime.fromisoformat(alarm["time"])
        if alarm_time.tzinfo is None:
            alarm_time = alarm_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if now >= alarm_time:
            status = "notified" if (now - alarm_time).total_seconds() <= 60 else "late"

            # Update alarm status
            async with session.put(f"{ALARM_URL}/{alarm['id']}", json={"status": status}) as resp:
                if resp.status != 200:
                    print(f"[Scheduler] Failed to update alarm {alarm['id']}: {resp.status}")
                    return
                alarm_data = await resp.json()

            # Create a Notification
            async with session.post(f"{NOTIFY_URL}/{alarm_data['user_id']}", json={"message": alarm_data["message"]}) as notify_resp:
                print(f"[Scheduler] Alarm {alarm['id']} processed. Status={status}, Notification sent. Response={notify_resp.status}")

    except Exception as e:
        print(f"[Scheduler] Error processing alarm {alarm.get('id')}: {e}")

async def poll_pending_alarms():
    """ Fetches and handles all pending alarms """
    try:
        async with session.get(ALARM_URL, params={"status": "pending"}) as response:
            if response.status != 200:
                print(f"[Scheduler] Failed to fetch pending alarms: {response.status}")
                return

            alarms = await response.json()
            for alarm in alarms:
                await process_alarm(alarm)

    except Exception as e:
        print(f"[Scheduler] Error during polling: {e}")


async def main():
    global session
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))
    print("[Scheduler] Alarm polling service started")

    try:
        while True:
            await poll_pending_alarms()
            await asyncio.sleep(POLL_INTERVAL)
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
