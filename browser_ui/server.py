import sys
import os

from engine import TorrentEngine
from downloader import TorrentDownloader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from omdb_api import search_imdb, search_imdb_details
from torrents_api import search_torrents

# Initialize TorrentEngine and TorrentDownloader globally
# In a production app, consider dependency injection for better management
torrent_engine = TorrentEngine("./out")
torrent_downloader = TorrentDownloader(torrent_engine)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def fetch_torrent_metadata(ml: str):
    torrent_engine = TorrentEngine("./out")
    torrent_engine.add_magnet(ml)
    return torrent_engine.fetch_metadata()

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

@app.get("/get_torrent_metadata")
async def find_torrent_metadata(q: str):
    data = fetch_torrent_metadata(q)
    return { "data": data }

@app.post("/download_file")
async def download_file(magnet_link: str, file_choice: Union[int, str], save_path: str):
    metadata = fetch_torrent_metadata(magnet_link)
    if not metadata:
        return {"error": "Could not fetch torrent metadata."}

    try:
        abs_path, file_index, file_size = torrent_downloader.download_file(
            metadata, file_choice, save_path
        )
        return {"message": "Download started", "file_path": abs_path, "file_index": file_index, "file_size": file_size}
    except (IndexError, FileNotFoundError, TypeError) as e:
        return {"error": str(e)}

@app.get("/stream_file")
async def stream_file(file_path: str):
    import mimetypes

    if not os.path.exists(file_path):
        return {"error": "File not found."}
    
    media_type, _ = mimetypes.guess_type(file_path)
    if not media_type:
        media_type = "application/octet-stream" # Default if type cannot be guessed

    return FileResponse(file_path, media_type=media_type)
