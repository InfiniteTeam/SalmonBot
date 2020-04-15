import discord
from discord.ext import commands
import datetime

class Salmoncmds(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = client.get_data('color')
        self.emj = client.get_data('emojictrl')
        self.msglog = client.get_data('msglog')
        self.errors = client.get_data('errors')

    @commands.command(name='help', aliases=['도움'])
    async def _help(self, ctx: commands.Context):
        embed = discord.Embed(title='📃 연어봇 전체 명령어', description='**[전체 명령어 보기](https://help.infiniteteam.me/salmonbot)**', color=self.color['salmon'])
        await ctx.send(embed=embed)

    @commands.command(name='info', aliases=['정보'])
    async def _info(self, ctx: commands.Context):
        await ctx.send(self.client.get_emoji(697041204793311252))

def setup(client):
    cog = Salmoncmds(client)
    for cmd in cog.get_commands():
        cmd.add_check(client.get_data('check').registered)
    client.add_cog(cog)