import discord
from discord.ext import commands
import datetime
import time
import math
import io

class Mastercmds(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = client.get_data('color')
        self.emj = client.get_data('emojictrl')
        self.msglog = client.get_data('msglog')
        self.errors = client.get_data('errors')

    @commands.command(name='eval')
    async def _eval(self, ctx: commands.Context, *, arg):
        try:
            rst = eval(arg)
        except Exception as ex:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{ex}```\n{self.emj.get("cross")} ERROR'
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n📤OUTPUT: ```python\n{rst}```\n{self.emj.get("check")} SUCCESS'
        embed=discord.Embed(title='**💬 EVAL**', color=self.color['salmon'], timestamp=datetime.datetime.utcnow(), description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='exec')
    async def _exec(self, ctx: commands.Context, *, arg):
        try:
            rst = exec(arg)
        except Exception as ex:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{ex}```\n{self.emj.get("cross")} ERROR'
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n📤OUTPUT: ```python\n{rst}```\n{self.emj.get("check")} SUCCESS'
        embed=discord.Embed(title='**💬 EXEC**', color=self.color['salmon'], timestamp=datetime.datetime.utcnow(), description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='await')
    async def _await(self, ctx: commands.Context, *, arg):
        try:
            rst = await eval(arg)
        except Exception as ex:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{ex}```\n{self.emj.get("cross")} ERROR'
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n📤OUTPUT: ```python\n{rst}```\n{self.emj.get("check")} SUCCESS'
        embed=discord.Embed(title='**💬 AWAIT**', color=self.color['salmon'], timestamp=datetime.datetime.utcnow(), description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='hawait')
    async def _hawait(self, ctx: commands.Context, *, arg):
        await eval(arg)

    @commands.command(name='noti')
    async def _noti(self, ctx: commands.Context, *, noti):
        cur = self.client.get_data('cur')
        cur.execute('select * from serverdata where noticechannel is not NULL')
        guild_dbs = cur.fetchall()
        guild_ids = list(map(lambda one: one['id'], guild_dbs))
        guilds = list(map(lambda one: self.client.get_guild(one), guild_ids))
        guilds = list(filter(bool, guilds))
        guild_ids = list(map(lambda one: one.id, guilds))

        start = time.time()
        embed = discord.Embed(title='📢 공지 전송', description=f'전체 `{len(self.client.guilds)}`개 서버 중 `{len(guilds)}`개 서버에 전송합니다.', color=self.color['salmon'])
        rst = {'suc': 0, 'exc': 0}
        logstr = ''
        embed.add_field(name='성공', value='0 서버')
        embed.add_field(name='실패', value='0 서버')
        notimsg = await ctx.send(embed=embed)
        for onedb in guild_dbs:
            guild = self.client.get_guild(onedb['id'])
            if not guild:
                rst['exc'] += 1
                logstr += f'서버를 찾을 수 없습니다: {onedb["id"]}\n'
                continue
            notich = guild.get_channel(onedb['noticechannel'])
            try:
                await notich.send(noti)
            except discord.errors.Forbidden:
                rst['exc'] += 1
                logstr += f'권한이 없습니다: {guild.id}({guild.name}) 서버의 {notich.id}({notich.name}) 채널.\n'
            else:
                rst['suc'] += 1
            finally:
                embed.set_field_at(0, name='성공', value=str(rst['suc']) + ' 서버')
                embed.set_field_at(1, name='실패', value=str(rst['exc']) + ' 서버')
                await notimsg.edit(embed=embed)
        end = time.time()
        alltime = math.trunc(end - start)
        embed = discord.Embed(title=f'{self.emj.get("check")} 공지 전송을 완료했습니다!', description='자세한 내용은 로그 파일을 참조하세요.', color=self.color['salmon'])
        logfile = discord.File(fp=io.StringIO(logstr), filename='notilog.log')
        await ctx.send(embed=embed)
        await ctx.send(file=logfile)


def setup(client):
    cog = Mastercmds(client)
    for cmd in cog.get_commands():
        cmd.add_check(client.get_data('check').master)
    client.add_cog(cog)