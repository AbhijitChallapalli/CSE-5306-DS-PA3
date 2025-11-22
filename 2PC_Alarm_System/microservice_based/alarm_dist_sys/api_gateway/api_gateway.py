
# # can visit http://localhost:8080/

# import grpc, time
# from fastapi import FastAPI, Form, Request, Response
# from fastapi.responses import HTMLResponse, RedirectResponse
# from datetime import datetime, timedelta
# from itertools import count
# from google.protobuf.timestamp_pb2 import Timestamp
# from zoneinfo import ZoneInfo

# import alarm_pb2, alarm_pb2_grpc
# from google.protobuf import empty_pb2


# app = FastAPI(title="Distributed Alarm System API")

# # gRPC stubs
# storage_channel = grpc.insecure_channel("storage:50051")
# storage_stub = alarm_pb2_grpc.StorageStub(storage_channel)

# scheduler_channel = grpc.insecure_channel("scheduler:50052")
# scheduler_stub = alarm_pb2_grpc.SchedulerStub(scheduler_channel)

# account_channel = grpc.insecure_channel("accounts:50053")
# account_stub = alarm_pb2_grpc.AccountStub(account_channel)

# # coordinator stub
# coordinator_channel = grpc.insecure_channel("coordinator:60050")
# coordinator_stub = alarm_pb2_grpc.TwoPCCoordinatorStub(coordinator_channel)



# # notification vars
# notif_id_counter = count(1)
# notifications = []

# # alarm cache vars
# alarm_cache = {}


# # Dashboard
# @app.get("/dashboard", response_class=HTMLResponse)
# def home(request: Request):
#     user = getUser(request)
#     return f"""
#     <html>
#       <head>
#         <title>Alarm Dashboard</title>
#         <style>
#           body {{ font-family: Arial; background: #d6f6ff; padding: 2em; }}
#           h1 {{ color: #333; }}
#           form {{ margin-bottom: 1.5em; }}
#           input[type=text], input[type=time] {{ padding: 0.4em; margin-right: 0.5em; }}
#           input[type=submit], button {{ padding: 0.4em 0.8em; background: #0066cc; color: white; border: none; cursor: pointer; }}
#           input[type=submit]:hover, button:hover {{ background: #004c99; }}
#           .notif {{ background: #f5f5f5; padding: 0.5em; margin-top: 0.5em; border: 1px solid #ffeeba; border-radius: 4px; }}
#           table {{ border-collapse: collapse; width: 100%; background: white; }}
#           th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
#         </style>
#       </head>
#       <body>
#         <h1>Distributed Alarm System</h1>

#         <form action="/add" method="post">
#             <input type="hidden" name="username" value="{user.username}">
#             <input type="text" name="title" placeholder="Alarm title" required>
#             <input type="time" name="hhmm" required>
#             <input type="submit" value="Add Alarm">
#         </form>

#         <h2>Scheduled Alarms</h2>
#         <table>
#           <tr><th>ID</th><th>Title</th><th>Time</th><th>Actions</th></tr>
#           <tbody id="alarm-table"></tbody>
#         </table>

#         <h2>Notifications</h2>
#         <div id="notifications"></div>

#         <script>
#           async function fetchAlarms() {{
#             const resp = await fetch('/alarms_html');
#             document.getElementById('alarm-table').innerHTML = await resp.text();
#           }}

#           async function fetchNotifications() {{
#             const resp = await fetch('/notifications');
#             document.getElementById('notifications').innerHTML = await resp.text();
#           }}

#           async function dismissNotif(id) {{
#             await fetch(`/dismiss/${{id}}`, {{ method: 'POST' }});
#             const notifDiv = document.querySelector(`div[data-id='${{id}}']`);
#             if (notifDiv) notifDiv.remove();
#           }}

#           setInterval(fetchAlarms, 1000);
#           setInterval(fetchNotifications, 1000);
#           fetchAlarms();
#           fetchNotifications();
#         </script>
#       </body>
#     </html>
#     """


# LOCAL_TZ = ZoneInfo("America/Chicago")

# # Alarm display refresh 
# @app.get("/alarms_html", response_class=HTMLResponse)
# def alarms_html(request: Request):
#     user = getUser(request)
#     all_alarms=[]
#     if not getattr(user, "username", ""):   # check for logged in user
#         return Response(status_code=204)
#     try:
#         all_alarms = list(storage_stub.ListAlarms(user))
#     except grpc.RpcError as e:
#         if e.code() in ( grpc.StatusCode.INVALID_ARGUMENT, grpc.StatusCode.UNAVAILABLE):
#             return Response(status_code=204)

#     # filter alarms for the logged-in user
#     user_alarms = [a for a in all_alarms if a.user == user.username]
#     if not user_alarms:
#         return Response(status_code=204)
#     rows = ""
#     for alarm in user_alarms:
#         local_dt = datetime.fromtimestamp(alarm.time.seconds, LOCAL_TZ)
#         alarm_time = local_dt.strftime("%I:%M %p")
#         rows += f"""
#         <tr>
#             <td>{alarm.id}</td>
#             <td>{alarm.title}</td>
#             <td>{alarm_time}</td>
#             <td>
#                 <form action="/delete/{alarm.id}" method="post" style="display:inline;">
#                     <button type="submit">Delete</button>
#                 </form>
#                 <form action="/edit/{alarm.id}" method="get" style="display:inline;">
#                     <button type="submit">Edit</button>
#                 </form>
#             </td>
#         </tr>
#         """
#     return rows



# #Alarm management 
# # parse HH:MM user input to int timestamp
# def parse_alarm_time(hhmm: str) -> int:
#     now = datetime.now(LOCAL_TZ)
#     alarm_time_today = datetime.strptime(hhmm, "%H:%M").replace(year=now.year, month=now.month, day=now.day, tzinfo=LOCAL_TZ)
#     if alarm_time_today < now:
#         alarm_time_today += timedelta(days=1)
#     return int(alarm_time_today.timestamp())

# # Add Alarm
# @app.post("/add")
# def add_alarm(request: Request, title: str = Form(...), hhmm: str = Form(...)):
#     user = getUser(request)
#     if not user:
#         return RedirectResponse(url="/", status_code=303)   # user not logged in

#     secs = parse_alarm_time(hhmm)
#     trigger_time = Timestamp()
#     trigger_time.seconds = secs

#     alarm = alarm_pb2.Alarm(id=0, user=user.username, title=title, time=trigger_time)

#     # ---- 2PC via coordinator ----
#     two_pc_req = alarm_pb2.AddAlarmRequest(alarm=alarm)
#     ack = coordinator_stub.AddAlarm2PC(two_pc_req)
#     print(f"[API] 2PC result: success={ack.success}, message={ack.message}")

#     # ---- Persist alarm in Storage ONLY if global commit succeeded ----
#     if ack.success:
#         try:
#             storage_stub.AddAlarm(alarm)
#             print(f"[API] Stored alarm in Storage for user={alarm.user}, title={alarm.title}")
#         except grpc.RpcError as e:
#             # Optional: log error so you can see it in the container logs
#             print(f"[API] ERROR calling Storage.AddAlarm: code={e.code()} details={e.details()}")

#     return RedirectResponse(url="/dashboard", status_code=303)


# # Edit Alarm
# @app.get("/edit/{alarm_id}", response_class=HTMLResponse)
# def edit_form(alarm_id: int):
#     alarm = storage_stub.GetAlarm(alarm_pb2.AlarmId(id=alarm_id))
#     local_time = datetime.fromtimestamp(alarm.time.seconds, LOCAL_TZ)
#     hhmm = local_time.strftime("%H:%M")
#     return f"""
#     <html><body>
#     <h1>Edit Alarm {alarm.id}</h1>
#     <form action="/edit/{alarm.id}" method="post">
#       <input type="text" name="title" value="{alarm.title}" required>
#       <input type="time" name="hhmm" value="{hhmm}" required>
#       <input type="submit" value="Save">
#     </form>
#     </body></html>
#     """

# @app.post("/edit/{alarm_id}")
# def edit_alarm(alarm_id: int, title: str = Form(...), hhmm: str = Form(...)):
#     alarm = storage_stub.GetAlarm(alarm_pb2.AlarmId(id=alarm_id))
#     new_time = Timestamp(seconds= parse_alarm_time(hhmm))
#     updated_alarm = alarm_pb2.Alarm(id=alarm_id, user=alarm.user, title=title, time=new_time)
#     storage_stub.DeleteAlarm(alarm_pb2.AlarmId(id=alarm_id))
#     storage_stub.AddAlarm(updated_alarm)
#     return RedirectResponse(url="/dashboard", status_code=303)

# # Delete Alarm
# @app.post("/delete/{alarm_id}")
# def delete_alarm(alarm_id: int):
#     storage_stub.DeleteAlarm(alarm_pb2.AlarmId(id=alarm_id))
#     return RedirectResponse(url="/dashboard", status_code=303)






# # Notifications 
# @app.post("/notify")
# def notify(alarm: dict):
#     if "user" not in alarm:
#         return {"status": "no_user"}
#     notif = {"id": next(notif_id_counter), "user": alarm["user"], "text": f"{alarm['title']}!"}
#     notifications.append(notif)
#     return {"status": "ok"}


# @app.get("/notifications", response_class=HTMLResponse)
# def get_notifications(request: Request):
#     global notifications
#     user = getUser(request)
#     if not user:
#         return "<p>No user logged in</p>"
#     # Filter notifications for user
#     user_notifs = []
#     for n in notifications:
#         if n["user"] == user.username:
#             user_notifs.append(n)
#     if not user_notifs:
#         return "<p>No notifications</p>"
#     html = ""
#     for n in user_notifs[-10:]:  
#         html += f"""
#         <div class='notif' data-id='{n['id']}'>
#             {n['text']}
#             <button onclick="dismissNotif({n['id']})" style="font-size:0.8em; margin-left:10px;">Dismiss</button>
#         </div>
#         """
#     return html


# @app.post("/dismiss/{notif_id}")
# def dismiss_notification(notif_id: int, request: Request):
#     global notifications
#     user = getUser(request)
#     if not user:
#         return {"status": "no_user"}
#     for n in notifications:
#         if n["id"] == notif_id:
#             if n["user"] == user.username:
#                 notifications.remove(n)
#     return {"status": "ok"}  






# # login/account management implementation
# def getUser(request: Request):
#     token = request.cookies.get("token")
#     if not token:
#         return None
#     md = (("token", token), )
#     user = account_stub.GetUser(empty_pb2.Empty(), metadata=md)
#     if not user.username:
#         return None
#     return user

# @app.get("/", response_class=HTMLResponse)
# def login_page():
#     return """
#     <html>
#       <head>
#         <title>Login</title>
#         <style>
#           body { font-family: Arial; background: #d6f6ff; padding: 2em; }
#           h1 { color: #333; }
#           form { margin-bottom: 1em; }
#           input { padding: 0.4em; margin-right: 0.5em; }
#           button { padding: 0.4em 0.8em; background: #0066cc; color: white; border: none; cursor: pointer; margin-right: 0.5em; }
#           button:hover { background: #004c99; }
#         </style>
#       </head>
#       <body>
#         <h1>Distributed Alarm System </h1>
#         <form method="post">
#             <input type="text" name="username" placeholder="Username" required>
#             <input type="password" name="password" placeholder="Password" required>
#             <button type="submit" formaction="/login">Sign In</button>
#             <button type="submit" formaction="/signup">Sign Up</button>
#         </form>
#       </body>
#     </html>
#     """

# @app.post("/login")
# def login(username: str = Form(...), password: str = Form(...)):
#     user = alarm_pb2.User(username=username, password=password)
#     status = account_stub.VerifyUser(user)
#     if status.success == 1:
#         redirect = RedirectResponse(url="/dashboard", status_code=303)
#         redirect.set_cookie(key="token", value=status.token, httponly=False, samesite="lax")
#         return redirect
#     else:
#         return HTMLResponse("<p>Invalid username or password <a href='/'>Try again</a></p>")

# @app.post("/signup")
# def signup(username: str = Form(...), password: str = Form(...)):
#     user = alarm_pb2.User(username=username, password=password)
#     status = account_stub.AddUser(user)
#     if status.success == 1:
#         redirect = RedirectResponse(url="/dashboard", status_code=303)
#         redirect.set_cookie(key="token", value=status.token, httponly=False, samesite="lax")
#         return redirect
#     else:
#         return HTMLResponse("<p>Signup failed — user already exists <a href='/'>Try again</a></p>")

# can visit http://localhost:8080/

import grpc, time
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timedelta
from itertools import count
from google.protobuf.timestamp_pb2 import Timestamp
from zoneinfo import ZoneInfo

import alarm_pb2, alarm_pb2_grpc
from google.protobuf import empty_pb2

app = FastAPI(title="Distributed Alarm System API")

# gRPC stubs
storage_channel = grpc.insecure_channel("storage:50051")
storage_stub = alarm_pb2_grpc.StorageStub(storage_channel)

scheduler_channel = grpc.insecure_channel("scheduler:50052")
scheduler_stub = alarm_pb2_grpc.SchedulerStub(scheduler_channel)

account_channel = grpc.insecure_channel("accounts:50053")
account_stub = alarm_pb2_grpc.AccountStub(account_channel)

# coordinator stub
coordinator_channel = grpc.insecure_channel("coordinator:60050")
coordinator_stub = alarm_pb2_grpc.TwoPCCoordinatorStub(coordinator_channel)

# notification vars
notif_id_counter = count(1)
notifications = []

# alarm cache vars (unused but kept if you want caching later)
alarm_cache = {}

LOCAL_TZ = ZoneInfo("America/Chicago")


# ---------------- Dashboard ----------------

@app.get("/dashboard", response_class=HTMLResponse)
def home(request: Request):
    user = getUser(request)
    return f"""
    <html>
      <head>
        <title>Alarm Dashboard</title>
        <style>
          body {{ font-family: Arial; background: #d6f6ff; padding: 2em; }}
          h1 {{ color: #333; }}
          form {{ margin-bottom: 1.5em; }}
          input[type=text], input[type=time] {{ padding: 0.4em; margin-right: 0.5em; }}
          input[type=submit], button {{ padding: 0.4em 0.8em; background: #0066cc; color: white; border: none; cursor: pointer; }}
          input[type=submit]:hover, button:hover {{ background: #004c99; }}
          .notif {{ background: #f5f5f5; padding: 0.5em; margin-top: 0.5em; border: 1px solid #ffeeba; border-radius: 4px; }}
          table {{ border-collapse: collapse; width: 100%; background: white; }}
          th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        </style>
      </head>
      <body>
        <h1>Distributed Alarm System</h1>

        <form action="/add" method="post">
            <input type="hidden" name="username" value="{getattr(user, "username", "")}">
            <input type="text" name="title" placeholder="Alarm title" required>
            <input type="time" name="hhmm" required>
            <input type="submit" value="Add Alarm">
        </form>

        <h2>Scheduled Alarms</h2>
        <table>
          <tr><th>ID</th><th>Title</th><th>Time</th><th>Actions</th></tr>
          <tbody id="alarm-table"></tbody>
        </table>

        <h2>Notifications</h2>
        <div id="notifications"></div>

        <script>
          async function fetchAlarms() {{
            const resp = await fetch('/alarms_html');
            if (resp.status === 200) {{
              document.getElementById('alarm-table').innerHTML = await resp.text();
            }} else {{
              document.getElementById('alarm-table').innerHTML = '';
            }}
          }}

          async function fetchNotifications() {{
            const resp = await fetch('/notifications');
            document.getElementById('notifications').innerHTML = await resp.text();
          }}

          async function dismissNotif(id) {{
            await fetch(`/dismiss/${{id}}`, {{ method: 'POST' }});
            const notifDiv = document.querySelector(`div[data-id='${{id}}']`);
            if (notifDiv) notifDiv.remove();
          }}

          setInterval(fetchAlarms, 1000);
          setInterval(fetchNotifications, 1000);
          fetchAlarms();
          fetchNotifications();
        </script>
      </body>
    </html>
    """


# ---------------- Alarm display refresh ----------------

@app.get("/alarms_html", response_class=HTMLResponse)
def alarms_html(request: Request):
    user = getUser(request)
    all_alarms = []
    if not getattr(user, "username", ""):   # check for logged in user
        return Response(status_code=204)
    try:
        all_alarms = list(storage_stub.ListAlarms(user))
    except grpc.RpcError as e:
        if e.code() in (grpc.StatusCode.INVALID_ARGUMENT, grpc.StatusCode.UNAVAILABLE):
            return Response(status_code=204)

    # filter alarms for the logged-in user
    user_alarms = [a for a in all_alarms if a.user == user.username]
    if not user_alarms:
        return Response(status_code=204)

    rows = ""
    for alarm in user_alarms:
        local_dt = datetime.fromtimestamp(alarm.time.seconds, LOCAL_TZ)
        alarm_time = local_dt.strftime("%I:%M %p")
        rows += f"""
        <tr>
            <td>{alarm.id}</td>
            <td>{alarm.title}</td>
            <td>{alarm_time}</td>
            <td>
                <form action="/delete/{alarm.id}" method="post" style="display:inline;">
                    <button type="submit">Delete</button>
                </form>
                <form action="/edit/{alarm.id}" method="get" style="display:inline;">
                    <button type="submit">Edit</button>
                </form>
            </td>
        </tr>
        """
    return rows


# ---------------- Alarm management ----------------

def parse_alarm_time(hhmm: str) -> int:
    """Parse HH:MM into a future timestamp (today or tomorrow)."""
    now = datetime.now(LOCAL_TZ)
    alarm_time_today = datetime.strptime(hhmm, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=LOCAL_TZ
    )
    if alarm_time_today < now:
        alarm_time_today += timedelta(days=1)
    return int(alarm_time_today.timestamp())


# Add Alarm via 2PC
@app.post("/add")
def add_alarm(request: Request, title: str = Form(...), hhmm: str = Form(...)):
    user = getUser(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)   # user not logged in

    secs = parse_alarm_time(hhmm)
    trigger_time = Timestamp()
    trigger_time.seconds = secs

    alarm = alarm_pb2.Alarm(id=0, user=user.username, title=title, time=trigger_time)

    two_pc_req = alarm_pb2.AddAlarmRequest(alarm=alarm)
    ack = coordinator_stub.AddAlarm2PC(two_pc_req)

    print(f"[API] 2PC result: success={ack.success}, message={ack.message}")

    # 2PC participants (scheduler/accounts) handle commit/abort.
    # We just redirect back to dashboard.
    return RedirectResponse(url="/dashboard", status_code=303)


# Edit Alarm (directly via Storage)
@app.get("/edit/{alarm_id}", response_class=HTMLResponse)
def edit_form(alarm_id: int):
    alarm = storage_stub.GetAlarm(alarm_pb2.AlarmId(id=alarm_id))
    local_time = datetime.fromtimestamp(alarm.time.seconds, LOCAL_TZ)
    hhmm = local_time.strftime("%H:%M")
    return f"""
    <html><body>
    <h1>Edit Alarm {alarm.id}</h1>
    <form action="/edit/{alarm.id}" method="post">
      <input type="text" name="title" value="{alarm.title}" required>
      <input type="time" name="hhmm" value="{hhmm}" required>
      <input type="submit" value="Save">
    </form>
    </body></html>
    """


@app.post("/edit/{alarm_id}")
def edit_alarm(alarm_id: int, title: str = Form(...), hhmm: str = Form(...)):
    alarm = storage_stub.GetAlarm(alarm_pb2.AlarmId(id=alarm_id))
    new_time = Timestamp(seconds=parse_alarm_time(hhmm))
    updated_alarm = alarm_pb2.Alarm(id=alarm_id, user=alarm.user, title=title, time=new_time)
    storage_stub.DeleteAlarm(alarm_pb2.AlarmId(id=alarm_id))
    storage_stub.AddAlarm(updated_alarm)
    return RedirectResponse(url="/dashboard", status_code=303)


# Delete Alarm
@app.post("/delete/{alarm_id}")
def delete_alarm(alarm_id: int):
    storage_stub.DeleteAlarm(alarm_pb2.AlarmId(id=alarm_id))
    return RedirectResponse(url="/dashboard", status_code=303)


# ---------------- Notifications ----------------

@app.post("/notify")
def notify(alarm: dict):
    if "user" not in alarm:
        return {"status": "no_user"}
    notif = {"id": next(notif_id_counter), "user": alarm["user"], "text": f"{alarm['title']}!"}
    notifications.append(notif)
    return {"status": "ok"}


@app.get("/notifications", response_class=HTMLResponse)
def get_notifications(request: Request):
    global notifications
    user = getUser(request)
    if not user:
        return "<p>No user logged in</p>"

    user_notifs = [n for n in notifications if n["user"] == user.username]
    if not user_notifs:
        return "<p>No notifications</p>"

    html = ""
    for n in user_notifs[-10:]:
        html += f"""
        <div class='notif' data-id='{n['id']}'>
            {n['text']}
            <button onclick="dismissNotif({n['id']})" style="font-size:0.8em; margin-left:10px;">Dismiss</button>
        </div>
        """
    return html


@app.post("/dismiss/{notif_id}")
def dismiss_notification(notif_id: int, request: Request):
    global notifications
    user = getUser(request)
    if not user:
        return {"status": "no_user"}
    notifications = [n for n in notifications if not (n["id"] == notif_id and n["user"] == user.username)]
    return {"status": "ok"}


# ---------------- Login / account ----------------

def getUser(request: Request):
    token = request.cookies.get("token")
    if not token:
        return None
    md = (("token", token),)
    user = account_stub.GetUser(empty_pb2.Empty(), metadata=md)
    if not user.username:
        return None
    return user


@app.get("/", response_class=HTMLResponse)
def login_page():
    return """
    <html>
      <head>
        <title>Login</title>
        <style>
          body { font-family: Arial; background: #d6f6ff; padding: 2em; }
          h1 { color: #333; }
          form { margin-bottom: 1em; }
          input { padding: 0.4em; margin-right: 0.5em; }
          button { padding: 0.4em 0.8em; background: #0066cc; color: white; border: none; cursor: pointer; margin-right: 0.5em; }
          button:hover { background: #004c99; }
        </style>
      </head>
      <body>
        <h1>Distributed Alarm System </h1>
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" formaction="/login">Sign In</button>
            <button type="submit" formaction="/signup">Sign Up</button>
        </form>
      </body>
    </html>
    """


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = alarm_pb2.User(username=username, password=password)
    status = account_stub.VerifyUser(user)
    if status.success == 1:
        redirect = RedirectResponse(url="/dashboard", status_code=303)
        redirect.set_cookie(key="token", value=status.token, httponly=False, samesite="lax")
        return redirect
    else:
        return HTMLResponse("<p>Invalid username or password <a href='/'>Try again</a></p>")


@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    user = alarm_pb2.User(username=username, password=password)
    status = account_stub.AddUser(user)
    if status.success == 1:
        redirect = RedirectResponse(url="/dashboard", status_code=303)
        redirect.set_cookie(key="token", value=status.token, httponly=False, samesite="lax")
        return redirect
    else:
        return HTMLResponse("<p>Signup failed — user already exists <a href='/'>Try again</a></p>")
