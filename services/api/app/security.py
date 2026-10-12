"""Opaque HttpOnly sessions with origin verification and Argon2id password hashing."""
import os, secrets, hashlib, smtplib
from datetime import datetime,timezone,timedelta
from email.message import EmailMessage
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from .db import get_db
from .models import User, Session

hasher=PasswordHasher(time_cost=3,memory_cost=65536,parallelism=2)
COOKIE="pipmora_session"
def token_digest(s):return hashlib.sha256(s.encode()).hexdigest()
def hash_password(s):return hasher.hash(s)
def verify_password(h,s):
    try:return hasher.verify(h,s)
    except (VerifyMismatchError,VerificationError):return False

def trusted_origin(request: Request):
    if request.method in ("GET","HEAD","OPTIONS"):return
    origin=request.headers.get("origin")
    allowed=os.getenv("FRONTEND_ORIGIN","http://localhost:3000").split(",")
    if origin and origin not in allowed:raise HTTPException(403,"Untrusted origin")

def current_user(request:Request,db:DBSession=Depends(get_db)):
    raw=request.cookies.get(COOKIE)
    if not raw:raise HTTPException(401,"Please sign in")
    s=db.query(Session).filter(Session.token_hash==token_digest(raw),Session.revoked==False).first()
    if not s:raise HTTPException(401,"Session expired")
    end=s.expires_at.replace(tzinfo=timezone.utc) if s.expires_at.tzinfo is None else s.expires_at
    if end<datetime.now(timezone.utc): raise HTTPException(401,"Session expired")
    user=db.get(User,s.user_id)
    if not user:raise HTTPException(401,"Account no longer exists")
    return user

def issue_session(db,user):
    raw=secrets.token_urlsafe(48)
    db.add(Session(user_id=user.id,token_hash=token_digest(raw),expires_at=datetime.now(timezone.utc)+timedelta(days=7)))
    return raw

def set_cookie(response,raw):
    response.set_cookie(COOKIE,raw,httponly=True,secure=os.getenv("COOKIE_SECURE","false").lower()=="true",samesite="lax",max_age=7*86400,path="/")

def email_reset(to,link):
    server=os.getenv("SMTP_HOST")
    if not server:return False
    m=EmailMessage();m["Subject"]="Reset your PipMora password";m["From"]=os.environ["SMTP_FROM"];m["To"]=to
    m.set_content(f"Use this one-time link within 30 minutes: {link}\nIf you didn't request a reset, ignore this email.")
    with smtplib.SMTP(server,int(os.getenv("SMTP_PORT","587")),timeout=10) as client:
        if os.getenv("SMTP_TLS","true")=="true":client.starttls()
        if os.getenv("SMTP_USER"):client.login(os.environ["SMTP_USER"],os.environ["SMTP_PASSWORD"])
        client.send_message(m)
    return True
