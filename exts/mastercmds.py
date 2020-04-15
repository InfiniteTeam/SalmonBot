import discord
from discord.ext import commands
import datetime

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

def setup(client):
    cog = Mastercmds(client)
    for cmd in cog.get_commands():
        cmd.add_check(client.get_data('check').master)
    client.add_cog(cog)