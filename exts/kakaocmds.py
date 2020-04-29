import discord
from discord.ext import commands
import datetime
import re
import json
import asyncio
from exts.utils import pager
from exts.utils.basecog import BaseCog
from exts.apis import kakaoapi

class Kakaocmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)

    @commands.command(name='주소검색')
    async def _address_search(self, ctx: commands.Context, *, query):
        rst = await kakaoapi.AddressSearch.search_address(self.openapi['kakao']['clientSec'], query)
        pgr = pager.Pager(rst["documents"], perpage=5)
        embed = kakaoapi.AddressSearch.search_address_make_embed(pgr.get_thispage(), pgr.now_pagenum() + 1, len(pgr.pages()), rst["meta"]["total_count"])
        
        await ctx.send(embed=embed)
        

def setup(client):
    cog = Kakaocmds(client)
    client.add_cog(cog)