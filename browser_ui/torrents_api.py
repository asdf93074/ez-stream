import urllib.parse
import httpx

async def search_torrents(title: str):
    pb_query = urllib.parse.quote(title)
    pb_url = f'https://apibay.org/q.php?q={pb_query}&cat=200'
    async with httpx.AsyncClient() as client:
        response = await client.get(pb_url)
        return response.json()
