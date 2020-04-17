import discord
from discord.ext import commands
import datetime
import re

class Salmoncmds(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = client.get_data('color')
        self.emj = client.get_data('emojictrl')
        self.msglog = client.get_data('msglog')
        self.errors = client.get_data('errors')

    @commands.command(name='help', aliases=['도움'])
    async def _help(self, ctx: commands.Context):
        embed = discord.Embed(title='📃 연어봇 전체 명령어', description='**현재 연어봇 리메이크중입니다! 일부 명령어가 동작하지 않을 수 있습니다.\n[전체 명령어 보기](https://help.infiniteteam.me/salmonbot)**', color=self.color['salmon'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[도움]')

    @commands.command(name='info', aliases=['정보'])
    async def _info(self, ctx: commands.Context):
        uptimenow = re.findall('\d+', str(datetime.datetime.now() - self.client.get_data('start')))
        uptimestr = ''
        if len(uptimenow) == 4:
            if int(uptimenow[0]) > 0:
                uptimestr += f'{int(uptimenow[0])}시간 '
            if int(uptimenow[1]) > 0:
                uptimestr += f'{int(uptimenow[1])}분 '
            if int(uptimenow[2]) > 0:
                uptimestr += f'{int(uptimenow[2])}초 '
        if len(uptimenow) == 5:
            if int(uptimenow[0]) > 0:
                uptimestr += f'{int(uptimenow[0])}일 '
            if int(uptimenow[1]) > 0:
                uptimestr += f'{int(uptimenow[1])}시간 '
            if int(uptimenow[2]) > 0:
                uptimestr += f'{int(uptimenow[2])}분 '
            if int(uptimenow[3]) > 0:
                uptimestr += f'{int(uptimenow[3])}초 '

        embed=discord.Embed(title='🏷 연어봇 정보', description=f'연어봇 버전: {self.client.get_data("version_str")}\n실행 시간: {uptimestr}', color=self.color['salmon'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[정보]')

    @commands.command(name='ping', aliases=['핑'])
    async def _ping(self, ctx: commands.Context):
        embed=discord.Embed(title='🏓 퐁!', description=f'**디스코드 지연시간: **{self.client.get_data("ping")[0]}ms - {self.client.get_data("ping")[1]}\n\n디스코드 지연시간은 디스코드 웹소켓 프로토콜의 지연 시간(latency)을 뜻합니다.', color=self.color['salmon'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[핑]')

def setup(client):
    cog = Salmoncmds(client)
    for cmd in cog.get_commands():
        cmd.add_check(client.get_data('check').registered)
    client.add_cog(cog)