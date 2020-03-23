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
import paramiko
import re
import os
import sys
import urllib.request
import traceback
import websockets
from salmonext import naverapi, pagecontrol, salmoncmds, kakaoapi, mapgridcvt, datagokr

# =============== Local Data Load ===============
with open('./data/config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)
with open('./data/version.json', encoding='utf-8') as version_file:
    version = json.load(version_file)
with open('./data/color.json', encoding='utf-8') as color_file:
    color = json.load(color_file)

# IMPORTant data
if platform.system() == 'Windows':
    if config['betamode'] == False:
        with open('C:/salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
            token = token_file.readline()
    else:
        with open('C:/salmonbot/' + config['betatokenFileName'], encoding='utf-8') as token_file:
            token = token_file.readline()
    with open('C:/salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open('C:/salmonbot/' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
    with open('C:/salmonbot/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
        openapi = json.load(openapi_file)
elif platform.system() == 'Linux':
    if config['betamode'] == False:
        with open('/home/pi/salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
            token = token_file.readline()
    else:
        with open('/home/pi/salmonbot/' + config['betatokenFileName'], encoding='utf-8') as token_file:
            token = token_file.readline()
    with open('/home/pi/salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open('/home/pi/salmonbot/' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
    with open('/home/pi/salmonbot/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
        openapi = json.load(openapi_file)

# mkdir
if not os.path.exists('./logs'):
    os.makedirs('./logs')
if not os.path.exists('./logs/general'):
    os.makedirs('./logs/general')
if not os.path.exists('./logs/ping'):
    os.makedirs('./logs/ping')

botname = config['botName']
prefix = config['prefix']
activity = config['activity']
status = config['status']
boticon = config['botIconUrl']
thumbnail = config['thumbnailUrl']
for i in color.keys(): # convert HEX to DEC
    color[i] = int(color[i], 16)

versionNum = version['versionNum']
versionPrefix = version['versionPrefix']

seclist =[]
black = []
acnum = 0

starttime = datetime.datetime.now()
globalmsg = None

# =============== SSH connect ===============
sshclient = paramiko.SSHClient()
sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy)
sshclient.connect(ssh['host'], username=ssh['user'], password=ssh['password'], port=ssh['port'])

def sshcmd(cmd):
    stdin, stdout, stderr = sshclient.exec_command(cmd)
    lines = stdout.readlines()
    return ''.join(lines)

# =============== Database server connect ===============
db = pymysql.connect(
    host=dbac['host'],
    user=dbac['dbUser'],
    password=dbac['dbPassword'],
    db=dbac['dbName'],
    charset='utf8',
    autocommit=True
)
cur = db.cursor(pymysql.cursors.DictCursor)

# =============== NAVER Open API ===============
naverapi_id = openapi['naver']['clientID']
naverapi_secret = openapi['naver']['clientSec']

# ================ Kakao Open API ===============
kakaoapi_id = openapi['kakao']['clientID']
kakaoapi_secret = openapi['kakao']['clientSec']

# ================ data.go.kr Open API ===============
datagokr_key = openapi['data.go.kr']['ServiceKey']

# =============== Logging ===============
logger = logging.getLogger('salmonbot')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_streamh = logging.StreamHandler()
log_streamh.setFormatter(log_formatter)
logger.addHandler(log_streamh)
log_fileh = logging.handlers.RotatingFileHandler('./logs/general/salmon.log', maxBytes=config['maxlogbytes'], backupCount=10)
log_fileh.setFormatter(log_formatter)
logger.addHandler(log_fileh)

pinglogger = logging.getLogger('ping')
pinglogger.setLevel(logging.INFO)
ping_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ping_fileh = logging.handlers.RotatingFileHandler('./logs/ping/ping.log', maxBytes=config['maxlogbytes'], backupCount=10)
ping_fileh.setFormatter(ping_formatter)
pinglogger.addHandler(ping_fileh)

errlogger = logging.getLogger('error')
errlogger.setLevel(logging.DEBUG)
err_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
err_streamh = logging.StreamHandler()
err_streamh.setFormatter(err_formatter)
errlogger.addHandler(err_streamh)
err_fileh = logging.handlers.RotatingFileHandler('./logs/general/error.log', maxBytes=config['maxlogbytes'], backupCount=10)
err_fileh.setFormatter(err_formatter)
errlogger.addHandler(err_fileh)

logger.info('========== START ==========')
logger.info('Data Load Complete.')

# ================ Bot Command ===============
client = discord.Client(status=discord.Status.dnd, activity=discord.Game('연어봇 시작'))

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    if config['betamode'] == True:
        logger.warning(f'BETA MODE ENABLED.')
    secloop.start()
    dbrecon.start()
    activityLoop.start()
    #await client.change_presence(status=eval(f'discord.Status.{status}'), activity=discord.Game(activity)) # presence 를 설정 데이터 첫째로 적용합니다.

@tasks.loop(seconds=5)
async def secloop():
    global ping, pinglevel, seclist, dbping, temp, cpus, cpulist, mem
    try:
        ping = round(1000 * client.latency)
        if ping <= 100: pinglevel = '🔵 매우좋음'
        elif ping > 100 and ping <= 250: pinglevel = '🟢 양호함'
        elif ping > 250 and ping <= 400: pinglevel = '🟡 보통'
        elif ping > 400 and ping <= 550: pinglevel = '🔴 나쁨'
        elif ping > 550: pinglevel = '⚫ 매우나쁨'
        pinglogger.info(f'{ping}ms')
        pinglogger.info(f'DB_OPEN: {db.open}')
        pinglogger.info(f'CLIENT_CONNECTED: {not client.is_closed()}')
        dbip = config['dbIP']
        if config['localRun'] == True:
            dbping = '0'
        else:
            pingcmd = os.popen(f'ping -n 1 {dbip}').readlines()[-1]
            dbping = re.findall('\d+', pingcmd)[1]
        temp = sshcmd('vcgencmd measure_temp') # CPU 온도 불러옴 (RPi 전용)
        temp = temp[5:]
        cpus = sshcmd("mpstat -P ALL | tail -5 | awk '{print 100-$NF}'") # CPU별 사용량 불러옴
        cpulist = cpus.split('\n')[:-1]
        mem = sshcmd('free -m')
        if globalmsg != None:
            if not globalmsg.author.id in black:
                if seclist.count(spamuser) >= 5:
                    black.append(spamuser)
                    await globalmsg.channel.send(f'🤬 <@{spamuser}> 너님은 차단되었고 영원히 명령어를 쓸 수 없습니다. 사유: 명령어 도배')
                    msglog(globalmsg, '[차단됨. 사유: 명령어 도배]')
                seclist = []
    except Exception:
        traceback.print_exc()
        
@tasks.loop(seconds=2)
async def dbrecon():
    try:
        db.ping(reconnect=False)
    except Exception:
        traceback.print_exc()
        logger.warning('DB CONNECTION CLOSED. RECONNECTING...')
        db.ping(reconnect=True)
        logger.info('DB RECONNECT DONE.')

@tasks.loop(seconds=4)
async def activityLoop():
    global acnum
    try:
        aclist = [f'연어봇 - {prefix}도움 입력!', f'{len(client.users)}명의 사용자와 함께', f'{len(client.guilds)}개의 서버와 함께']
        await client.change_presence(status=eval(f'discord.Status.{status}'), activity=discord.Game(aclist[acnum]))
        if acnum >= len(aclist)-1: acnum = 0
        else: acnum += 1
    except Exception:
        traceback.print_exc()

@client.event
async def on_guild_join(guild):
    if cur.execute('select * from serverdata where id=%s', guild.id) == 0: # 서버 자동 등록 및 공지채널 자동 찾기.
        def search_noticechannel(): # 공지 및 봇 관련된 단어가 포함되어 있고 메시지 보내기 권한이 있는 채널을 찾음, 없으면 메시지 보내기 권한이 있는 맨 위 채널로 선택.
            noticechs = []
            freechannel = None
            for channel in guild.text_channels:
                if channel.permissions_for(guild.get_member(client.user.id)).send_messages:
                    freechannel = channel
                    if '공지' in channel.name and '봇' in channel.name:
                        noticechs.append(channel)
                        break
                    elif 'noti' in channel.name.lower() and 'bot' in channel.name.lower():
                        noticechs.append(channel)
                        break
                    elif '공지' in channel.name:
                        noticechs.append(channel)
                        break
                    elif 'noti' in channel.name.lower():
                        noticechs.append(channel)
                        break
                    elif '봇' in channel.name:
                        noticechs.append(channel)
                        break
                    elif 'bot' in channel.name.lower():
                        noticechs.append(channel)
                        break
            if noticechs == []:
                noticechs.append(freechannel)

            return noticechs[0]
        
        notich = search_noticechannel()
        cur.execute('insert into serverdata values (%s, %s)', (guild.id, notich.id))
        logger.info(f'새 서버: {guild.id}, 공지 채널: {notich.id}')
        if notich != None:
            await notich.send(f'안녕하세요! 연어봇을 서버에 초대해주셔서 감사합니다. `{prefix}도움`을 입력해 전체 명령어를 보실 수 있어요. 현재 채널이 공지 채널로 감지되었으며 `{prefix}공지채널` 명령으로 연어봇의 공지 채널을 변경할 수 있어요.')

@client.event
async def on_guild_remove(guild):
    if cur.execute('select * from serverdata where id=%s', guild.id) == 1:
        cur.execute('delete from serverdata where id=%s', guild.id)
        logger.info(f'서버에서 제거됨: {guild.id}')

@client.event
async def on_error(event, *args, **kwargs):
    ignoreexc = [discord.http.NotFound]
    excinfo = sys.exc_info()
    errstr = f'{"".join(traceback.format_tb(excinfo[2]))}{excinfo[0].__name__}: {excinfo[1]}'
    tb = traceback.format_tb(excinfo[2])
    if not excinfo[0] in ignoreexc:
        if 'Missing Permissions' in str(excinfo[1]):
            miniembed = discord.Embed(title='⛔ 권한 부족!', description=f'이 명령어의 동작에 필요한 연어봇의 권한이 부족합니다!\n`{prefix}봇권한 채널` 명령으로 연어봇의 권한을 확인할 수 있습니다.', color=color['error'])
            await args[0].channel.send(embed=miniembed)
            msglog(args[0], '[권한 부족!]')
        else:
            await args[0].channel.send(embed=errormsg(errstr, args[0]))
            if cur.execute('select * from userdata where id=%s and type=%s', (args[0].author.id, 'Master')) == 0:
                errlogger.error(errstr + '\n=========================')
            

@client.event
async def on_message(message):
    global spamuser, globalmsg, serverid_or_type
    if message.author == client.user:
        return
    if message.author.bot:
        return
    if message.author.id in black:
        return
    if message.content == prefix:
        return
    
    # 일반 사용자 커맨드.
    if message.content.startswith(prefix):
        # 서버인지 아닌지 확인
        if message.channel.type == discord.ChannelType.group or message.channel.type == discord.ChannelType.private:
            serverid_or_type = message.channel.type
        else:
            serverid_or_type = message.guild.id
            # 권한 확인
            myperms = message.channel.permissions_for(message.guild.get_member(client.user.id))

        if config['inspection'] == True:
            if cur.execute('select * from userdata where id=%s and type=%s', (message.author.id, 'Master')) == 0:
                await message.channel.send('현재 점검중이거나, 기능 추가 중입니다. 안정적인 봇 이용을 위해 잠시 기다려주세요.')
                return
        globalmsg = message
        spamuser = message.author.id
        seclist.append(spamuser)
        def checkmsg(m):
            return m.channel == message.channel and m.author == message.author
        userexist = cur.execute('select * from userdata where id=%s', message.author.id) # 유저 등록 여부
        # 등록 확인
        if userexist == 0:
            if message.content == prefix + '등록':
                embed = discord.Embed(title=f'{botname} 등록', description='**연어봇을 이용하기 위한 이용약관 및 개인정보 취급방침입니다. 동의하시면 20초 안에 `동의`를 입력해주세요.**', color=color['ask'], timestamp=datetime.datetime.utcnow())
                embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
                embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
                await message.channel.send(content=message.author.mention, embed=embed)
                msglog(message, '[등록: 이용약관 및 개인정보 취급방침의 동의]') 
                try:
                    msg = await client.wait_for('message', timeout=20.0, check=checkmsg)
                except asyncio.TimeoutError:
                    await message.channel.send('시간이 초과되었습니다.')
                    msglog(message, '[등록: 시간 초과]')
                else:
                    if msg.content == '동의':
                        if cur.execute('select * from userdata where id=%s', (msg.author.id)) == 0:
                            now = datetime.datetime.now()
                            if cur.execute('insert into userdata values (%s, %s, %s, %s)', (msg.author.id, 1, 'User', datetime.date(now.year, now.month, now.day))) == 1:
                                await message.channel.send(f'등록되었습니다. `{prefix}도움` 명령으로 전체 명령을 볼 수 있습니다.')
                                msglog(message, '[등록: 등록 완료]')
                        else:
                            await message.channel.send('이미 등록된 사용자입니다.')
                            msglog(message, '[등록: 이미 등록됨]')
                    else:
                        await message.channel.send('취소되었습니다. 정확히 `동의`를 입력해주세요!')
                        msglog(message, '[등록: 취소됨]')
            else:
                embed=discord.Embed(title='❔ 미등록 사용자', description=f'**등록되어 있지 않은 사용자입니다!**\n`{prefix}등록`명령을 입력해서, 약관에 동의해주세요.', color=color['error'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message, '[미등록 사용자]')

        elif userexist == 1: # 일반 사용자 명령어
            if message.content == prefix + '등록':
                await message.channel.send('이미 등록된 사용자입니다!')
                msglog(message, '[이미 등록된 사용자]')

            elif message.content == prefix + '탈퇴':
                embed = discord.Embed(title=f'{botname} 탈퇴',
                description='''**연어봇 이용약관 및 개인정보 취급방침 동의를 철회하고, 연어봇을 탈퇴하게 됩니다.**
                이 경우 _사용자님의 모든 데이터(개인정보 취급방침을 참조하십시오)_가 연어봇에서 삭제되며, __되돌릴 수 없습니다.__
                계속하시려면 `탈퇴`를 입력하십시오.''', color=color['warn'], timestamp=datetime.datetime.utcnow())
                embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
                embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
                await message.channel.send(content=message.author.mention, embed=embed)
                msglog(message, '[탈퇴: 사용자 탈퇴]')
                try:
                    msg = await client.wait_for('message', timeout=20.0, check=checkmsg)
                except asyncio.TimeoutError:
                    await message.channel.send('시간이 초과되었습니다.')
                    msglog(message, '[탈퇴: 시간 초과]')
                else:
                    if msg.content == '탈퇴':
                        if cur.execute('select * from userdata where id=%s', message.author.id) == 1:
                            cur.execute('delete from userdata where id=%s', message.author.id)
                            await message.channel.send('탈퇴되었으며 모든 사용자 데이터가 삭제되었습니다.')
                            msglog(msg, '[탈퇴: 완료]')
                        else:
                            await message.channel.send('오류! 이미 탈퇴된 사용자입니다.')
                            msglog(msg, '[탈퇴: 이미 탈퇴됨]')
                    else:
                        await message.channel.send('취소되었습니다. 정확히 `탈퇴`를 입력해주세요!')
                        msglog(message, '[탈퇴: 취소됨]')

            elif message.content == prefix + '도움':
                '''
                helpstr_salmonbot = f"""\
                    `{prefix}도움`: 전체 명령어를 확인합니다.
                    `{prefix}정보`: 봇 정보를 확인합니다.
                    `{prefix}핑`: 봇 지연시간을 확인합니다.
                    `{prefix}데이터서버`: 데이터서버의 CPU 점유율, 메모리 사용량 및 데이터베이스 연결 상태를 확인합니다.
                    `{prefix}봇권한 서버`: 현재 서버에서 {botname}이 가진 권한을 확인합니다.
                    `{prefix}봇권한 채널 [채널 멘션]`: 서버 채널에서 {botname}이 가진 권한을 확인합니다.
                    `{prefix}봇권한 채널목록`: 서버 채널에서 {botname}이 접근(읽기/쓰기/듣기/말하기)할 수 있는 채널 목록을 확인합니다.
                    `{prefix}공지채널`: 현재 채널을 {botname} 공지채널로 설정합니다.
                    """
                helpstr_naverapi = f"""\
                    `{prefix}네이버검색 (블로그/뉴스/책/백과사전/이미지) (검색어) [&&정확도순/&&최신순]`,
                    `{prefix}네이버검색 쇼핑 (검색어) [&&정확도순/&&최신순/&&가격높은순/&&가격낮은순]`,
                    `{prefix}네이버검색 (영화/웹문서/전문자료) (검색어)`:
                    ㅤ네이버 검색 API를 사용해 검색합니다.
                    ㅤ사용예: `네이버검색 백과사전 파이썬 &&최신순`
                    `{prefix}웹주소단축 (주소)`: 입력한 긴 웹주소를 짧게 단축합니다.
                    `{prefix}무슨언어 (텍스트)`: 네이버 파파고 언어 감지 기능으로 입력한 텍스트의 언어를 감지합니다.
                    """
                embed=discord.Embed(title='전체 명령어', description='**`(소괄호)`는 반드시 입력해야 하는 부분, `[대괄호]`는 입력하지 않아도 되는 부분입니다.**', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                embed.add_field(name='ㅤ\n연어봇', inline=False, value=helpstr_salmonbot)
                embed.add_field(name='네이버 오픈 API', inline=False, value=helpstr_naverapi)
                
                await message.channel.send(embed=embed)
                msglog(message, '[도움]')
                '''
                embed=discord.Embed(description='**[전체 명령어 보기](https://help.infiniteteam.me/salmonbot)**', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message, '[도움]')
            
            elif message.content == prefix + '정보':
                uptimenow = re.findall('\d+', str(datetime.datetime.now() - starttime))
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

                embed=discord.Embed(title='봇 정보', description=f'봇 이름: {botname}\n봇 버전: {versionPrefix}{versionNum}\n실행 시간: {uptimestr}', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.set_thumbnail(url=client.user.avatar_url)
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message, '[정보]')

            elif message.content == prefix + '핑':
                if config['localRun'] == True:
                    localrunstr = '_로컬 실행 상태_'
                else:
                    localrunstr = ''
                embed=discord.Embed(title='🏓 퐁!', description=f'**디스코드 지연시간: **{ping}ms - {pinglevel}\n**데이터서버 지연시간: **{dbping}ms\n{localrunstr}\n\n디스코드 지연시간은 디스코드 웹소켓 프로토콜의 지연 시간(latency)을 뜻합니다.', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message, '[핑]')

            elif message.content.startswith(prefix + '봇권한'):
                if type(serverid_or_type) == int:
                    if message.content == prefix + '봇권한 서버':
                        botperm_server = f"""\
                            초대 코드 만들기: `{myperms.create_instant_invite}`
                            사용자 추방: `{myperms.kick_members}`
                            사용자 차단: `{myperms.ban_members}`
                            관리자 권한: `{myperms.administrator}`
                            채널 관리: `{myperms.manage_channels}`
                            서버 관리: `{myperms.manage_guild}`
                            반응 추가: `{myperms.add_reactions}`
                            감사 로그 보기: `{myperms.view_audit_log}`
                            우선 발언권: `{myperms.priority_speaker}`
                            음성 채널에서 방송: `{myperms.stream}`
                            """
                        embed=discord.Embed(title='🔐 연어봇 권한 - 서버', description='현재 서버에서 연어봇이 가진 권한입니다.', color=color['info'], timestamp=datetime.datetime.utcnow())
                        embed.set_author(name=botname, icon_url=boticon)
                        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                        embed.add_field(name='ㅤ', value=botperm_server)
                        await message.channel.send(embed=embed)
                        msglog(message, '[봇권한: 서버]')

                    elif message.content == prefix + '봇권한 채널목록':
                        permchs = salmoncmds.accessibleChannelsMention(guild=message.guild, clientid=client.user.id)
                        embed=discord.Embed(title='🔐 연어봇 권한 - 채널 목록', description='현재 서버에서 연어봇이 접근(읽기/보내기/듣기/말하기) 할 수 있는 채널들의 목록입니다.', color=color['info'], timestamp=datetime.datetime.utcnow())
                        embed.set_author(name=botname, icon_url=boticon)
                        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                        if len(permchs[0]) > 0:
                            embed.add_field(name='채팅 채널', value='\n'.join(permchs[0]))
                        else:
                            embed.add_field(name='채팅 채널', value='접근할 수 있는 채널이 없어요.')
                        if len(permchs[1]) > 0:
                            embed.add_field(name='음성 채널', value='\n'.join(permchs[1]))
                        else:
                            embed.add_field(name='음성 채널', value='접근할 수 있는 채널이 없어요.')
                        await message.channel.send(embed=embed)
                        msglog(message, '[봇권한: 채널목록]')

                    elif message.content.startswith(prefix + '봇권한 채널'):
                        whpermch = message.channel
                        if len(message.channel_mentions) >= 1:
                            whpermch = message.channel_mentions[0]
                            myperms = message.channel_mentions[0].permissions_for(message.guild.get_member(client.user.id))
                        botperm_thischannel1 = f"""\
                            메시지 읽기: `{myperms.read_messages}`
                            메시지 보내기: `{myperms.send_messages}`
                            TTS 메시지 보내기: `{myperms.send_tts_messages}`
                            메시지 관리: `{myperms.manage_messages}`
                            파일 전송: `{myperms.attach_files}`
                            메시지 기록 보기: `{myperms.read_message_history}`
                            `@everyone` 멘션: `{myperms.mention_everyone}`
                            확장 이모지: `{myperms.external_emojis}`
                            길드 정보 보기: `{myperms.view_guild_insights}`
                            음성 채널 연결: `{myperms.connect}`
                            음성 채널에서 발언: `{myperms.speak}`
                            """
                        botperm_thischannel2 = f"""\
                            다른 멤버 마이크 음소거: `{myperms.mute_members}`
                            다른 멤버 헤드폰 음소거: `{myperms.deafen_members}`
                            다른 음성 채널로 멤버 옮기기: `{myperms.move_members}`
                            음성 감지 사용: `{myperms.use_voice_activation}`
                            내 닉네임 변경: `{myperms.change_nickname}`
                            다른 멤버 닉네임 변경: `{myperms.manage_nicknames}`
                            역할 관리: `{myperms.manage_roles}`
                            권한 관리: `{myperms.manage_permissions}`
                            웹훅 관리: `{myperms.manage_webhooks}`
                            이모지 관리: `{myperms.manage_emojis}`
                            """
                        embed=discord.Embed(title='🔐 연어봇 권한 - 채널', description=f'{whpermch.mention} 채널에서 연어봇이 가진 권한입니다.', color=color['info'], timestamp=datetime.datetime.utcnow())
                        embed.set_author(name=botname, icon_url=boticon)
                        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                        embed.add_field(name='ㅤ', value=botperm_thischannel1)
                        embed.add_field(name='ㅤ', value=botperm_thischannel2)
                        await message.channel.send(embed=embed)
                        msglog(message, '[봇권한: 채널]')

                    else:
                        await message.channel.send(embed=notexists())
                else:
                    await message.channel.send(embed=onlyguild())

            elif message.content == prefix + '데이터서버':
                dbalive = None
                try: db.ping(reconnect=False)
                except: dbalive = 'Closed'
                else: dbalive = 'Alive'
                
                memlist = re.findall('\d+', mem)
                memtotal, memused, memfree, membc, swaptotal, swapused, swapfree = memlist[0], memlist[1], memlist[2], memlist[4], memlist[6], memlist[7], memlist[8]
                memrealfree = str(int(memfree) + int(membc))
                membarusedpx = round((int(memused) / int(memtotal)) * 10)
                memusedpct = round((int(memused) / int(memtotal)) * 100)
                membar = '|' + '▩' * membarusedpx + 'ㅤ' * (10 - membarusedpx) + '|'
                swapbarusedpx = round((int(swapused) / int(swaptotal)) * 10)
                swapusedpct = round((int(swapused) / int(swaptotal)) * 100)
                swapbar = '|' + '▩' * swapbarusedpx + 'ㅤ' * (10 - swapbarusedpx) + '|'

                embed=discord.Embed(title='🖥 데이터서버 상태', description=f'데이터베이스 연결 열림: **{db.open}**\n데이터베이스 서버 상태: **{dbalive}**', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.add_field(name='CPU사용량', value=f'```  ALL: {cpulist[0]}%\nCPU 0: {cpulist[1]}%\nCPU 1: {cpulist[2]}%\nCPU 2: {cpulist[3]}%\nCPU 3: {cpulist[4]}%\nCPU 온도: {temp}```', inline=True)
                embed.add_field(name='메모리 사용량', value=f'메모리\n```{membar}\n {memused}M/{memtotal}M ({memusedpct}%)```스왑 메모리\n```{swapbar}\n {swapused}M/{swaptotal}M ({swapusedpct}%)```', inline=True)
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message, '[서버상태 데이터서버]')

            elif message.content == prefix + '공지채널':
                if message.channel.permissions_for(message.author).administrator:
                    cur.execute('select * from serverdata where id=%s', message.guild.id)
                    servernoticeid = cur.fetchall()[0]['noticechannel']
                    if servernoticeid == None:
                        embed=discord.Embed(title='📢 공지채널 설정', color=color['ask'], timestamp=datetime.datetime.utcnow(),
                        description=f'현재 {message.guild.name} 서버의 {botname} 공지 채널이 설정되어 있지 않습니다. 이 채널을 공지 채널로 설정할까요?')
                        embed.set_author(name=botname, icon_url=boticon)
                        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                    else:
                        embed=discord.Embed(title='📢 공지채널 설정', color=color['ask'], timestamp=datetime.datetime.utcnow(),
                        description=f'현재 {message.guild.name} 서버의 {botname} 공지 채널은 {client.get_channel(servernoticeid).mention} 으로 설정되어 있습니다.\n현재 채널을 공지 채널로 설정할까요?')
                        embed.set_author(name=botname, icon_url=boticon)
                        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                    noticeselect = await message.channel.send(content=message.author.mention, embed=embed)
                    for emoji in ['⭕', '❌']:
                        await noticeselect.add_reaction(emoji)
                    msglog(message, '[공지채널]')
                    def noticecheck(reaction, user):
                        return user == message.author and noticeselect.id == reaction.message.id and str(reaction.emoji) in ['⭕', '❌']
                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=20.0, check=noticecheck)
                    except asyncio.TimeoutError:
                        embed=discord.Embed(description=f'**⛔ 시간이 초과되었습니다.**', color=color['error'])
                        await message.channel.send(embed=embed)
                        msglog(message, '[공지채널: 시간 초과]')
                    else:
                        if reaction.emoji == '❌':
                            embed=discord.Embed(description=f'**❌ 취소되었습니다.**', color=color['error'])
                            await message.channel.send(embed=embed)
                            msglog(message, '[공지채널: 취소됨]')
                        elif reaction.emoji == '⭕':
                            cur.execute('update serverdata set noticechannel=%s where id=%s', (message.channel.id, message.guild.id))
                            embed=discord.Embed(description=f'**✅ {botname}의 현재 서버 공지 채널이{message.channel.mention} 으로 설정되었습니다!**', color=color['salmon'])
                            await message.channel.send(embed=embed)
                            msglog(message, '[공지채널: 설정됨]')

            # ==================== NAVER API ====================
            elif message.content.startswith(prefix + '네이버검색'):
                if type(serverid_or_type) == int:
                    def navercheck(reaction, user):
                        return user == message.author and naverresult.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                    searchstr = message.content
                    if message.content.startswith(prefix + '네이버검색 쇼핑'):
                        if searchstr[-8:] == ' &&가격높은순':
                            naversort = '가격 높은순'
                            naversortcode = 'dsc'
                            searchstr = searchstr[:-8]
                        elif searchstr[-8:] == ' &&가격낮은순':
                            naversort = '가격 낮은순'
                            naversortcode = 'asc'
                            searchstr = searchstr[:-8]
                        elif searchstr[-6:] == ' &&최신순':
                            naversort = '최신순'
                            naversortcode = 'date'
                            searchstr = searchstr[:-6]
                        else:
                            naversort = '정확도순'
                            naversortcode = 'sim'
                    else:
                        if searchstr[-6:] == ' &&최신순':
                            naversort = '최신순'
                            naversortcode = 'date'
                            searchstr = searchstr[:-6]
                        else:
                            naversort = '정확도순'
                            naversortcode = 'sim'
                    if searchstr.startswith(prefix + '네이버검색 블로그'):
                        cmdlen = 9
                        perpage = 4
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    naverblogsc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='blog', query=query, sort=naversortcode)
                                except Exception as ex:
                                    await globalmsg.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if naverblogsc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(naverblogsc) == int:
                                        await message.channel.send(f'오류! 코드: {naverblogsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif naverblogsc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if naverblogsc['total'] < perpage: naverblogallpage = 0
                                        else: 
                                            if naverblogsc['total'] > 100: naverblogallpage = (100-1)//perpage
                                            else: naverblogallpage = (naverblogsc['total']-1)//perpage
                                        naverblogembed = naverapi.blogEmbed(jsonresults=naverblogsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        naverblogembed.set_author(name=botname, icon_url=boticon)
                                        naverblogembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        naverblogresult = await message.channel.send(embed=naverblogembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await naverblogresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 블로그검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = naverblogresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await naverblogresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=naverblogresult, allpage=naverblogallpage, perpage=4, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        naverblogembed = naverapi.blogEmbed(jsonresults=naverblogsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        naverblogembed.set_author(name=botname, icon_url=boticon)
                                                        naverblogembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await naverblogresult.edit(embed=naverblogembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 블로그검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 뉴스'):
                        cmdlen = 8
                        perpage = 4
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    navernewssc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='news', query=query, sort=naversortcode)
                                except Exception as ex:
                                    await globalmsg.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if navernewssc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(navernewssc) == int:
                                        await message.channel.send(f'오류! 코드: {navernewssc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif navernewssc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if navernewssc['total'] < perpage: navernewsallpage = 0
                                        else: 
                                            if navernewssc['total'] > 100: navernewsallpage = (100-1)//perpage
                                            else: navernewsallpage = (navernewssc['total']-1)//perpage
                                        navernewsembed = naverapi.newsEmbed(jsonresults=navernewssc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        navernewsembed.set_author(name=botname, icon_url=boticon)
                                        navernewsembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        navernewsresult = await message.channel.send(embed=navernewsembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await navernewsresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 뉴스검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = navernewsresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await navernewsresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=navernewsresult, allpage=navernewsallpage, perpage=4, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        navernewsembed = naverapi.newsEmbed(jsonresults=navernewssc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        navernewsembed.set_author(name=botname, icon_url=boticon)
                                                        navernewsembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await navernewsresult.edit(embed=navernewsembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 뉴스검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 책'):
                        cmdlen = 7
                        perpage = 1
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    naverbooksc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='book', query=query, sort=naversortcode)
                                except Exception as ex:
                                    await globalmsg.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if naverbooksc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(naverbooksc) == int:
                                        await message.channel.send(f'오류! 코드: {naverbooksc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif naverbooksc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if naverbooksc['total'] < perpage: naverbookallpage = 0
                                        else: 
                                            if naverbooksc['total'] > 100: naverbookallpage = (100-1)//perpage
                                            else: naverbookallpage = (naverbooksc['total']-1)//perpage
                                        naverbookembed = naverapi.bookEmbed(jsonresults=naverbooksc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        naverbookembed.set_author(name=botname, icon_url=boticon)
                                        naverbookembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        naverbookresult = await message.channel.send(embed=naverbookembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await naverbookresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 책검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = naverbookresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await naverbookresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=naverbookresult, allpage=naverbookallpage, perpage=10, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        naverbookembed = naverapi.bookEmbed(jsonresults=naverbooksc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        naverbookembed.set_author(name=botname, icon_url=boticon)
                                                        naverbookembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await naverbookresult.edit(embed=naverbookembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 책검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 백과사전'):
                        cmdlen = 10
                        perpage = 1
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    naverencycsc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='encyc', query=query, sort=naversortcode)
                                except Exception as ex:
                                    await globalmsg.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if naverencycsc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(naverencycsc) == int:
                                        await message.channel.send(f'오류! 코드: {naverencycsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif naverencycsc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if naverencycsc['total'] < perpage: naverencycallpage = 0
                                        else: 
                                            if naverencycsc['total'] > 100: naverencycallpage = (100-1)//perpage
                                            else: naverencycallpage = (naverencycsc['total']-1)//perpage
                                        naverencycembed = naverapi.encycEmbed(jsonresults=naverencycsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        naverencycembed.set_author(name=botname, icon_url=boticon)
                                        naverencycembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        naverencycresult = await message.channel.send(embed=naverencycembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await naverencycresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 백과사전검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = naverencycresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await naverencycresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=naverencycresult, allpage=naverencycallpage, perpage=10, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        naverencycembed = naverapi.encycEmbed(jsonresults=naverencycsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        naverencycembed.set_author(name=botname, icon_url=boticon)
                                                        naverencycembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await naverencycresult.edit(embed=naverencycembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 백과사전검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 영화'):
                        cmdlen = 8
                        perpage = 1
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    navermoviesc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='movie', query=query, sort=naversortcode)
                                except Exception as ex:
                                    await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if navermoviesc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(navermoviesc) == int:
                                        await message.channel.send(f'오류! 코드: {navermoviesc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif navermoviesc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if navermoviesc['total'] < perpage: navermovieallpage = 0
                                        else: 
                                            if navermoviesc['total'] > 100: navermovieallpage = (100-1)//perpage
                                            else: navermovieallpage = (navermoviesc['total']-1)//perpage
                                        navermovieembed = naverapi.movieEmbed(jsonresults=navermoviesc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        navermovieembed.set_author(name=botname, icon_url=boticon)
                                        navermovieembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        navermovieresult = await message.channel.send(embed=navermovieembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await navermovieresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 영화검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = navermovieresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await navermovieresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=navermovieresult, allpage=navermovieallpage, perpage=10, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        navermovieembed = naverapi.movieEmbed(jsonresults=navermoviesc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        navermovieembed.set_author(name=botname, icon_url=boticon)
                                                        navermovieembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await navermovieresult.edit(embed=navermovieembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 영화검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 카페글'):
                        cmdlen = 9
                        perpage = 4
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    navercafesc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='cafearticle', query=query, sort=naversortcode)
                                except Exception as ex:
                                    await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if navercafesc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(navercafesc) == int:
                                        await message.channel.send(f'오류! 코드: {navercafesc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif navercafesc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if navercafesc['total'] < perpage: navercafeallpage = 0
                                        else: 
                                            if navercafesc['total'] > 100: navercafeallpage = (100-1)//perpage
                                            else: navercafeallpage = (navercafesc['total']-1)//perpage
                                        navercafeembed = naverapi.cafeEmbed(jsonresults=navercafesc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        navercafeembed.set_author(name=botname, icon_url=boticon)
                                        navercafeembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        navercaferesult = await message.channel.send(embed=navercafeembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await navercaferesult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 카페글검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = navercaferesult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await navercaferesult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=navercaferesult, allpage=navercafeallpage, perpage=4, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        navercafeembed = naverapi.cafeEmbed(jsonresults=navercafesc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        navercafeembed.set_author(name=botname, icon_url=boticon)
                                                        navercafeembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await navercaferesult.edit(embed=navercafeembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 카페글검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 지식인'):
                        cmdlen = 9
                        perpage = 4
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    naverkinsc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='kin', query=query, sort=naversortcode)
                                except Exception as ex:
                                    await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if naverkinsc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(naverkinsc) == int:
                                        await message.channel.send(f'오류! 코드: {naverkinsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif naverkinsc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if naverkinsc['total'] < perpage: naverkinallpage = 0
                                        else: 
                                            if naverkinsc['total'] > 100: naverkinallpage = (100-1)//perpage
                                            else: naverkinallpage = (naverkinsc['total']-1)//perpage
                                        naverkinembed = naverapi.kinEmbed(jsonresults=naverkinsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        naverkinembed.set_author(name=botname, icon_url=boticon)
                                        naverkinembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        naverkinresult = await message.channel.send(embed=naverkinembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await naverkinresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 지식iN검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = naverkinresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await naverkinresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=naverkinresult, allpage=naverkinallpage, perpage=4, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        naverkinembed = naverapi.kinEmbed(jsonresults=naverkinsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        naverkinembed.set_author(name=botname, icon_url=boticon)
                                                        naverkinembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await naverkinresult.edit(embed=naverkinembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 지식iN검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 웹문서'):
                        cmdlen = 9
                        perpage = 4
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    naverwebkrsc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='webkr', query=query, display=30, sort=naversortcode)
                                except Exception as ex:
                                    await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if naverwebkrsc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(naverwebkrsc) == int:
                                        await message.channel.send(f'오류! 코드: {naverwebkrsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif naverwebkrsc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if naverwebkrsc['total'] < perpage: naverwebkrallpage = 0
                                        else: 
                                            if naverwebkrsc['total'] > 30: naverwebkrallpage = (30-1)//perpage
                                            else: naverwebkrallpage = (naverwebkrsc['total']-1)//perpage
                                        naverwebkrembed = naverapi.webkrEmbed(jsonresults=naverwebkrsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        naverwebkrembed.set_author(name=botname, icon_url=boticon)
                                        naverwebkrembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        naverwebkrresult = await message.channel.send(embed=naverwebkrembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await naverwebkrresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 웹문서검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = naverwebkrresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await naverwebkrresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=naverwebkrresult, allpage=naverwebkrallpage, perpage=4, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        naverwebkrembed = naverapi.webkrEmbed(jsonresults=naverwebkrsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        naverwebkrembed.set_author(name=botname, icon_url=boticon)
                                                        naverwebkrembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await naverwebkrresult.edit(embed=naverwebkrembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 웹문서검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 이미지'):
                        cmdlen = 9
                        perpage = 1
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    naverimagesc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='image', query=query, display=100, sort=naversortcode)
                                except Exception as ex:
                                    await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if naverimagesc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(naverimagesc) == int:
                                        await message.channel.send(f'오류! 코드: {naverimagesc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif naverimagesc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if naverimagesc['total'] < perpage: naverimageallpage = 0
                                        else: 
                                            if naverimagesc['total'] > 100: naverimageallpage = (100-1)//perpage
                                            else: naverimageallpage = (naverimagesc['total']-1)//perpage
                                        naverimageembed = naverapi.imageEmbed(jsonresults=naverimagesc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        naverimageembed.set_author(name=botname, icon_url=boticon)
                                        naverimageembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        naverimageresult = await message.channel.send(embed=naverimageembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await naverimageresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 이미지검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = naverimageresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await naverimageresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=naverimageresult, allpage=naverimageallpage, perpage=10, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        naverimageembed = naverapi.imageEmbed(jsonresults=naverimagesc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        naverimageembed.set_author(name=botname, icon_url=boticon)
                                                        naverimageembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await naverimageresult.edit(embed=naverimageembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 이미지검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 쇼핑'):
                        cmdlen = 8
                        perpage = 1
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    navershopsc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='shop', query=query, display=100, sort=naversortcode)
                                except Exception as ex:
                                    await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if navershopsc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(navershopsc) == int:
                                        await message.channel.send(f'오류! 코드: {navershopsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif navershopsc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if navershopsc['total'] < perpage: navershopallpage = 0
                                        else: 
                                            if navershopsc['total'] > 100: navershopallpage = (100-1)//perpage
                                            else: navershopallpage = (navershopsc['total']-1)//perpage
                                        navershopembed = naverapi.shopEmbed(jsonresults=navershopsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        navershopembed.set_author(name=botname, icon_url=boticon)
                                        navershopembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        navershopresult = await message.channel.send(embed=navershopembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await navershopresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 쇼핑검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = navershopresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await navershopresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=navershopresult, allpage=navershopallpage, perpage=10, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        navershopembed = naverapi.shopEmbed(jsonresults=navershopsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        navershopembed.set_author(name=botname, icon_url=boticon)
                                                        navershopembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await navershopresult.edit(embed=navershopembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 쇼핑검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    elif searchstr.startswith(prefix + '네이버검색 전문자료'):
                        cmdlen = 10
                        perpage = 4
                        if searchstr[len(prefix)+1+cmdlen:]:
                            if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                                page = 0
                                query = searchstr[len(prefix)+1+cmdlen:]
                                try:
                                    naverdocsc = naverapi.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='doc', query=query, sort=naversortcode)
                                except Exception as ex:
                                    await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                                    await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                                else:
                                    if naverdocsc == 429:
                                        await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 횟수초과]')
                                    elif type(naverdocsc) == int:
                                        await message.channel.send(f'오류! 코드: {naverdocsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                        msglog(message, '[네이버검색: 오류]')
                                    elif naverdocsc['total'] == 0:
                                        await message.channel.send('검색 결과가 없습니다!')
                                    else:
                                        if naverdocsc['total'] < perpage: naverdocallpage = 0
                                        else: 
                                            if naverdocsc['total'] > 100: naverdocallpage = (100-1)//perpage
                                            else: naverdocallpage = (naverdocsc['total']-1)//perpage
                                        naverdocembed = naverapi.docEmbed(jsonresults=naverdocsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                        naverdocembed.set_author(name=botname, icon_url=boticon)
                                        naverdocembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                        naverdocresult = await message.channel.send(embed=naverdocembed)
                                        for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                            await naverdocresult.add_reaction(emoji)
                                        msglog(message, '[네이버검색: 전문자료검색]')
                                        while True:
                                            msglog(message, '[네이버검색: 반응 추가함]')
                                            naverresult = naverdocresult
                                            try:
                                                reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                            except asyncio.TimeoutError:
                                                await naverdocresult.clear_reactions()
                                                break
                                            else:
                                                pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=naverdocresult, allpage=naverdocallpage, perpage=4, nowpage=page)
                                                await pagect[1]
                                                if type(pagect[0]) == int:
                                                    if page != pagect[0]:
                                                        page = pagect[0]
                                                        naverdocembed = naverapi.docEmbed(jsonresults=naverdocsc, page=page, perpage=perpage, color=color['naverapi'], query=query, naversort=naversort)
                                                        naverdocembed.set_author(name=botname, icon_url=boticon)
                                                        naverdocembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                        await naverdocresult.edit(embed=naverdocembed)
                                                elif pagect[0] == None: break
                                                
                                    msglog(message, '[네이버검색: 전문자료검색 정지]')

                        else:
                            await message.channel.send('검색어를 입력해주세요.')
                            msglog(message, '[네이버검색: 검색어 없음]')

                    else: await message.channel.send(embed=notexists())
                
                else:
                    await message.channel.send(embed=onlyguild())

            elif message.content.startswith(prefix + '웹주소단축'):
                cmdlen = 5
                url = message.content[len(prefix)+1+cmdlen:]
                if url and message.content.startswith(prefix + '웹주소단축 '):
                    try:
                        shorturlresult = naverapi.shortUrl(clientid=naverapi_id, clientsecret=naverapi_secret, url=url)
                    except Exception as ex:
                        if str(ex) == 'HTTP Error 403: Forbidden':
                            await message.channel.send('올바르지 않은 주소이거나 이미 단축된 주소입니다.')
                        else:
                            await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                            await message.channel.send(f'입력한 주소에 문제가 없는지 확인해보세요.')
                    else:
                        if shorturlresult == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 주소 단축 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message, '[네이버주소단축: 횟수초과]')
                        elif type(shorturlresult) == int:
                            await message.channel.send(f'오류! 코드: {shorturlresult}\n주소 단축 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message, '[네이버주소단축: 오류]')
                        else:
                            shorturlembed = naverapi.shorturlEmbed(jsonresult=shorturlresult, color=color['naverapi'])
                            shorturlembed.set_author(name=botname, icon_url=boticon)
                            shorturlembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            await message.channel.send(embed=shorturlembed)
                            msglog(message, f"[네이버주소단축: {shorturlresult['result']['orgUrl']}]")
                else:
                    await message.channel.send('단축할 웹주소(URL)을 입력해 주세요.')
                    msglog(message, "[네이버주소단축: 주소없음]")

            elif message.content.startswith(prefix + '무슨언어'):
                cmdlen = 4
                query = message.content[len(prefix)+1+cmdlen:]
                if query and message.content.startswith(prefix + '무슨언어 '):
                    try:
                        detectlangsresult = naverapi.detectLangs(clientid=naverapi_id, clientsecret=naverapi_secret, query=query)
                    except Exception as ex:
                        await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', message))
                        await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                    else:
                        if detectlangsresult == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message, '[네이버언어감지: 횟수초과]')
                        elif type(detectlangsresult) == int:
                            await message.channel.send(f'오류! 코드: {detectlangsresult}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message, '[네이버언어감지: 오류]')
                        else:
                            detectlangsembed = naverapi.detectlangsEmbed(jsonresult=detectlangsresult, orgtext=query, color=color['naverapi'])
                            detectlangsembed.set_author(name=botname, icon_url=boticon)
                            detectlangsembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            shorturlmsg = await message.channel.send(embed=detectlangsembed)
                            msglog(message, f"[네이버언어감지: {detectlangsresult['langCode']}]")
                else:
                    miniembed = discord.Embed(description='**❌ 언어를 감지할 텍스트를 입력해주세요!**', color=color['error'])
                    await message.channel.send(embed=miniembed)
                    msglog(message, "[네이버언어감지: 텍스트없음]")

            # ==================== KAKAO API ====================
            elif message.content.startswith(prefix + '이미지태그'):
                msgurls = salmoncmds.urlExtract(message.content)
                if len(message.attachments):
                    fileurl = message.attachments[0].url
                    multitags = kakaoapi.multitag(kakaoapi_secret, image_url=fileurl)
                elif len(msgurls):
                    multitags = kakaoapi.multitag(kakaoapi_secret, image_url=msgurls[0])
                else:
                    multitags = False
                    miniembed = discord.Embed(description='**❌ 명령어에 사진 파일 또는 사진 웹주소(URL)가 포함되어 있지 않습니다!**', color=color['error'])
                    await message.channel.send(embed=miniembed)
                    msglog(message, '[이미지태그: 파일 없음]')
                if multitags != False:
                    if multitags:
                        stags = []
                        for onetag in multitags:
                            stags.append('#' + onetag)
                        tagsstr = '`, `'.join(stags)
                        embed = discord.Embed(title='🔲 이미지 태그 생성', description=f'생성된 태그:\n`{tagsstr}`', color=color['kakaoapi'])
                        embed.set_author(name=botname, icon_url=boticon)
                        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                        await message.channel.send(embed=embed)
                        msglog(message, '[이미지태그: 생성 완료]')
                    else:
                        await message.channel.send('생성된 태그가 없습니다!')
                        msglog(message, '[이미지태그: 태그 없음]')
            
            elif message.content.startswith(prefix + '문자감지'):
                if len(message.attachments):
                    async with message.channel.typing():
                        try:
                            textstarttime = time.time()
                            embed = discord.Embed(title='🔠 이미지 문자 감지 - (1/3단계)', description='\n**1단계: 사진 파일을 가져오고 있습니다...**', color=color['kakaoapi'])
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            textdrmsg = await message.channel.send(embed=embed)
                            textdr_file = await message.attachments[0].read()

                            embed = discord.Embed(title='🔠 이미지 문자 감지 - (2/3단계)', description='\n**2단계: 문자를 찾는 중입니다...**', color=color['kakaoapi'])
                            embed.set_thumbnail(url=message.attachments[0].url)
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            await textdrmsg.edit(embed=embed)
                            textdetect_results = kakaoapi.text_detect(kakaoapi_secret, textdr_file)

                            embed = discord.Embed(title='🔠 이미지 문자 감지 - (3/3단계)', description='\n**3단계: 문자를 변환 중입니다...**', color=color['kakaoapi'])
                            embed.set_thumbnail(url=message.attachments[0].url)
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            await textdrmsg.edit(embed=embed)
                            textrecog_results = kakaoapi.text_recognize(kakaoapi_secret, textdr_file, textdetect_results)

                            textendtime = time.time()
                        except Exception as ex:
                            if str(ex).startswith('400 Client Error'):
                                embed = discord.Embed(title='🔠 이미지 문자 감지', description='사진에서 문자가 감지되지 않았습니다!\n정상적인 이미지 파일인지 확인해보세요.', color=color['error'])
                                embed.set_author(name=botname, icon_url=boticon)
                                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                await textdrmsg.edit(embed=embed)
                                msglog(message, '[문자감지: 문자 감지 실패]')
                            else:
                                await message.channel.send(embed=errormsg(ex, message))
                        else:
                            timetotal = round(textendtime-textstarttime, 2)
                            recogtext = []
                            for onebox in textrecog_results:
                                if onebox != '':
                                    recogtext.append(onebox)
                            textdr_str = '`, `'.join(recogtext)
                            embed = discord.Embed(title='🔠 이미지 문자 감지 - 완료!', description=f'\n**문자 감지 결과({timetotal} 초):**\n\n`{textdr_str}`', color=color['kakaoapi'])
                            embed.set_thumbnail(url=message.attachments[0].url)
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            await textdrmsg.edit(embed=embed)
                            msglog(message, '[문자감지: 문자 감지 완료]')
                else:
                    miniembed = discord.Embed(description='**❌ 명령어에 사진 파일 또는 사진 웹주소(URL)가 포함되어 있지 않습니다!**', color=color['error'])
                    await message.channel.send(embed=miniembed)
                    msglog(message, '[문자감지: 파일 없음]')

            # ==================== data.go.kr ====================

            elif message.content.startswith(prefix + '주소검색'):
                if type(serverid_or_type) == int:
                    cmdlen = 4
                    query = message.content[len(prefix)+1+cmdlen:]
                    if query:
                        page = 0
                        perpage = 5
                        async with message.channel.typing():
                            addresses = datagokr.searchAddresses(datagokr_key, query, 1, 50)
                            header = datagokr.searchAddressesHeader(addresses)
                            total = header['totalCount']
                        if total == None or total == 0:
                            miniembed = discord.Embed(title='❌ 검색된 주소가 하나도 없습니다!', description='**예시를 참고해보세요! (예: 파호동 89, 호산로 125)**', color=color['error'])
                            await message.channel.send(embed=miniembed)
                            msglog(message, '[주소검색: 결과없음]')
                        else:
                            if total%perpage == 0:
                                allpage = total//perpage
                            else:
                                allpage = total//perpage + 1
                            embed = datagokr.searchAddressesEmbed(addresses, query, page, perpage, color['datagokr'])
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            addressmsg = await message.channel.send(embed=embed)
                            for rct in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await addressmsg.add_reaction(rct)
                            msglog(message, '[주소검색: 주소검색]')
                            while True:
                                def addresscheck(reaction, user):
                                    return user == message.author and addressmsg.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=addresscheck)
                                except asyncio.TimeoutError:
                                    await addressmsg.clear_reactions()
                                    break
                                else:
                                    if total < perpage: allpage = 0
                                    else: 
                                        if total > 50: allpage = (50-1)//perpage
                                        else: allpage = (total-1)//perpage
                                    pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=addressmsg, allpage=allpage, perpage=5, nowpage=page)
                                    await pagect[1]
                                    if type(pagect[0]) == int:
                                        msglog(message, '[주소검색: 반응 추가함]')
                                        if page != pagect[0]:
                                            page = pagect[0]
                                            embed = datagokr.searchAddressesEmbed(addresses, query, page, perpage, color['datagokr'])
                                            embed.set_author(name=botname, icon_url=boticon)
                                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                            await addressmsg.edit(embed=embed)
                                    elif pagect[0] == None: break
                            msglog(message, '[주소검색: 정지]')

                    else:
                        miniembed = discord.Embed(title='❌ 검색할 주소를 입력해주세요!', description='**(예: 파호동 89, 호산로 125)**', color=color['error'])
                        await message.channel.send(embed=miniembed)
                        msglog(message, '[주소검색: 주소입력]')
                else: 
                    await message.channel.send(embed=onlyguild())

            elif message.content.startswith(prefix + '마스크'):
                if serverid_or_type == int:
                    cmdlen = 3
                    addr = message.content[len(prefix)+1+cmdlen:]
                    notexistsmsg = '''**! 검색 양식을 확인해주세요 !**\n1. 반드시 `~~도` 또는 `~~광역시(특별시)`를 붙여야 합니다.\n2. 그 다음에는 반드시 `구/동/군/면/읍` 등을 입력하세요!\n(예: `대구광역시 달서구 파호동`, `경상북도 군위군 군위읍`)'''
                    if addr:
                        page = 0
                        perpage = 4
                        masks = datagokr.corona19Masks_byaddr(addr)
                        total = masks['count']
                        if total == None or total == 0:
                            # =============== Re-search ===============
                            llpage = 0
                            llperpage = 4
                            lladdr = kakaoapi.search_address(kakaoapi_secret, addr, 1, 1)
                            lladdrtotal = lladdr['meta']['total_count']
                            if lladdrtotal == None or lladdrtotal == 0:
                                miniembed = discord.Embed(title='❌ 검색된 판매처가 하나도 없습니다!', color=color['error'])
                                await message.channel.send(embed=miniembed)
                                msglog(message, '[마스크: 결과없음]')
                            else:
                                ll_lat = lladdr['documents'][0]['y']
                                ll_lng = lladdr['documents'][0]['x']
                                llmasks = datagokr.corona19Masks_bygeo(ll_lat, ll_lng)
                                llmaskstotal = llmasks['count']
                                if llmaskstotal == None or llmaskstotal == 0:
                                    miniembed = discord.Embed(title='❌ 검색된 판매처가 하나도 없습니다!', color=color['error'])
                                    await message.channel.send(embed=miniembed)
                                    msglog(message, '[마스크: 결과없음]')
                                else:
                                    lltotal = llmasks['count']
                                    if lltotal%llperpage == 0:
                                        llallpage = lltotal//llperpage
                                    else:
                                        llallpage = lltotal//llperpage + 1
                                    embed = datagokr.corona19Masks_Embed(llmasks, llpage, llperpage)
                                    embed.set_author(name=botname, icon_url=boticon)
                                    embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                    maskmsg = await message.channel.send(embed=embed)
                                    for rct in ['⏪', '◀', '⏹', '▶', '⏩']:
                                        await maskmsg.add_reaction(rct)
                                    msglog(message, '[마스크: 마스크]')
                                    while True:
                                        def maskcheck(reaction, user):
                                            return user == message.author and maskmsg.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                                        try:
                                            reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=maskcheck)
                                        except asyncio.TimeoutError:
                                            await maskmsg.clear_reactions()
                                            break
                                        else:
                                            if lltotal < llperpage: llallpage = 0
                                            else: 
                                                llallpage = (lltotal-1)//llperpage
                                            llpagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=maskmsg, allpage=llallpage, perpage=7, nowpage=llpage)
                                            await llpagect[1]
                                            if type(llpagect[0]) == int:
                                                msglog(message, '[마스크: 반응 추가함]')
                                                if llpage != llpagect[0]:
                                                    llpage = llpagect[0]
                                                    embed = datagokr.corona19Masks_Embed(llmasks, llpage, llperpage)
                                                    embed.set_author(name=botname, icon_url=boticon)
                                                    embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                    await maskmsg.edit(embed=embed)
                                            elif llpagect[0] == None: break
                                    msglog(message, '[마스크: 정지]')
                            # =============== Re-search END ===============
                        else:
                            if total%perpage == 0:
                                allpage = total//perpage
                            else:
                                allpage = total//perpage + 1
                            embed = datagokr.corona19Masks_Embed(masks, page, perpage)
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            maskmsg = await message.channel.send(embed=embed)
                            for rct in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await maskmsg.add_reaction(rct)
                            msglog(message, '[마스크: 마스크]')
                            while True:
                                def maskcheck(reaction, user):
                                    return user == message.author and maskmsg.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=maskcheck)
                                except asyncio.TimeoutError:
                                    await maskmsg.clear_reactions()
                                    break
                                else:
                                    if total < perpage: allpage = 0
                                    else: 
                                        allpage = (total-1)//perpage
                                    pagect = pagecontrol.naverPageControl(reaction=reaction, user=user, msg=maskmsg, allpage=allpage, perpage=7, nowpage=page)
                                    await pagect[1]
                                    if type(pagect[0]) == int:
                                        msglog(message, '[마스크: 반응 추가함]')
                                        if page != pagect[0]:
                                            page = pagect[0]
                                            embed = datagokr.corona19Masks_Embed(masks, page, perpage)
                                            embed.set_author(name=botname, icon_url=boticon)
                                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                            await maskmsg.edit(embed=embed)
                                    elif pagect[0] == None: break
                            msglog(message, '[마스크: 정지]')
                    else:
                        miniembed = discord.Embed(title='❌ 주변 판매처를 검색할 주소를 입력해주세요!', description=notexistsmsg, color=color['error'])
                        await message.channel.send(embed=miniembed)
                        msglog(message, '[마스크: 주소입력]')
                else: 
                    await message.channel.send(embed=onlyguild())

            # ==================== MASTER ONLY ====================
            elif message.content.startswith(prefix + '//'):
                if cur.execute('select * from serverdata where id=%s and master=%s', (message.guild.id, 1)) != 0:
                    if cur.execute('select * from userdata where id=%s and type=%s', (message.author.id, 'Master')) == 1:
                        if message.content == prefix + '//i t':
                            config['inspection'] = True
                            await message.channel.send('관리자 외 사용제한 켜짐.')
                        elif message.content == prefix + '//i f':
                            config['inspection'] = False
                            await message.channel.send('관리자 외 사용제한 꺼짐.')
                        elif message.content.startswith(prefix + '//exec'):
                            try:
                                exout = exec(message.content[len(prefix)+7:])
                            except Exception as ex:
                                execout = f'📥INPUT: ```python\n{message.content[len(prefix)+7:]}```\n💥EXCEPT: ```python\n{ex}```\n❌ ERROR'
                            else:
                                execout = f'📥INPUT: ```python\n{message.content[len(prefix)+7:]}```\n📤OUTPUT: ```python\n{exout}```\n✅ SUCCESS'
                            embed=discord.Embed(title='**💬 EXEC**', color=color['salmon'], timestamp=datetime.datetime.utcnow(), description=execout)
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            await message.channel.send(embed=embed)
                            msglog(message, f'[EXEC] {message.content[len(prefix)+7:]}')
                        elif message.content.startswith(prefix + '//eval'):
                            try:
                                evout = eval(message.content[len(prefix)+7:])
                            except Exception as ex:
                                evalout = f'📥INPUT: ```python\n{message.content[len(prefix)+7:]}```\n💥EXCEPT: ```python\n{ex}```\n❌ ERROR'
                            else:
                                evalout = f'📥INPUT: ```python\n{message.content[len(prefix)+7:]}```\n📤OUTPUT: ```python\n{evout}```\n✅ SUCCESS'
                            embed=discord.Embed(title='**💬 EVAL**', color=color['salmon'], timestamp=datetime.datetime.utcnow(), description=evalout)
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            await message.channel.send(embed=embed)
                            msglog(message, f'[EVAL] {message.content[len(prefix)+7:]}')
                        elif message.content.startswith(prefix + '//await'):
                            try:
                                awout = await eval(message.content[len(prefix)+8:])
                            except Exception as ex:
                                awaitout = f'📥INPUT: ```python\n{message.content[len(prefix)+8:]}```\n💥EXCEPT: ```python\n{ex}```\n❌ ERROR'
                            else:
                                awaitout = f'📥INPUT: ```python\n{message.content[len(prefix)+8:]}```\n📤OUTPUT: ```python\n{awout}```\n✅ SUCCESS'
                            embed=discord.Embed(title='**💬 AWAIT**', color=color['salmon'], timestamp=datetime.datetime.utcnow(), description=awaitout)
                            embed.set_author(name=botname, icon_url=boticon)
                            embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                            await message.channel.send(embed=embed)
                            msglog(message, f'[AWAIT] {message.content[len(prefix)+8:]}')
                        elif message.content.startswith(prefix + '//hawait'):
                            awout = await eval(message.content[len(prefix)+8:])
                            msglog(message, f'[AWAIT] {message.content[len(prefix)+8:]}')
                        elif message.content == prefix + '//restart --db':
                            sshcmd('sudo systemctl restart mysql')
                            await message.channel.send('DONE. Please restart the bot script.')
                        elif message.content == prefix + '//restart --dbsv':
                            sshcmd('sudo reboot')
                            await message.channel.send('REBOOTING. Please restart the bot script.')
                        elif message.content == prefix + '//restart --bot':
                            sshcmd('pm2 restart bot')
                        elif message.content == prefix + '//update --bot':
                            if config['betamode'] == True:
                                await message.channel.send("Cannot update bot on beta mode.")
                            else:
                                sshcmd('cd /home/pi/GitHub/SalmonBot && git pull')
                                await message.channel.send('DONE.')
                        elif message.content.startswith(prefix + '//noti '):
                            cmdlen = 8
                            print(cur.execute('select * from serverdata where noticechannel is not NULL'))
                            servers = cur.fetchall()
                            await message.channel.send(f'{len(servers)}개의 서버에 공지를 보냅니다.')
                            for notichannel in servers:
                                notiguild = client.get_guild(notichannel['id'])
                                if notiguild != None:
                                    notiguildchannel = notiguild.get_channel(notichannel['noticechannel'])
                                    if notiguildchannel.permissions_for(notiguild.get_member(client.user.id)).send_messages:
                                        await client.get_guild(notichannel['id']).get_channel(notichannel['noticechannel']).send(message.content[8:])
                            await message.channel.send('공지 전송 완료.')
                        elif message.content == prefix + '//error':
                            raise Exception('TEST')
                        elif message.content.startswith(prefix + '//logfile '):
                            cmdlen = 11
                            async with message.channel.typing():
                                if message.content[11:] == 'salmon':
                                    with open('./logs/general/salmon.log', 'rb') as logfile:
                                        dfile = discord.File(fp=logfile, filename='salmon.log')
                                elif message.content[11:] == 'ping':
                                    with open('./logs/ping/ping.log', 'rb') as logfile:
                                        dfile = discord.File(fp=logfile, filename='ping.log')
                                elif message.content[11:] == 'error':
                                    with open('./logs/general/error.log', 'rb') as logfile:
                                        dfile = discord.File(fp=logfile, filename='error.log')
                                await message.channel.send(file=dfile)

            elif message.content[len(prefix)] == '%': pass
            else: await message.channel.send(embed=notexists())
        else:
            await globalmsg.channel.send(embed=errormsg('DB.FOUND_DUPLICATE_USER', message))
            

# 메시지 로그 출력기 - 
# 함수 인자: message: 발신한 메시지 객체, fsent: 발신한 메시지 요약, fetc: 기타 기록
# 출력 형식: [날짜&시간] [ChannelType:] (채널 유형- DM/Group/서버아이디), [Author:] (수신자 아이디), [RCV:] (수신한 메시지 내용), [Sent:] (발신한 메시지 내용), [etc:] (기타 기록)
def msglog(message, fsent, fetc=None):
    if serverid_or_type == discord.ChannelType.group:
        logline = f'[ChannelType:] Group, [ChannelID:] {message.channel.id}, [Author:] {message.author.id}, [RCV]: {message.content}, [Sent]: {fsent}, [etc]: {fetc}'
    elif serverid_or_type == discord.ChannelType.private:
        logline = f'[ChannelType:] DM, [ChannelID:] {message.channel.id}, [Author:] {message.author.id}, [RCV]: {message.content}, [Sent]: {fsent}, [etc]: {fetc}'
    else:
        logline = f'[ServerID:] {serverid_or_type}, [ChannelID:] {message.channel.id}, [Author:] {message.author.id}, [RCV:] {message.content}, [Sent:] {fsent}, [etc:] {fetc}'
    logger.info(logline)

def errormsg(error, msg):
    embed=discord.Embed(title='**❌ 무언가 오류가 발생했습니다!**', description=f'오류가 기록되었습니다. 개발자가 오류 기록을 발견하면 처리하게 됩니다.\n오류 코드: ```{error}```', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=msg.author, icon_url=msg.author.avatar_url)
    msglog(msg, f'[오류] {error}')
    return embed

def onlyguild():
    embed=discord.Embed(title='**❌ 서버에서만 사용 가능한 명령입니다!**', description='DM이나 그룹 메시지에서는 사용할 수 없어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=globalmsg.author, icon_url=globalmsg.author.avatar_url)
    msglog(globalmsg, '[서버에서만 사용 가능한 명령어]')
    return embed

def notexists():
    embed=discord.Embed(title='**❌ 존재하지 않는 명령입니다!**', description=f'`{prefix}도움`을 입력해서 전체 명령어를 볼 수 있어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=globalmsg.author, icon_url=globalmsg.author.avatar_url)
    msglog(globalmsg, '[존재하지 않는 명령어]')
    return embed

client.run(token)