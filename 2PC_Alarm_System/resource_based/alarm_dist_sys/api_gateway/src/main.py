from fastapi import FastAPI, Request, Response, Query
import httpx

ALARM_URL = "http://alarm_manager:5001/alarms"
USER_URL  = "http://user_manager:5002/users"
NOTIFICATION_URL = "http://notification_manager:5003/notifications"

app = FastAPI(title="API Gateway")

async def forward_request(request: Request, target_url: str) -> Response:
    try:
        response = await client.request(
            request.method,
            target_url,
            params=dict(request.query_params),
            content=await request.body(),
            headers=dict(request.headers),
        )

        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type")
        )
    except httpx.TimeoutException:
        return Response("Upstream timeout", status_code=504)
    except httpx.ConnectError:
        return Response("Upstream unavailable", status_code=503)
    except httpx.HTTPStatusError as e:
        return Response(f"HTTP Error: {e.response.status_code}", status_code=e.response.status_code)
    except Exception as e:
        return Response(f"Unexpected error: {e}", status_code=500)

@app.on_event("startup")
async def startup_event():
    global client
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(60, connect=3),
        limits=httpx.Limits(max_connections=1000, max_keepalive_connections=300),
    )

@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()

@app.get("/")
def root():
    return {"message": "API Gateway is running"}

@app.api_route("/alarms/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def alarms_proxy(request: Request, path: str):
    target_url = f"{ALARM_URL}/{path}" if path != "" else ALARM_URL
    return await forward_request(request, target_url)
    
@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def users_proxy(request: Request, path: str):
    target_url = f"{USER_URL}/{path}" if path != "" else USER_URL
    return await forward_request(request, target_url)

@app.api_route("/notifications/{path:path}", methods=["GET", "DELETE"])
async def notificaion_proxy(request: Request, path: str):
    target_url = f"{NOTIFICATION_URL}/{path}" if path != "" else NOTIFICATION_URL
    return await forward_request(request, target_url)
