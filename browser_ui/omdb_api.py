import urllib.parse

import httpx

OMDB_API_KEY = 'c9095ed5'

def build_omdb_api_req(url: str):
    return url + f'&apikey={OMDB_API_KEY}'

async def search_imdb(query: str):
    url = build_omdb_api_req(f'https://www.omdbapi.com/?s={urllib.parse.quote(query)}')
    print(url)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            print(url, response.json(), response)
            print(f"IMDb API request failed with status code {response.status_code}")
            print("Make sure you have a valid OMDB API key")
            return { }
        data = response.json()
        if 'error' in data:
            print(f"IMDb API error: {data['error']}")
            return { }
        return data

async def search_imdb_details(imdb_id: str):
    url = build_omdb_api_req(f'https://www.omdbapi.com/?i={imdb_id}')
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            print(url, response.json(), response)
            print(f"IMDb API request failed with status code {response.status_code}")
            print("Make sure you have a valid OMDB API key")
            return { }
        data = response.json()
        if 'error' in data:
            print(f"IMDb API error: {data['error']}")
            return { }
        return data
