import discord
from discord.ext import commands
import datetime
import re
import asyncio
from exts.utils.basecog import BaseCog

class Salmoncmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(client.get_data('check').registered)
            if cmd.name == 'notice':
                cmd.add_check(client.get_data('check').only_guild)

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

    @commands.command(name='shard-id', aliases=['샤드'])
    async def _shard_id(self, ctx: commands.Context):
        await ctx.send(embed=discord.Embed(description=f'**이 서버의 샤드 아이디는 `{ctx.guild.shard_id}`입니다.**', color=self.color['info']))

    @commands.command(name='notice', aliases=['공지채널'])
    @commands.has_guild_permissions(administrator=True)
    async def _notice(self, ctx: commands.Context, *mention):
        mention = ctx.message.channel_mentions
        if mention:
            notich = mention[0]
        else:
            notich = ctx.channel
        current_id = self.cur.execute('select * from serverdata where id=%s', ctx.guild.id)
        if current_id:
            ch = ctx.guild.get_channel(self.cur.fetchone()['noticechannel'])
            if notich == ctx.channel:
                await ctx.send(embed=discord.Embed(title=f'❓ 이미 이 채널이 공지채널로 설정되어 있습니다!', color=self.color['error']))
            elif ch:
                if mention:
                    embed = discord.Embed(title='📢 공지채널 설정', description=f'**현재 공지채널은 {ch.mention} 로 설정되어 있습니다.**\n{notich.mention} 을 공지채널로 설정할까요?\n20초 안에 선택해주세요.', color=self.color['ask'], timestamp=datetime.datetime.utcnow())
                else:
                    embed = discord.Embed(title='📢 공지채널 설정', description=f'**현재 공지채널은 {ch.mention} 로 설정되어 있습니다.**\n현재 채널을 공지채널로 설정할까요?\n20초 안에 선택해주세요.', color=self.color['ask'], timestamp=datetime.datetime.utcnow())
                msg = await ctx.send(embed=embed)
                for rct in ['⭕', '❌']:
                    await msg.add_reaction(rct)
                def notich_check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in ['⭕', '❌']
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=20, check=notich_check)
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
                else:
                    em = str(reaction.emoji)
                    if em == '⭕':
                        self.cur.execute('update serverdata set noticechannel=%s where id=%s', (notich.id, ctx.guild.id))
                        await ctx.send(embed=discord.Embed(title=f'{self.emj.get(ctx, "check")} 공지 채널을 성공적으로 설정했습니다!', description=f'이제 {notich.mention} 채널에 공지를 보냅니다.', color=self.color['info']))
                    elif em == '❌':
                        await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))

def setup(client):
    cog = Salmoncmds(client)
    client.add_cog(cog)