import discord
import asyncio
import aiohttp

class Search:
    @staticmethod
    async def search(cid, sec, query, sector, display=100, sort='sim') -> dict:
        params = {
            'query': query,
            'display': display,
            'sort': sort
        }
        async with aiohttp.ClientSession() as s:
            async with s.get('https://openapi.naver.com/v1/search/{}.json'.format(sector), headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec}, params=params) as resp:
                rst = await resp.json()
        return rst
