import discord
from discord.ext import commands
from exts.utils.basecog import BaseCog
import asyncio
from exts.apis import naverapi

class Navercmd(BaseCog):
    sectors = {
        '블로그': 'blog',
        '뉴스': 'news',
        '책': 'book',
        '백과사전': 'encyc',
        '카페글': 'cafearticle',
        '지식인': 'kin',
        '웹문서': 'webkr',
        '이미지': 'image',
        '쇼핑': 'shop',
        '전문자료': 'doc'
    }
    options = {
        'sim': ['blog', 'news', 'book', 'cafearticle', 'kin', 'image', 'shop'],
        'date': ['blog', 'news', 'book', 'cafearticle', 'kin', 'image', 'shop'],
        'asc': ['shop'],
        'dsc': ['shop'],
        'count': ['book']
    }
    formats = {
        '--정확도순': 'sim',
        '--최신순': 'date',
        '--저렴한순': 'asc',
        '--비싼순': 'dsc',
        '--판매량순': 'count'
    }

    @classmethod
    def paramchecker(self, sector: str, param: str) -> int:
        """
        If option does not exist: 0
        If option exists but cannot be used in this sector: 2
        If option exists and can be used: sector code
        """
        if param in Navercmd.formats.keys():
            op = Navercmd.formats[param]
            if sector in Navercmd.options[op]:
                return op
            return 2
        return 0

    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)

    @commands.group(name='네이버검색')
    async def _naversearch(self, ctx: commands.Context, sector, *args):
        sort = 'sim'
        if sector not in Navercmd.sectors:
            await ctx.send(embed=discord.Embed(title='❓ 존재하지 않는 검색 분야입니다: ' + sector, description='예) 네이버검색 뉴스 (검색어)', color=self.color['error']))
            return
        query = ' '.join(args)
        if args[-1].startswith('--'):
            sortexists = Navercmd.paramchecker(Navercmd.sectors[sector], args[-1])
            query = ' '.join(args[:-1])    
            if type(sortexists) == str:
                sort = sortexists
            elif sortexists == 0:
                query = ' '.join(args)
        print(query, ',', sort, Navercmd.sectors[sector])
        print(await naverapi.Search.search(self.openapi['naver']['clientID'], self.openapi['naver']['clientSec'], query, Navercmd.sectors[sector], sort=sort))
            

def setup(client):
    cog = Navercmd(client)
    client.add_cog(cog)