# -*-coding: utf-8-*-

import discord
from discord.ext import tasks, commands
import asyncio
import json
import time
import platform
import datetime
import pymysql
import logging
import logging.handlers

# =============== Local Data Load ===============
with open('./data/config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)
with open('./data/version.json', encoding='utf-8') as version_file:
    version = json.load(version_file)

if platform.system() == 'Windows': # IMPORTant data
    with open('C:/salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('C:/salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
elif platform.system() == 'Linux':
    with open('/.salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('/.salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)

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

seclist =[]
black = []

# =============== Database server connect ===============
db = pymysql.connect(
    host=dbac['host'],
    user=dbac['dbUser'],
    password=dbac['dbPassword'],
    db=dbac['dbName'],
    charset='utf8'
)
cur = db.cursor(pymysql.cursors.DictCursor)

# =============== Logging ===============
logger = logging.getLogger('salmonbot')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_streamh = logging.StreamHandler()
log_streamh.setFormatter(log_formatter)
logger.addHandler(log_streamh)
log_fileh = logging.handlers.RotatingFileHandler('./logs/ping/salmon.log', maxBytes=config['maxlogbytes'], backupCount=10)
log_fileh.setFormatter(log_formatter)
logger.addHandler(log_fileh)

pinglogger = logging.getLogger('ping')
pinglogger.setLevel(logging.INFO)
ping_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ping_fileh = logging.handlers.RotatingFileHandler('./logs/ping/ping.log', maxBytes=config['maxlogbytes'], backupCount=10)
ping_fileh.setFormatter(ping_formatter)
pinglogger.addHandler(ping_fileh)

logger.info('========== START ==========')

logger.info('Data Load Complete.')

# ================ Bot Command ===============
client = discord.Client()

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    tensecloop.start()
    await client.change_presence(status=eval(f'discord.Status.{status}'), activity=discord.Game(activity)) # presence 를 설정 데이터 첫째로 적용합니다.

@tasks.loop(seconds=5)
async def tensecloop():
    global ping, pinglevel, seclist
    try:
        ping = round(1000 * client.latency)
        if ping <= 100: pinglevel = '🔵 매우좋음'
        elif ping > 100 and ping <= 250: pinglevel = '🟢 양호함'
        elif ping > 250 and ping <= 400: pinglevel = '🟡 보통'
        elif ping > 400 and ping <= 550: pinglevel = '🔴 나쁨'
        elif ping > 550: pinglevel = '⚫ 매우나쁨'
        pinglogger.info(f'{ping}ms')
        if not str(globalmsg.author.id) in black:
            if seclist.count(spamuser) >= 5:
                black.append(spamuser)
                await globalmsg.channel.send(f'🤬 <@{spamuser}> 너님은 차단되었고 영원히 명령어를 쓸 수 없습니다. 사유: 명령어 도배')
            seclist = []
    except: pass

@client.event
async def on_message(message):
    global spamuser, globalmsg
    if message.author == client.user:
        return
    if message.author.bot:
        return
    if message.author.id in black:
        return
    if message.content == prefix:
        return
    if message.channel.type == discord.ChannelType.group or message.channel.type == discord.ChannelType.private: serverid_or_type = message.channel.type
    else: serverid_or_type = message.guild.id
    # 일반 사용자 커맨드.
    if message.content.startswith(prefix):
        globalmsg = message
        spamuser = str(message.author.id)
        seclist.append(spamuser)
        print(seclist)
        if message.content == prefix + '블랙':
            await message.channel.send(str(black))
        if message.content == prefix + '샌즈':
            await message.channel.send('와!')
        else:
            embed=discord.Embed(title='**❌ 존재하지 않는 명령입니다.!**', description=f'`{prefix}도움`을 입력해서 전체 명령어를 볼 수 있어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
            embed.set_author(name=botname, icon_url=boticon)
            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
            await message.channel.send(embed=embed)
            log(message.author.id, message.channel.id, message.content, '[존재하지 않는 명령어입니다!]', fwhere_server=serverid_or_type)

# 메시지 로그 출력기 - 
# 함수 인자: fwho: 수신자, fwhere_channel: 수신 채널 아이디, freceived: 수신한 메시지 내용, fsent: 발신한 메시지 요약, fetc: 기타 기록, fwhere_server: 수신 서버 아이디
# 출력 형식: [날짜&시간] [ChannelType:] (채널 유형- DM/Group/서버아이디), [Author:] (수신자 아이디), [RCV:] (수신한 메시지 내용), [Sent:] (발신한 메시지 내용), [etc:] (기타 기록)
def log(fwho, fwhere_channel, freceived, fsent, fetc=None, fwhere_server=None):
    if fwhere_server == discord.ChannelType.group:
        logline = f'[ChannelType:] Group, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}'
    elif fwhere_server == discord.ChannelType.private:
        logline = f'[ChannelType:] DM, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}'
    else:
        logline = f'[ServerID:] {fwhere_server}, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV:] {freceived}, [Sent:] {fsent}, [etc:] {fetc}'
    logger.info(logline)

client.run(token)