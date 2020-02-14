# -*-coding: utf-8-*-

import discord
from discord.ext import tasks
import asyncio
import json
import time
import platform
import datetime

# ========== config data import ==========
with open('./data/config.json', encoding='utf-8') as config_file:
        config = json.load(config_file)
with open('./data/version.json', encoding='utf-8') as version_file:
        version = json.load(version_file)
if platform.system() == 'Windows':
    with open(config['secureDirWin'] + config['tokenFileName']) as token_file:
        token = token_file.readline()
elif platform.system() == 'Linux':
    with open(config['secureDirLnx'] + config['tokenFileName']) as token_file:
        token = token_file.readline()

botname = config['botName']
prefix = config['prefix']
activity = config['activity']
status = config['status']
boticon = config['botIconUrl']
thumbnail = config['thumbnailUrl']
color = config['color']
for i in color.keys(): # convert HEX to DEC
    color[i] = int(color[i], 16)

versionNum = version['versionNum']
versionPrefix = version['versionPrefix']

# ========== prepair bot ==========
client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as{}'.format(client.user))
    await client.change_presence(status=eval('discord.Status.{}'.format(status)), activity=discord.Game(activity)) # presence 를 설정 데이터로 적용합니다. 

@client.event
async def on_message(message):
    if message.author.bot or message.author == client.user or message.content == '%': # 메시지 발신자가 다른 봇이거나 자기 자신인 경우, 접두사 뒤 명령어가 없는 경우 무시합니다.
        return
    else:
        if message.channel.type == discord.ChannelType.group or message.channel.type == discord.ChannelType.private: serverid_or_type = message.channel.type # 메시지를 수신한 곳이 서버인 경우 True, 아니면 False.
        else: serverid_or_type = message.guild.id

        if message.content == prefix + '도움':
            embed=discord.Embed(title="전체 명령어 목록", color=color['default'], timestamp=datetime.datetime.utcnow())
            embed.add_field(name='**연어봇**', value=f'**`{prefix}정보`**: {botname}의 버전, 개발자 정보 등 확인', inline=True)
            embed.set_author(name=botname, icon_url=boticon)
            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
            await message.channel.send(embed=embed)
            log(message.author.id, message.channel.id, message.content, '[도움]', fwhere_server=serverid_or_type)

        elif message.content == prefix + '정보':
            embed=discord.Embed(title="봇 정보", description=f'봇 이름: {botname}\n봇 버전: {versionPrefix}{versionNum}', color=color['default'], timestamp=datetime.datetime.utcnow())
            embed.set_thumbnail(url=thumbnail)
            embed.set_author(name=botname, icon_url=boticon)
            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
            await message.channel.send(embed=embed)
            log(message.author.id, message.channel.id, message.content, '[정보]', fwhere_server=serverid_or_type)

        elif message.content == prefix + '설정':


        elif message.content.startswith(prefix):
            embed=discord.Embed(title='**❌ 존재하지 않는 명령어입니다!**', description=f'`{prefix}도움`을 입력해서 전체 명령어를 볼 수 있어요.', color=color['default'], timestamp=datetime.datetime.utcnow())
            embed.set_author(name=botname, icon_url=boticon)
            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
            await message.channel.send(embed=embed)
            log(message.author.id, message.channel.id, message.content, '[존재하지 않는 명령어입니다!]', fwhere_server=serverid_or_type)

# 로그 출력기 - 
# 함수 인자: fwho: 수신자, fwhere_channel: 수신 채널 아이디, freceived: 수신한 메시지 내용, fsent: 발신한 메시지 요약, fetc: 기타 기록, fwhere_server: 수신 서버 아이디
# 출력 형식: [날짜&시간] [ChannelType:] (채널 유형- DM/Group/서버아이디), [Author:] (수신자 아이디), [RCV:] (수신한 메시지 내용), [Sent:] (발신한 메시지 내용), [etc:] (기타 기록)
def log(fwho, fwhere_channel, freceived, fsent, fetc=None, fwhere_server=None):
    now = datetime.datetime.today()
    fwhen = f'{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}:{now.microsecond}'
    if fwhere_server == discord.ChannelType.group:
        print(f'[{fwhen}] [ChannelType:] Group, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}')
    elif fwhere_server == discord.ChannelType.private:
        print(f'[{fwhen}] [ChannelType:] DM, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}')
    else:
        print(f'[{fwhen}] [ChannelType:] {fwhere_server}, [Author:] {fwho}, [RCV:] {freceived}, [Sent:] {fsent}, [etc:] {fetc}')

client.run(token)