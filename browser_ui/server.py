import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from omdb_api import search_imdb, search_imdb_details
from torrents_api import search_torrents


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/search")
async def search(q: str):
    data = await search_imdb(q)
    return { "data": data }

@app.get("/details")
async def read_content_details(q: str):
    data = await search_imdb_details(q)
    return { "data": data }

@app.get("/get_torrents")
async def find_torrent(q: str):
    data = await search_torrents(q)
    return { "data": data }
