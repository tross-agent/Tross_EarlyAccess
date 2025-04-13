import uuid
from sqlalchemy import ForeignKey, inspect
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship , session
from sqlalchemy.sql import func
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.declarative import declarative_base
import typing
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import requests
import json
import uvicorn
import os
import urllib
from server import app
from sqlalchemy.orm import Session
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class AuthReq(BaseModel):
    token:str

class Token(Base):
    __tablename__ = "token"

    id: Mapped[int] = mapped_column(primary_key=True)
    token :Mapped[uuid] = mapped_column() # type: ignore


@app.post("/authenticate")
def authenticate(auth_req:AuthReq, db= Depends(get_db)):
    token = auth_req.token
    query= Token.select().where(Token.c.token == token)
    try:
        res =db.execute(query).fetchone()
    except Exception as e:
        raise HTTPException()
