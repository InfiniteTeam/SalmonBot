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
from salmonext import naver_search, pagecontrol, mastercommand

# =============== Local Data Load ===============
with open('./data/config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)
with open('./data/version.json', encoding='utf-8') as version_file:
    version = json.load(version_file)

# IMPORTant data
if platform.system() == 'Windows':
    with open('C:/salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('C:/salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open('C:/salmonbot/' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
    with open('C:/salmonbot/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
        openapi = json.load(openapi_file)
elif platform.system() == 'Linux':
    with open('/home/pi/salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('/home/pi/salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open('/home/pi/salmonbot/' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
    with open('/home/pi/salmonbot/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
        openapi = json.load(openapi_file)

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
acnum = 0

starttime = datetime.datetime.now()

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
    charset='utf8'
)
cur = db.cursor(pymysql.cursors.DictCursor)

# =============== NAVER Open API ===============
naverapi_id = openapi['naver']['clientID']
naverapi_secret = openapi['naver']['clientSec']

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

logger.info('========== START ==========')
logger.info('Data Load Complete.')

# ================ Bot Command ===============
client = discord.Client()

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    secloop.start()
    #await client.change_presence(status=eval(f'discord.Status.{status}'), activity=discord.Game(activity)) # presence 를 설정 데이터 첫째로 적용합니다.

@tasks.loop(seconds=5)
async def secloop():
    global ping, pinglevel, seclist, dbping, temp, cpus, cpulist, mem, acnum
    try:
        aclist = [f'연어봇 - {prefix}도움 입력!', f'{len(client.users)}명의 사용자와 함께']
        await client.change_presence(status=eval(f'discord.Status.{status}'), activity=discord.Game(aclist[acnum]))
        if acnum >= len(aclist)-1: acnum = 0
        else: acnum += 1
        ping = round(1000 * client.latency)
        if ping <= 100: pinglevel = '🔵 매우좋음'
        elif ping > 100 and ping <= 250: pinglevel = '🟢 양호함'
        elif ping > 250 and ping <= 400: pinglevel = '🟡 보통'
        elif ping > 400 and ping <= 550: pinglevel = '🔴 나쁨'
        elif ping > 550: pinglevel = '⚫ 매우나쁨'
        pinglogger.info(f'{ping}ms')
        pinglogger.info(f'{db.open}')
        dbip = config['dbIP']
        if config['localRun'] == True:
            dbping = '0 (로컬 실행, 봇서버=데이터서버)'
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
                    msglog(globalmsg.author.id, globalmsg.channel.id, globalmsg.content, '[차단됨. 사유: 명령어 도배]')
                seclist = []
    except Exception:
        traceback.print_exc()

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
    # 서버인지 아닌지 확인
    if message.channel.type == discord.ChannelType.group or message.channel.type == discord.ChannelType.private: serverid_or_type = message.channel.type
    else: serverid_or_type = message.guild.id
    # 권한 확인
    myperms = message.channel.permissions_for(message.guild.get_member(client.user.id))
    
    # 일반 사용자 커맨드.
    if message.content.startswith(prefix):
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
                msglog(message.author.id, message.channel.id, message.content, '[등록: 이용약관 및 개인정보 취급방침의 동의]', fwhere_server=serverid_or_type) 
                try:
                    msg = await client.wait_for('message', timeout=20.0, check=checkmsg)
                except asyncio.TimeoutError:
                    await message.channel.send('시간이 초과되었습니다.')
                    msglog(message.author.id, message.channel.id, message.content, '[등록: 시간 초과]', fwhere_server=serverid_or_type)
                else:
                    if msg.content == '동의':
                        if cur.execute('select * from userdata where id=%s', (msg.author.id)) == 0:
                            now = datetime.datetime.now()
                            if cur.execute('insert into userdata values (%s, %s, %s, %s)', (msg.author.id, 1, 'User', datetime.date(now.year, now.month, now.day))) == 1:
                                db.commit()
                                await message.channel.send(f'등록되었습니다. `{prefix}도움` 명령으로 전체 명령을 볼 수 있습니다.')
                                msglog(message.author.id, message.channel.id, message.content, '[등록: 등록 완료]', fwhere_server=serverid_or_type)
                        else:
                            await message.channel.send('이미 등록된 사용자입니다.')
                            msglog(message.author.id, message.channel.id, message.content, '[등록: 이미 등록됨]', fwhere_server=serverid_or_type)
                    else:
                        await message.channel.send('취소되었습니다. 정확히 `동의`를 입력해주세요!')
                        msglog(message.author.id, message.channel.id, message.content, '[등록: 취소됨]', fwhere_server=serverid_or_type)
            else:
                embed=discord.Embed(title='❔ 미등록 사용자', description=f'**등록되어 있지 않은 사용자입니다!**\n`{prefix}등록`명령을 입력해서, 약관에 동의해주세요.', color=color['error'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[미등록 사용자]', fwhere_server=serverid_or_type)

        elif userexist == 1: # 일반 사용자 명령어
            if cur.execute('select * from serverdata where id=%s', message.guild.id) == 0: # 서버 자동 등록 및 공지채널 자동 찾기.
                def search_noticechannel(): # 공지 및 봇 관련된 단어가 포함되어 있고 메시지 보내기 권한이 있는 채널을 찾음, 없으면 메시지 보내기 권한이 있는 맨 위 채널로 선택.
                    noticech = []
                    freechannel = None
                    for channel in message.guild.text_channels:
                        if channel.permissions_for(message.guild.get_member(client.user.id)).send_messages:
                            freechannel = channel
                            if '공지' in channel.name and '봇' in channel.name:
                                noticech.append(channel)
                                break
                            elif 'noti' in channel.name.lower() and 'bot' in channel.name.lower():
                                noticech.append(channel)
                                break
                            elif '공지' in channel.name:
                                noticech.append(channel)
                            elif 'noti' in channel.name.lower():
                                noticech.append(channel)
                            elif '봇' in channel.name:
                                noticech.append(channel)
                            elif 'bot' in channel.name.lower():
                                noticech.append(channel)
                    if noticech == []:
                        noticech.append(freechannel)

                    return noticech[0]
                    
                cur.execute('insert into serverdata values (%s, %s)', (message.guild.id, search_noticechannel().id))
                db.commit()
            if message.content == prefix + '등록':
                await message.channel.send('이미 등록된 사용자입니다!')
            elif message.content == prefix + '블랙':
                await message.channel.send(str(black))
            elif message.content == prefix + '샌즈':
                await message.guild.get_member(message.author.id).move_to(message.guild.get_channel(598454531600285706))
                msglog(message.author.id, message.channel.id, message.content, '[와 샌즈]', fwhere_server=serverid_or_type)

            elif message.content == prefix + '탈퇴':
                embed = discord.Embed(title=f'{botname} 탈퇴',
                description='''**연어봇 이용약관 및 개인정보 취급방침 동의를 철회하고, 연어봇을 탈퇴하게 됩니다.**
                이 경우 _사용자님의 모든 데이터(개인정보 취급방침을 참조하십시오)_가 연어봇에서 삭제되며, __되돌릴 수 없습니다.__
                계속하시려면 `탈퇴`를 입력하십시오.''', color=color['warn'], timestamp=datetime.datetime.utcnow())
                embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
                embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
                await message.channel.send(content=message.author.mention, embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[탈퇴: 사용자 탈퇴]', fwhere_server=serverid_or_type)
                try:
                    msg = await client.wait_for('message', timeout=20.0, check=checkmsg)
                except asyncio.TimeoutError:
                    await message.channel.send('시간이 초과되었습니다.')
                    msglog(message.author.id, message.channel.id, message.content, '[탈퇴: 시간 초과]', fwhere_server=serverid_or_type)
                else:
                    if msg.content == '탈퇴':
                        if cur.execute('select * from userdata where id=%s', message.author.id) == 1:
                            cur.execute('delete from userdata where id=%s', message.author.id)
                            db.commit()
                            await message.channel.send('탈퇴되었으며 모든 사용자 데이터가 삭제되었습니다.')
                            msglog(msg.author.id, msg.channel.id, msg.content, '[탈퇴: 완료]', fwhere_server=serverid_or_type)
                        else:
                            await message.channel.send('오류! 이미 탈퇴된 사용자입니다.')
                            msglog(msg.author.id, msg.channel.id, msg.content, '[탈퇴: 이미 탈퇴됨]', fwhere_server=serverid_or_type)
                    else:
                        await message.channel.send('취소되었습니다. 정확히 `탈퇴`를 입력해주세요!')

            elif message.content == prefix + '도움':
                helpstr_salmonbot = f"""\
                    `{prefix}도움`: 전체 명령어를 확인합니다.
                    `{prefix}정보`: 봇 정보를 확인합니다.
                    `{prefix}핑`: 봇 지연시간을 확인합니다.
                    `{prefix}서버상태 데이터서버`: 데이터서버의 CPU 점유율, 메모리 사용량 및 데이터베이스 연결 상태를 확인합니다.
                    """
                helpstr_naverapi = f"""\
                    `{prefix}네이버검색 (블로그/뉴스/책/백과사전) (검색어) [&&최신순/&&정확도순]`: 네이버 검색 API를 사용해 블로그, 뉴스 등을 최대 100건 까지 검색합니다.
                    `{prefix}네이버검색 (영화) (검색어)`: 네이버 검색 API를 사용해 영화 등을 최대 100건까지 검색합니다.
                     -사용예: `네이버검색 백과사전 파이썬 &&최신순`
                    """
                embed=discord.Embed(title='전체 명령어', description='**`(소괄호)`는 반드시 입력해야 하는 부분, `[대괄호]`는 입력하지 않아도 되는 부분입니다.**', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                embed.add_field(name='ㅤ\n연어봇', inline=False, value=helpstr_salmonbot)
                embed.add_field(name='네이버 오픈 API', inline=False, value=helpstr_naverapi)
                
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[정보]', fwhere_server=serverid_or_type)
            
            elif message.content == prefix + '정보':
                embed=discord.Embed(title='봇 정보', description=f'봇 이름: {botname}\n봇 버전: {versionPrefix}{versionNum}', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.set_thumbnail(url=thumbnail)
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[정보]', fwhere_server=serverid_or_type)

            elif message.content == prefix + '핑':
                embed=discord.Embed(title='🏓 퐁!', description=f'**디스코드 지연시간: **{ping}ms - {pinglevel}\n**데이터서버 지연시간: **{dbping}ms\n\n디스코드 지연시간은 디스코드 웹소켓 프로토콜의 지연 시간(latency)을 뜻합니다.', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[핑]', fwhere_server=serverid_or_type)

            elif message.content == prefix + '업타임':
                uptimenow = re.findall('\d+', str(datetime.datetime.now() - starttime))
                uptimestr = '봇 실행 시간: '
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
                embed=discord.Embed(title='⏱ 봇 실행 시간', description=uptimestr, color=color['salmon'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[핑]', fwhere_server=serverid_or_type)

            elif message.content == prefix + '봇권한':
                if type(serverid_or_type) == int:
                    botperm_section1 = f"""\
                        초대 만들기: `{myperms.create_instant_invite}`
                        사용자 추방: `{myperms.kick_members}`
                        사용자 차단: `{myperms.ban_members}`
                        관리자 권한: `{myperms.administrator}`
                        채널 관리: `{myperms.manage_channels}`
                        서버 관리: `{myperms.manage_guild}`
                        반응 추가: `{myperms.add_reactions}`
                        감사 로그 보기: `{myperms.view_audit_log}`
                        우선 발언권: `{myperms.priority_speaker}`
                        음성 채널에서 방송: `{myperms.stream}`
                        메시지 보기: `{myperms.read_messages}`
                        메시지 전송: `{myperms.send_messages}`
                        TTS 메시지 전송: `{myperms.send_tts_messages}`
                        메시지 관리: `{myperms.manage_messages}`
                        파일 전송: `{myperms.attach_files}`
                        
                        """
                    botperm_section2 = f"""\
                        메시지 기록 보기: `{myperms.read_message_history}`
                        `@everyone` 멘션: `{myperms.mention_everyone}`
                        확장 이모지: `{myperms.external_emojis}`
                        길드 정보 보기: `{myperms.view_guild_insights}`
                        음성 채널 연결: `{myperms.connect}`
                        음성 채널에서 발언: `{myperms.speak}`
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
                    embed=discord.Embed(title='🔐 연어봇 권한', description='현재 서버에서 연어봇이 가진 권한입니다.', color=color['salmon'], timestamp=datetime.datetime.utcnow())
                    embed.set_author(name=botname, icon_url=boticon)
                    embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                    embed.add_field(name='ㅤ', value=botperm_section1)
                    embed.add_field(name='ㅤ', value=botperm_section2)
                    await message.channel.send(embed=embed)
                    msglog(message.author.id, message.channel.id, message.content, '[봇권한]', fwhere_server=serverid_or_type)
                else:
                    await message.channel.send(embed=onlyguild(where=serverid_or_type))

            elif message.content == prefix + '서버상태 데이터서버':
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
                msglog(message.author.id, message.channel.id, message.content, '[서버상태 데이터서버]', fwhere_server=serverid_or_type)

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
                    msglog(message.author.id, message.channel.id, message.content, '[공지채널]', fwhere_server=serverid_or_type)
                    def noticecheck(reaction, user):
                        return user == message.author and noticeselect.id == reaction.message.id and str(reaction.emoji) in ['⭕', '❌']
                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=20.0, check=noticecheck)
                    except asyncio.TimeoutError:
                        embed=discord.Embed(description=f'**⛔ 시간이 초과되었습니다.**', color=color['error'])
                        await message.channel.send(embed=embed)
                        msglog(message.author.id, message.channel.id, message.content, '[공지채널: 시간 초과]', fwhere_server=serverid_or_type)
                    else:
                        if reaction.emoji == '❌':
                            embed=discord.Embed(description=f'**❌ 취소되었습니다.**', color=color['error'])
                            await message.channel.send(embed=embed)
                            msglog(message.author.id, message.channel.id, message.content, '[공지채널: 취소됨]', fwhere_server=serverid_or_type)
                        elif reaction.emoji == '⭕':
                            cur.execute('update serverdata set noticechannel=%s where id=%s', (message.channel.id, message.guild.id))
                            embed=discord.Embed(description=f'**✅ {botname}의 현재 서버 공지 채널이{message.channel.mention} 으로 설정되었습니다!**', color=color['salmon'])
                            await message.channel.send(embed=embed)
                            msglog(message.author.id, message.channel.id, message.content, '[공지채널: 설정됨]', fwhere_server=serverid_or_type)

            elif message.content.startswith(prefix + '네이버검색'):
                def navercheck(reaction, user):
                    return user == message.author and naverresult.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                searchstr = message.content
                if searchstr[-6:] == ' &&최신순':
                    naversort = '최신순'
                    naversortcode = 'date'
                    searchstr = searchstr[:-6]
                elif searchstr[-7:] == ' &&정확도순':
                    naversort = '정확도순'
                    naversortcode = 'sim'
                    searchstr = searchstr[:-7]
                else:
                    naversort = '정확도순'
                    naversortcode = 'sim'
                if searchstr.startswith(prefix + '네이버검색 블로그'):
                    cmdlen = 9
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        query = searchstr[len(prefix)+1+cmdlen:]
                        try:
                            naverblogsc = naver_search.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='blog', query=query, sort=naversortcode)
                        except Exception as ex:
                            await globalmsg.channel.send(embed=errormsg(f'EXCEPT: {ex}', serverid_or_type))
                            await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                        else:
                            if naverblogsc == 429:
                                await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                            elif type(naverblogsc) == int:
                                await message.channel.send(f'오류! 코드: {naverblogsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                            elif naverblogsc['total'] == 0:
                                await message.channel.send('검색 결과가 없습니다!')
                            else:
                                
                                if naverblogsc['total'] < 4: naverblogallpage = 0
                                else: 
                                    if naverblogsc['total'] > 100: naverblogallpage = (100-1)//4
                                    else: naverblogallpage = (naverblogsc['total']-1)//4
                                naverblogembed = naver_search.blogEmbed(jsonresults=naverblogsc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                naverblogembed.set_author(name=botname, icon_url=boticon)
                                naverblogembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                naverblogresult = await message.channel.send(embed=naverblogembed)
                                for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                    await naverblogresult.add_reaction(emoji)
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 블로그검색]', fwhere_server=serverid_or_type)
                                while True:
                                    msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                    naverresult = naverblogresult
                                    try:
                                        reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                    except asyncio.TimeoutError:
                                        await naverblogresult.clear_reactions()
                                        break
                                    else:
                                        pagect = pagecontrol.PageControl(reaction=reaction, user=user, msg=naverblogresult, allpage=naverblogallpage, perpage=4, nowpage=page)
                                        await pagect[1]
                                        if type(pagect[0]) == int:
                                            if page != pagect[0]:
                                                page = pagect[0]
                                                naverblogembed = naver_search.blogEmbed(jsonresults=naverblogsc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                                naverblogembed.set_author(name=botname, icon_url=boticon)
                                                naverblogembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                await naverblogresult.edit(embed=naverblogembed)
                                        elif pagect[0] == None: break
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 블로그검색 정지]', fwhere_server=serverid_or_type)

                elif searchstr.startswith(prefix + '네이버검색 뉴스'):
                    cmdlen = 8
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        query = searchstr[len(prefix)+1+cmdlen:]
                        try:
                            navernewssc = naver_search.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='news', query=query, sort=naversortcode)
                        except Exception as ex:
                            await globalmsg.channel.send(embed=errormsg(f'EXCEPT: {ex}', serverid_or_type))
                            await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                        else:
                            if navernewssc == 429:
                                await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                            elif type(navernewssc) == int:
                                await message.channel.send(f'오류! 코드: {navernewssc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                            elif navernewssc['total'] == 0:
                                await message.channel.send('검색 결과가 없습니다!')
                            else:
                                
                                if navernewssc['total'] < 4: navernewsallpage = 0
                                else: 
                                    if navernewssc['total'] > 100: navernewsallpage = (100-1)//4
                                    else: navernewsallpage = (navernewssc['total']-1)//4
                                navernewsembed = naver_search.newsEmbed(jsonresults=navernewssc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                navernewsembed.set_author(name=botname, icon_url=boticon)
                                navernewsembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                navernewsresult = await message.channel.send(embed=navernewsembed)
                                for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                    await navernewsresult.add_reaction(emoji)
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 뉴스검색]', fwhere_server=serverid_or_type)
                                while True:
                                    msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                    naverresult = navernewsresult
                                    try:
                                        reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                    except asyncio.TimeoutError:
                                        await navernewsresult.clear_reactions()
                                        break
                                    else:
                                        pagect = pagecontrol.PageControl(reaction=reaction, user=user, msg=navernewsresult, allpage=navernewsallpage, perpage=4, nowpage=page)
                                        await pagect[1]
                                        if type(pagect[0]) == int:
                                            if page != pagect[0]:
                                                page = pagect[0]
                                                navernewsembed = naver_search.newsEmbed(jsonresults=navernewssc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                                navernewsembed.set_author(name=botname, icon_url=boticon)
                                                navernewsembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                await navernewsresult.edit(embed=navernewsembed)
                                        elif pagect[0] == None: break
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 뉴스검색 정지]', fwhere_server=serverid_or_type)

                elif searchstr.startswith(prefix + '네이버검색 책'):
                    cmdlen = 7
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        query = searchstr[len(prefix)+1+cmdlen:]
                        try:
                            naverbooksc = naver_search.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='book', query=query, sort=naversortcode)
                        except Exception as ex:
                            await globalmsg.channel.send(embed=errormsg(f'EXCEPT: {ex}', serverid_or_type))
                            await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                        else:
                            if naverbooksc == 429:
                                await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                            elif type(naverbooksc) == int:
                                await message.channel.send(f'오류! 코드: {naverbooksc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                            elif naverbooksc['total'] == 0:
                                await message.channel.send('검색 결과가 없습니다!')
                            else:
                                
                                if naverbooksc['total'] < 4: naverbookallpage = 0
                                else: 
                                    if naverbooksc['total'] > 100: naverbookallpage = (100-1)//4
                                    else: naverbookallpage = (naverbooksc['total']-1)//4
                                naverbookembed = naver_search.bookEmbed(jsonresults=naverbooksc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                naverbookembed.set_author(name=botname, icon_url=boticon)
                                naverbookembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                naverbookresult = await message.channel.send(embed=naverbookembed)
                                for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                    await naverbookresult.add_reaction(emoji)
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 책검색]', fwhere_server=serverid_or_type)
                                while True:
                                    msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                    naverresult = naverbookresult
                                    try:
                                        reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                    except asyncio.TimeoutError:
                                        await naverbookresult.clear_reactions()
                                        break
                                    else:
                                        pagect = pagecontrol.PageControl(reaction=reaction, user=user, msg=naverbookresult, allpage=naverbookallpage, perpage=4, nowpage=page)
                                        await pagect[1]
                                        if type(pagect[0]) == int:
                                            if page != pagect[0]:
                                                page = pagect[0]
                                                naverbookembed = naver_search.bookEmbed(jsonresults=naverbooksc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                                naverbookembed.set_author(name=botname, icon_url=boticon)
                                                naverbookembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                await naverbookresult.edit(embed=naverbookembed)
                                        elif pagect[0] == None: break
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 책검색 정지]', fwhere_server=serverid_or_type)

                elif searchstr.startswith(prefix + '네이버검색 백과사전'):
                    cmdlen = 10
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        query = searchstr[len(prefix)+1+cmdlen:]
                        try:
                            naverencycsc = naver_search.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='encyc', query=query, sort=naversortcode)
                        except Exception as ex:
                            await globalmsg.channel.send(embed=errormsg(f'EXCEPT: {ex}', serverid_or_type))
                            await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                        else:
                            if naverencycsc == 429:
                                await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                            elif type(naverencycsc) == int:
                                await message.channel.send(f'오류! 코드: {naverencycsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                            elif naverencycsc['total'] == 0:
                                await message.channel.send('검색 결과가 없습니다!')
                            else:
                                
                                if naverencycsc['total'] < 4: naverencycallpage = 0
                                else: 
                                    if naverencycsc['total'] > 100: naverencycallpage = (100-1)//4
                                    else: naverencycallpage = (naverencycsc['total']-1)//4
                                naverencycembed = naver_search.encycEmbed(jsonresults=naverencycsc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                naverencycembed.set_author(name=botname, icon_url=boticon)
                                naverencycembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                naverencycresult = await message.channel.send(embed=naverencycembed)
                                for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                    await naverencycresult.add_reaction(emoji)
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 백과사전검색]', fwhere_server=serverid_or_type)
                                while True:
                                    msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                    naverresult = naverencycresult
                                    try:
                                        reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                    except asyncio.TimeoutError:
                                        await naverencycresult.clear_reactions()
                                        break
                                    else:
                                        pagect = pagecontrol.PageControl(reaction=reaction, user=user, msg=naverencycresult, allpage=naverencycallpage, perpage=4, nowpage=page)
                                        await pagect[1]
                                        if type(pagect[0]) == int:
                                            if page != pagect[0]:
                                                page = pagect[0]
                                                naverencycembed = naver_search.encycEmbed(jsonresults=naverencycsc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                                naverencycembed.set_author(name=botname, icon_url=boticon)
                                                naverencycembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                await naverencycresult.edit(embed=naverencycembed)
                                        elif pagect[0] == None: break
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 백과사전검색 정지]', fwhere_server=serverid_or_type)

                elif searchstr.startswith(prefix + '네이버검색 영화'):
                    cmdlen = 8
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        query = searchstr[len(prefix)+1+cmdlen:]
                        try:
                            navermoviesc = naver_search.naverSearch(id=naverapi_id, secret=naverapi_secret, sctype='movie', query=query, sort=naversortcode)
                        except Exception as ex:
                            await message.channel.send(embed=errormsg(f'EXCEPT: {ex}', serverid_or_type))
                            await message.channel.send(f'검색어에 문제가 없는지 확인해보세요.')
                        else:
                            if navermoviesc == 429:
                                await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                            elif type(navermoviesc) == int:
                                await message.channel.send(f'오류! 코드: {navermoviesc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                            elif navermoviesc['total'] == 0:
                                await message.channel.send('검색 결과가 없습니다!')
                            else:
                                
                                if navermoviesc['total'] < 4: navermovieallpage = 0
                                else: 
                                    if navermoviesc['total'] > 100: navermovieallpage = (100-1)//4
                                    else: navermovieallpage = (navermoviesc['total']-1)//4
                                navermovieembed = naver_search.movieEmbed(jsonresults=navermoviesc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                navermovieembed.set_author(name=botname, icon_url=boticon)
                                navermovieembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                navermovieresult = await message.channel.send(embed=navermovieembed)
                                for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                    await navermovieresult.add_reaction(emoji)
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 영화검색]', fwhere_server=serverid_or_type)
                                while True:
                                    msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                    naverresult = navermovieresult
                                    try:
                                        reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercheck)
                                    except asyncio.TimeoutError:
                                        await navermovieresult.clear_reactions()
                                        break
                                    else:
                                        pagect = pagecontrol.PageControl(reaction=reaction, user=user, msg=navermovieresult, allpage=navermovieallpage, perpage=4, nowpage=page)
                                        await pagect[1]
                                        if type(pagect[0]) == int:
                                            if page != pagect[0]:
                                                page = pagect[0]
                                                navermovieembed = naver_search.movieEmbed(jsonresults=navermoviesc, page=page, perpage=4, color=color['naversearch'], query=query, naversort=naversort)
                                                navermovieembed.set_author(name=botname, icon_url=boticon)
                                                navermovieembed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                                await navermovieresult.edit(embed=navermovieembed)
                                        elif pagect[0] == None: break
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 영화검색 정지]', fwhere_server=serverid_or_type)

            elif message.content.startswith(prefix + '//'):
                if cur.execute('select * from userdata where id=%s and type=%s', (message.author.id, 'Master')) == 1:
                    if message.content == prefix + '//i t':
                        config['inspection'] = True
                        await message.channel.send('관리자 외 사용제한 켜짐.')
                    elif message.content == prefix + '//i f':
                        config['inspection'] = False
                        await message.channel.send('관리자 외 사용제한 꺼짐.')
                    elif message.content.startswith(prefix + '//exec'):
                        try:
                            exout = eval(message.content[len(prefix)+7:])
                        except Exception as ex:
                            execout = f'📥INPUT: ```python\n{message.content[len(prefix)+7:]}```\n💥EXCEPT: ```python\n{ex}```\n❌ ERROR'
                        else:
                            execout = f'📥INPUT: ```python\n{message.content[len(prefix)+7:]}```\n📤OUTPUT: ```python\n{exout}```\n✅ SUCCESS'
                        embed=discord.Embed(title='**💬 EXEC**', color=color['salmon'], timestamp=datetime.datetime.utcnow(), description=execout)
                        embed.set_author(name=botname, icon_url=boticon)
                        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                        await message.channel.send(embed=embed)
                        msglog(message.author.id, message.channel.id, message.content, '[EXEC]', fwhere_server=serverid_or_type)
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
                        msglog(message.author.id, message.channel.id, message.content, '[EVAL]', fwhere_server=serverid_or_type)
                    elif message.content.startswith(prefix + '//await'):
                        await eval(message.content[len(prefix)+8:])
                    elif message.content == prefix + '//restart --db':
                        sshcmd('sudo systemctl restart mysql')
                        await message.channel.send('DONE')
                    elif message.content == prefix + '//restart --dbsv':
                        sshcmd('sudo reboot')
                        await message.channel.send('REBOOTING. Please restart the bot script')
                    elif message.content.startswith(prefix + '//noti '):
                        cmdlen = 8
                        print(cur.execute('select * from serverdata where noticechannel is not NULL'))
                        servers = cur.fetchall()
                        await message.channel.send(f'{len(servers)}개의 서버에 공지를 보냅니다.')
                        for notichannel in servers:
                            await client.get_guild(notichannel['id']).get_channel(notichannel['noticechannel']).send(message.content[8:])
                        await message.channel.send('공지 전송 완료.')
                    elif message.content == prefix + '//error':
                        await globalmsg.channel.send(embed=errormsg('TEST', serverid_or_type))

            elif message.content[len(prefix)] == '%': pass

            else:
                embed=discord.Embed(title='**❌ 존재하지 않는 명령입니다!**', description=f'`{prefix}도움`을 입력해서 전체 명령어를 볼 수 있어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
                embed.set_author(name=botname, icon_url=boticon)
                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                await message.channel.send(embed=embed)
                msglog(message.author.id, message.channel.id, message.content, '[존재하지 않는 명령어]', fwhere_server=serverid_or_type)
        
        else:
            await globalmsg.channel.send(embed=errormsg('DB.FOUND_DUPLICATE_USER', serverid_or_type))
            

# 메시지 로그 출력기 - 
# 함수 인자: fwho: 수신자, fwhere_channel: 수신 채널 아이디, freceived: 수신한 메시지 내용, fsent: 발신한 메시지 요약, fetc: 기타 기록, fwhere_server: 수신 서버 아이디
# 출력 형식: [날짜&시간] [ChannelType:] (채널 유형- DM/Group/서버아이디), [Author:] (수신자 아이디), [RCV:] (수신한 메시지 내용), [Sent:] (발신한 메시지 내용), [etc:] (기타 기록)
def msglog(fwho, fwhere_channel, freceived, fsent, fetc=None, fwhere_server=None):
    if fwhere_server == discord.ChannelType.group:
        logline = f'[ChannelType:] Group, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}'
    elif fwhere_server == discord.ChannelType.private:
        logline = f'[ChannelType:] DM, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}'
    else:
        logline = f'[ServerID:] {fwhere_server}, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV:] {freceived}, [Sent:] {fsent}, [etc:] {fetc}'
    logger.info(logline)

def errormsg(error, where='idk', why=''):
    embed=discord.Embed(title='**❌ 무언가 오류가 발생했습니다!**', description=f'오류가 기록되었습니다. 시간이 되신다면, 오류 정보를 개발자에게 알려주시면 감사하겠습니다.\n오류 코드: ```{error}```', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=globalmsg.author, icon_url=globalmsg.author.avatar_url)
    msglog(globalmsg.author.id, globalmsg.channel.id, globalmsg.content, f'[오류: {error}]', fwhere_server=where)
    return embed

def onlyguild(where='idk'):
    embed=discord.Embed(title='**❌ 서버에서만 사용 가능한 명령입니다!**', description='DM이나 그룹 메시지에서는 사용할 수 없어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=globalmsg.author, icon_url=globalmsg.author.avatar_url)
    msglog(globalmsg.author.id, globalmsg.channel.id, globalmsg.content, '[서버에서만 사용 가능한 명령어]', fwhere_server=where)
    return embed

client.run(token)