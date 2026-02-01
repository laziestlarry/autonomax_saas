from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select

from .settings import settings
from .db import engine, get_db
from .models import Base, User
from .schemas import RegisterIn, LoginIn, TokenOut, OpsRunIn
from .security import hash_password, verify_password, create_access_token, decode_token
from .ops import acquire_lock

app = FastAPI(title="Autonomax API", version="1.0.0")

# CORS
origins = ["*"]
try:
    if settings.cors_origins and settings.cors_origins != "*":
        # supports JSON array string
        import json
        origins = json.loads(settings.cors_origins)
except Exception:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (starter behavior). In production, switch to Alembic migrations.
Base.metadata.create_all(bind=engine)

def require_admin(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")):
    if not settings.admin_secret_key:
        raise HTTPException(status_code=500, detail="ADMIN_SECRET_KEY not configured")
    if x_admin_key != settings.admin_secret_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")

def get_current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    return payload["sub"]

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1"/>
    <title>Autonomax</title>
    <style>
      body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto;max-width:900px;margin:40px auto;padding:0 16px;line-height:1.5}
      code{background:#f3f3f3;padding:2px 6px;border-radius:6px}
      .card{border:1px solid #e6e6e6;border-radius:14px;padding:18px;margin:14px 0}
      button{padding:10px 14px;border-radius:10px;border:1px solid #ddd;background:white;cursor:pointer}
      input{padding:10px;border-radius:10px;border:1px solid #ddd;width:100%;max-width:420px}
      .row{display:flex;gap:10px;flex-wrap:wrap}
    </style>
  </head>
  <body>
    <h1>Autonomax</h1>
    <p>Backend is live. Next step: connect your frontend + billing.</p>

    <div class="card">
      <h3>Health</h3>
      <div class="row">
        <button onclick="hit('/healthz')">/healthz</button>
        <button onclick="hit('/readyz')">/readyz</button>
      </div>
      <pre id="out"></pre>
    </div>

    <div class="card">
      <h3>Quick onboard test (register + login)</h3>
      <input id="email" placeholder="email" value="test@example.com" />
      <input id="pwd" placeholder="password (min 8)" value="changeme123" />
      <div class="row">
        <button onclick="register()">Register</button>
        <button onclick="login()">Login</button>
        <button onclick="me()">/api/me</button>
      </div>
      <pre id="auth"></pre>
    </div>

    <script>
      let token = null;
      async function hit(path){
        const r = await fetch(path);
        document.getElementById('out').textContent = await r.text();
      }
      async function register(){
        const email=document.getElementById('email').value;
        const password=document.getElementById('pwd').value;
        const r = await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
        document.getElementById('auth').textContent = await r.text();
      }
      async function login(){
        const email=document.getElementById('email').value;
        const password=document.getElementById('pwd').value;
        const r = await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
        const txt = await r.text();
        try{ token = JSON.parse(txt).access_token }catch(e){}
        document.getElementById('auth').textContent = txt;
      }
      async function me(){
        const r = await fetch('/api/me',{headers:{'Authorization':'Bearer '+token}});
        document.getElementById('auth').textContent = await r.text();
      }
    </script>
  </body>
</html>"""

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/readyz")
def readyz(db: Session = Depends(get_db)):
    # basic DB probe
    try:
        db.execute(select(1))
        return {"ready": True}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"db not ready: {type(e).__name__}")

@app.post("/api/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    u = User(email=body.email, password_hash=hash_password(body.password))
    db.add(u)
    db.commit()
    return TokenOut(access_token=create_access_token(sub=body.email))

@app.post("/api/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenOut(access_token=create_access_token(sub=u.email))

@app.get("/api/me")
def me(user_email: str = Depends(get_current_user)):
    return {"email": user_email}

# ---- OPS ROUTES (Cloud Scheduler compatible) ----

@app.post("/api/ops/run", dependencies=[Depends(require_admin)])
def ops_run(body: OpsRunIn | None = None, db: Session = Depends(get_db)):
    # Cloud Scheduler can call with no body -> body will be None
    task = (body.task if body else None) or "hourly-batch"
    if not acquire_lock(db, f"ops:{task}"):
        raise HTTPException(status_code=429, detail="Rate limit active for task")
    # Here you'd enqueue Cloud Tasks / PubSub for real work. For now, just ack.
    return {"status": "queued", "task": task}

@app.post("/api/ops/run/ledger-monitor", dependencies=[Depends(require_admin)])
def ledger_monitor(db: Session = Depends(get_db)):
    task = "ledger-monitor"
    if not acquire_lock(db, f"ops:{task}"):
        raise HTTPException(status_code=429, detail="Rate limit active for task")
    return {"status": "queued", "task": task}

@app.post("/api/ops/run/shopier-verify", dependencies=[Depends(require_admin)])
def shopier_verify(db: Session = Depends(get_db)):
    task = "shopier-verify"
    if not acquire_lock(db, f"ops:{task}"):
        raise HTTPException(status_code=429, detail="Rate limit active for task")
    return {"status": "queued", "task": task}
