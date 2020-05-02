import discord
from discord.ext import commands
from exts.utils.basecog import BaseCog
import asyncio
from exts.apis import naverapi
from exts.utils import pager

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
        distance = 5
        perpage = 4
        sort = 'sim'
        details = False
        if sector not in Navercmd.sectors:
            await ctx.send(embed=discord.Embed(title='❓ 존재하지 않는 검색 분야입니다: ' + sector, description='예) 네이버검색 뉴스 (검색어)', color=self.color['error']))
            return
        if not args:
            await ctx.send(embed=discord.Embed(title='❓ 검색어를 입력하세요!', description='예) 네이버검색 뉴스 (검색어)', color=self.color['error']))
            return
        params = []
        st = Navercmd.sectors[sector]
        for x in reversed(args):
            if x.startswith('--'):
                params.append(x)
            elif params:
                params.reverse()
                break
        if params:
            query = ' '.join(args[:args.index(params[0])])
            sortparams = list(set(params) & set(Navercmd.formats.keys()))
            if sortparams:
                sortexists = Navercmd.paramchecker(st, sortparams[-1])
                if type(sortexists) == str:
                    sort = sortexists
            if st in ['book'] and '--자세히' in params:
                details = True
                perpage = 1
                distance = 10
        else:
            query = ' '.join(args)
        
        print(query, sort, st, details, params, details)
        rst = await naverapi.Search.search(self.openapi['naver']['clientID'], self.openapi['naver']['clientSec'], query, st, sort=sort)
        if rst['total'] == 0:
            await ctx.send(embed=discord.Embed(title='❓ 검색 결과가 하나도 없습니다!', description='오타 또는 틀린 맞춤법이 있는지 확인해보세요.', color=self.color['error']))
            return
        pgr = pager.Pager(rst['items'], perpage=perpage)
        msg = await ctx.send(embed=naverapi.Search.embed(pgr.get_thispage(), rst, st, query, pgr.now_pagenum(), len(pgr.pages()), self.color['naverapi'], sort, details))
        emjs = ['⏪', '◀', '⏹', '▶', '⏩']
        rctts = [msg.add_reaction(emj) for emj in emjs]
        await asyncio.gather(*rctts)
        def check(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in emjs
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=60*5, check=check)
            except asyncio.TimeoutError:
                break
            else:
                ej = str(reaction.emoji)
                if ej == '⏹':
                    break
                elif ej == '◀':
                    pgr.prev()
                elif ej == '⏪':
                    pgr.minus(distance)
                elif ej == '▶':
                    pgr.next()
                elif ej == '⏩':
                    pgr.plus(distance)

            await asyncio.gather(
                msg.remove_reaction(reaction, user),
                msg.edit(embed=naverapi.Search.embed(pgr.get_thispage(), rst, st, query, pgr.now_pagenum(), len(pgr.pages()), self.color['naverapi'], sort, details))
                )
        await msg.clear_reactions()

def setup(client):
    cog = Navercmd(client)
    client.add_cog(cog)