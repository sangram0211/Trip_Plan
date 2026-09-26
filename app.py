import os
from pathlib import Path
import traceback
import uvicorn

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.api.sessions import (
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    clear_credentials,
    get_credentials_for,
    new_session_id,
    store_credentials,
)
from src.api.validation import check_database_url, check_groq_api_key
from src.clients import cache
from src.config.session import (
    MissingCredentialsError,
    credential_status,
    use_credentials,
)
from src.config.settings import COOKIE_SAMESITE, COOKIE_SECURE, CORS_ORIGINS
from src.graph.runner import run_travel_agent

# This is to allow nested event loops for async calls in FastAPI
import nest_asyncio
nest_asyncio.apply()


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Trip Planner AI",
    description="LangGraph Multi-Agent Trip Planner with FastAPI Frontend",
    version="1.0.0"
)


# Only needed when the browser talks to this API on a different origin. With
# the Vercel rewrite the frontend is same-origin, so this stays inactive.
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )


app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR / "static")),
    name="static"
)


templates = Jinja2Templates(
    directory=str(FRONTEND_DIR / "templates")
)



class TravelRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ConfigRequest(BaseModel):
    """
    None leaves a field untouched, "" clears it. Keys are held in server
    memory for this session only and are never echoed back.
    """
    groq_api_key: str | None = None
    database_url: str | None = None



def _session_id(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Trip Planner AI"}


@app.get("/api/config")
async def get_config(request: Request, response: Response):
    session_id = _session_id(request)
    creds = get_credentials_for(session_id) if session_id else None

    status = credential_status(creds)

    if not session_id:
        session_id = new_session_id()
        _set_session_cookie(response, session_id)

    return JSONResponse(status)


@app.post("/api/config")
async def set_config(payload: ConfigRequest, request: Request, response: Response):
    session_id = _session_id(request) or new_session_id()

    current = get_credentials_for(session_id)

    errors: dict[str, str] = {}

    groq_key = payload.groq_api_key
    db_url   = payload.database_url

    if groq_key is not None:
        if groq_key == "":
            groq_key = None
        else:
            ok, msg = check_groq_api_key(groq_key)
            if not ok:
                errors["groq_api_key"] = msg

    if db_url is not None:
        if db_url == "":
            db_url = None
        else:
            ok, msg = check_database_url(db_url)
            if not ok:
                errors["database_url"] = msg

    if errors:
        return JSONResponse({"ok": False, "errors": errors}, status_code=400)

    from src.config.session import Credentials
    updated = Credentials(
        groq_api_key=groq_key if groq_key is not None else (current.groq_api_key if current else None),
        database_url=db_url   if db_url   is not None else (current.database_url  if current else None),
    )

    store_credentials(session_id, updated)
    _set_session_cookie(response, session_id)

    return {"ok": True}


@app.delete("/api/config")
async def clear_config(request: Request, response: Response):
    session_id = _session_id(request)
    if session_id:
        clear_credentials(session_id)
    return {"ok": True}


@app.post("/api/travel")
async def travel(payload: TravelRequest, request: Request, response: Response):
    session_id = _session_id(request) or new_session_id()
    creds = get_credentials_for(session_id)

    try:
        with use_credentials(creds):
            result = run_travel_agent(
                user_input=payload.message,
                thread_id=payload.thread_id,
            )

        _set_session_cookie(response, session_id)

        messages = result.get("messages", [])
        last_ai = next(
            (m for m in reversed(messages) if hasattr(m, "content") and m.type == "ai"),
            None,
        )

        return {
            "reply": last_ai.content if last_ai else "No response generated.",
            "thread_id": result.get("thread_id", payload.thread_id),
        }

    except MissingCredentialsError as exc:
        return JSONResponse(
            {"error": "missing_credentials", "missing": exc.missing},
            status_code=401,
        )
    except Exception:
        traceback.print_exc()
        return JSONResponse(
            {"error": "internal", "detail": "An unexpected error occurred."},
            status_code=500,
        )


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
