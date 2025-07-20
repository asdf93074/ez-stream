import mimetypes
import sys
import os

from engine import TorrentEngine
from downloader import TorrentDownloader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Union

from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse, StreamingResponse
import aiofiles
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
async def download_file(magnet_link: str = Body(...), file_choice: Union[int, str] = Body(...), save_path: str = Body(...)):
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
async def stream_file(file_path: str, request: Request):
    if not os.path.exists(file_path):
        return {"error": "File not found."}

    file_size = os.path.getsize(file_path)
    media_type, _ = mimetypes.guess_type(file_path)
    if not media_type:
        media_type = "application/octet-stream"

    range_header = request.headers.get("Range")

    if range_header:
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0])
        end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
        content_length = (end - start) + 1
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(content_length),
            "Accept-Ranges": "bytes",
        }
        status_code = 206
    else:
        start = 0
        end = file_size - 1
        content_length = file_size
        headers = {
            "Content-Length": str(content_length),
            "Accept-Ranges": "bytes",
        }
        status_code = 200

    async def file_iterator():
        async with aiofiles.open(file_path, mode="rb") as f:
            await f.seek(start)
            while (chunk := await f.read(8192)):
                yield chunk

    return StreamingResponse(file_iterator(), media_type=media_type, headers=headers, status_code=status_code)
