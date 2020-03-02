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
import urllib.request

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
    with open('/.salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('/.salmonbot/' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open('/.salmonbot/' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
    with open('/.salmonbot/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
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

def naverSearch(text, code, sort):
    encText = urllib.parse.quote(text)
    url = f"https://openapi.naver.com/v1/search/{code}?query={encText}&display=100&sort={sort}"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", naverapi_id)
    request.add_header("X-Naver-Client-Secret", naverapi_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if rescode == 200:
        results = json.load(response)
        return results
    else:
        return rescode

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
    tensecloop.start()
    await client.change_presence(status=eval(f'discord.Status.{status}'), activity=discord.Game(activity)) # presence 를 설정 데이터 첫째로 적용합니다.

@tasks.loop(seconds=5)
async def tensecloop():
    global ping, pinglevel, seclist, dbping, temp, cpus, cpulist, mem
    try:
        ping = round(1000 * client.latency)
        if ping <= 100: pinglevel = '🔵 매우좋음'
        elif ping > 100 and ping <= 250: pinglevel = '🟢 양호함'
        elif ping > 250 and ping <= 400: pinglevel = '🟡 보통'
        elif ping > 400 and ping <= 550: pinglevel = '🔴 나쁨'
        elif ping > 550: pinglevel = '⚫ 매우나쁨'
        pinglogger.info(f'{ping}ms')
        pinglogger.info(f'{db.open}')
        dbip = config['dbIP']
        pingcmd = os.popen(f'ping -n 1 {dbip}').readlines()[-1]
        dbping = re.findall('\d+', pingcmd)[1]
        temp = sshcmd('vcgencmd measure_temp') # CPU 온도 불러옴 (RPi 전용)
        temp = temp[5:]
        cpus = sshcmd("mpstat -P ALL | tail -5 | awk '{print 100-$NF}'") # CPU별 사용량 불러옴
        cpulist = cpus.split('\n')[:-1]
        mem = sshcmd('free -m')
        if not globalmsg.author.id in black:
            if seclist.count(spamuser) >= 5:
                black.append(spamuser)
                await globalmsg.channel.send(f'🤬 <@{spamuser}> 너님은 차단되었고 영원히 명령어를 쓸 수 없습니다. 사유: 명령어 도배')
                msglog(message.author.id, message.channel.id, message.content, '[차단됨. 사유: 명령어 도배]', fwhere_server=serverid_or_type)
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
                await message.channel.send(content=f'<@{message.author.id}>', embed=embed)
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
                for ch in message.guild.text_channels:
                    print()
                await message.channel.send('와!')
                msglog(message.author.id, message.channel.id, message.content, '[와 샌즈]', fwhere_server=serverid_or_type)

            elif message.content == prefix + '탈퇴':
                embed = discord.Embed(title=f'{botname} 탈퇴',
                description='''**연어봇 이용약관 및 개인정보 취급방침 동의를 철회하고, 연어봇을 탈퇴하게 됩니다.**
                이 경우 _사용자님의 모든 데이터(개인정보 취급방침을 참조하십시오)_가 연어봇에서 삭제되며, __되돌릴 수 없습니다.__
                계속하시려면 `탈퇴`를 입력하십시오.''', color=color['warn'], timestamp=datetime.datetime.utcnow())
                embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
                embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
                await message.channel.send(content=f'<@{message.author.id}>', embed=embed)
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

            elif message.content.startswith(prefix + '네이버검색'):
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
                        word = searchstr[len(prefix)+1+cmdlen:]
                        blogsc = naverSearch(word, 'blog', naversortcode)
                        if blogsc == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                        elif type(blogsc) == int:
                            await message.channel.send(f'오류! 코드: {blogsc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                        elif blogsc['total'] == 0:
                            await message.channel.send('검색 결과가 없습니다!')
                        else:
                            for linenum in range(len(blogsc['items'])):
                                for blogreplaces in [['`', '\`'], ['&quot;', '"'], ['&lsquo;', "'"], ['&rsquo;', "'"], ['<b>', '`'], ['</b>', '`']]:
                                    blogsc['items'][linenum]['title'] = blogsc['items'][linenum]['title'].replace(blogreplaces[0], blogreplaces[1])
                                    blogsc['items'][linenum]['description'] = blogsc['items'][linenum]['description'].replace(blogreplaces[0], blogreplaces[1])
                            def naverblogembed(pg, one):
                                embed=discord.Embed(title=f'🔍📝 네이버 블로그 검색 결과 - `{word}`', color=color['websearch'], timestamp=datetime.datetime.utcnow())
                                for af in range(one):
                                    if page*one+af+1 <= blogsc['total']:
                                        title = blogsc['items'][page*one+af]['title']
                                        link = blogsc['items'][page*one+af]['link']
                                        description = blogsc['items'][page*one+af]['description']
                                        if description == '':
                                            description = '(설명 없음)'
                                        bloggername = blogsc['items'][page*one+af]['bloggername']
                                        bloggerlink = blogsc['items'][page*one+af]['bloggerlink']
                                        postdate_year = int(blogsc['items'][page*one+af]['postdate'][0:4])
                                        postdate_month = int(blogsc['items'][page*one+af]['postdate'][4:6])
                                        postdate_day = int(blogsc['items'][page*one+af]['postdate'][6:8])
                                        postdate = f'{postdate_year}년 {postdate_month}월 {postdate_day}일'
                                        embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}\n- *[{bloggername}]({bloggerlink})* / **{postdate}**", inline=False)
                                    else:
                                        break
                                if blogsc['total'] > 100: max100 = ' 중 상위 100건'
                                else: max100 = ''
                                if blogsc['total'] < one: allpage = 0
                                else: 
                                    if max100: allpage = (100-1)//one
                                    else: allpage = (blogsc['total']-1)//one
                                builddateraw = blogsc['lastBuildDate']
                                builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
                                if builddate.strftime('%p') == 'AM':
                                    builddayweek = '오전'
                                elif builddate.strftime('%p') == 'PM':
                                    builddayweek = '오후'
                                buildhour12 = builddate.strftime('%I')
                                embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {blogsc['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
                                embed.set_author(name=botname, icon_url=boticon)
                                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                return embed
                            
                            if blogsc['total'] < 4: blogallpage = 0
                            else: 
                                if blogsc['total'] > 100: blogallpage = (100-1)//4
                                else: blogallpage = (blogsc['total']-1)//4

                            blogresult = await message.channel.send(embed=naverblogembed(page, 4))
                            for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await blogresult.add_reaction(emoji)
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 블로그검색]', fwhere_server=serverid_or_type)
                            def naverblogcheck(reaction, user):
                                return user == message.author and blogresult.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                            while True:
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=naverblogcheck)
                                except asyncio.TimeoutError:
                                    await blogresult.clear_reactions()
                                    break
                                else:
                                    if reaction.emoji == '⏹':
                                        await blogresult.clear_reactions()
                                        break
                                    if reaction.emoji == '▶':
                                        await blogresult.remove_reaction('▶', user)
                                        if page < blogallpage:
                                            page += 1
                                        else:
                                            continue
                                    if reaction.emoji == '◀':
                                        await blogresult.remove_reaction('◀', user)
                                        if page > 0: 
                                            page -= 1
                                        else:
                                            continue
                                    if reaction.emoji == '⏩':
                                        await blogresult.remove_reaction('⏩', user)
                                        if page < blogallpage-4:
                                            page += 4
                                        elif page == blogallpage:
                                            continue
                                        else:
                                            page = blogallpage
                                    if reaction.emoji == '⏪':
                                        await blogresult.remove_reaction('⏪', user)
                                        if page > 4:
                                            page -= 4
                                        elif page == 0:
                                            continue
                                        else:
                                            page = 0
                                    await blogresult.edit(embed=naverblogembed(page, 4))
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 블로그검색 정지]', fwhere_server=serverid_or_type)

                elif searchstr.startswith(prefix + '네이버검색 뉴스'):
                    cmdlen = 8
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        word = searchstr[len(prefix)+1+cmdlen:]
                        newssc = naverSearch(word, 'news', naversortcode)
                        if newssc == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                        elif type(newssc) == int:
                            await message.channel.send(f'오류! 코드: {newssc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                        elif newssc['total'] == 0:
                            await message.channel.send('검색 결과가 없습니다!')
                        else:
                            for linenum in range(len(newssc['items'])):
                                for newsreplaces in [['`', '\`'], ['&quot;', '"'], ['&lsquo;', "'"], ['&rsquo;', "'"], ['<b>', '`'], ['</b>', '`']]:
                                    newssc['items'][linenum]['title'] = newssc['items'][linenum]['title'].replace(newsreplaces[0], newsreplaces[1])
                                    newssc['items'][linenum]['description'] = newssc['items'][linenum]['description'].replace(newsreplaces[0], newsreplaces[1])
                            def navernewsembed(pg, one=4):
                                embed=discord.Embed(title=f'🔍📰 네이버 뉴스 검색 결과 - `{word}`', color=color['websearch'], timestamp=datetime.datetime.utcnow())
                                for af in range(one):
                                    if page*one+af+1 <= newssc['total']:
                                        title = newssc['items'][page*one+af]['title']
                                        originallink = newssc['items'][page*one+af]['link']
                                        description = newssc['items'][page*one+af]['description']
                                        if description == '':
                                            description = '(설명 없음)'
                                        pubdateraw = newssc['items'][page*one+af]['pubDate']
                                        pubdate = datetime.datetime.strptime(pubdateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
                                        if pubdate.strftime('%p') == 'AM':
                                            dayweek = '오전'
                                        elif pubdate.strftime('%p') == 'PM':
                                            dayweek = '오후'
                                        hour12 = pubdate.strftime('%I')
                                        pubdatetext = f'{pubdate.year}년 {pubdate.month}월 {pubdate.day}일 {dayweek} {hour12}시 {pubdate.minute}분'
                                        embed.add_field(name="ㅤ", value=f"**[{title}]({originallink})**\n{description}\n- **{pubdatetext}**", inline=False)
                                    else:
                                        break
                                if newssc['total'] > 100: max100 = ' 중 상위 100건'
                                else: max100 = ''
                                if newssc['total'] < one: allpage = 0
                                else: 
                                    if max100: allpage = (100-1)//one
                                    else: allpage = (newssc['total']-1)//one
                                builddateraw = newssc['lastBuildDate']
                                builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
                                if builddate.strftime('%p') == 'AM':
                                    builddayweek = '오전'
                                elif builddate.strftime('%p') == 'PM':
                                    builddayweek = '오후'
                                buildhour12 = builddate.strftime('%I')
                                embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {newssc['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
                                embed.set_author(name=botname, icon_url=boticon)
                                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                return embed
                            
                            if newssc['total'] < 4: newsallpage = 0
                            else: 
                                if newssc['total'] > 100: newsallpage = (100-1)//4
                                else: newsallpage = (newssc['total']-1)//4
                            
                            newsresult = await message.channel.send(embed=navernewsembed(page, 4))
                            for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await newsresult.add_reaction(emoji)
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 뉴스검색]', fwhere_server=serverid_or_type)
                            def navernewscheck(reaction, user):
                                return user == message.author and newsresult.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                            while True:
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navernewscheck)
                                except asyncio.TimeoutError:
                                    await newsresult.clear_reactions()
                                    break
                                else:
                                    if reaction.emoji == '⏹':
                                        await newsresult.clear_reactions()
                                        break
                                    if reaction.emoji == '▶':
                                        await newsresult.remove_reaction('▶', user)
                                        if page < newsallpage:
                                            page += 1
                                        else:
                                            continue
                                    if reaction.emoji == '◀':
                                        await newsresult.remove_reaction('◀', user)
                                        if page > 0: 
                                            page -= 1
                                        else:
                                            continue
                                    if reaction.emoji == '⏩':
                                        await newsresult.remove_reaction('⏩', user)
                                        if page < newsallpage-4:
                                            page += 4
                                        elif page == newsallpage:
                                            continue
                                        else:
                                            page = newsallpage
                                    if reaction.emoji == '⏪':
                                        await newsresult.remove_reaction('⏪', user)
                                        if page > 4:
                                            page -= 4
                                        elif page == 0:
                                            continue
                                        else:
                                            page = 0
                                    await newsresult.edit(embed=navernewsembed(page, 4))
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 뉴스검색 정지]', fwhere_server=serverid_or_type)

                elif searchstr.startswith(prefix + '네이버검색 책'):
                    cmdlen = 7
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        word = searchstr[len(prefix)+1+cmdlen:]
                        booksc = naverSearch(word, 'book', naversortcode)
                        if booksc == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                        elif type(booksc) == int:
                            await message.channel.send(f'오류! 코드: {booksc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                        elif booksc['total'] == 0:
                            await message.channel.send('검색 결과가 없습니다!')
                        else:
                            for linenum in range(len(booksc['items'])):
                                for bookreplaces in [['`', '\`'], ['&quot;', '"'], ['&lsquo;', "'"], ['&rsquo;', "'"], ['<b>', '`'], ['</b>', '`']]:
                                    booksc['items'][linenum]['title'] = booksc['items'][linenum]['title'].replace(bookreplaces[0], bookreplaces[1])
                                    booksc['items'][linenum]['description'] = booksc['items'][linenum]['description'].replace(bookreplaces[0], bookreplaces[1])
                                booksc['items'][linenum]['author'] = booksc['items'][linenum]['author'].replace('|', ', ')
                            def naverbookembed(pg, one=4):
                                embed=discord.Embed(title=f'🔍📗 네이버 책 검색 결과 - `{word}`', color=color['websearch'], timestamp=datetime.datetime.utcnow())
                                for af in range(one):
                                    if page*one+af+1 <= booksc['total']:
                                        title = booksc['items'][page*one+af]['title']
                                        link = booksc['items'][page*one+af]['link']
                                        author = booksc['items'][page*one+af]['author']
                                        price = booksc['items'][page*one+af]['price']
                                        discount = booksc['items'][page*one+af]['discount']
                                        publisher = booksc['items'][page*one+af]['publisher']
                                        description = booksc['items'][page*one+af]['description']
                                        if description == '':
                                            description = '(설명 없음)'
                                        pubdate_year = int(booksc['items'][page*one+af]['pubdate'][0:4])
                                        pubdate_month = int(booksc['items'][page*one+af]['pubdate'][4:6])
                                        pubdate_day = int(booksc['items'][page*one+af]['pubdate'][6:8])
                                        pubdate = f'{pubdate_year}년 {pubdate_month}월 {pubdate_day}일'
                                        isbn = booksc['items'][page*one+af]['isbn'].split(' ')[1]
                                        embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{author} 저 | {publisher} | {pubdate} | ISBN: {isbn}\n**{discount}원**~~`{price}원`~~\n\n{description}", inline=False)
                                    else:
                                        break
                                if booksc['total'] > 100: max100 = ' 중 상위 100건'
                                else: max100 = ''
                                if booksc['total'] < one: allpage = 0
                                else: 
                                    if max100: allpage = (100-1)//one
                                    else: allpage = (booksc['total']-1)//one
                                builddateraw = booksc['lastBuildDate']
                                builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
                                if builddate.strftime('%p') == 'AM':
                                    builddayweek = '오전'
                                elif builddate.strftime('%p') == 'PM':
                                    builddayweek = '오후'
                                buildhour12 = builddate.strftime('%I')
                                embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {booksc['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
                                embed.set_author(name=botname, icon_url=boticon)
                                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                return embed
                            
                            if booksc['total'] < 4: bookallpage = 0
                            else: 
                                if booksc['total'] > 100: bookallpage = (100-1)//4
                                else: bookallpage = (booksc['total']-1)//4
                            
                            bookresult = await message.channel.send(embed=naverbookembed(page, 4))
                            for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await bookresult.add_reaction(emoji)
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 책검색]', fwhere_server=serverid_or_type)
                            def naverbookcheck(reaction, user):
                                return user == message.author and bookresult.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                            while True:
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=naverbookcheck)
                                except asyncio.TimeoutError:
                                    await bookresult.clear_reactions()
                                    break
                                else:
                                    if reaction.emoji == '⏹':
                                        await bookresult.clear_reactions()
                                        break
                                    if reaction.emoji == '▶':
                                        await bookresult.remove_reaction('▶', user)
                                        if page < bookallpage:
                                            page += 1
                                        else:
                                            continue
                                    if reaction.emoji == '◀':
                                        await bookresult.remove_reaction('◀', user)
                                        if page > 0: 
                                            page -= 1
                                        else:
                                            continue
                                    if reaction.emoji == '⏩':
                                        await bookresult.remove_reaction('⏩', user)
                                        if page < bookallpage-4:
                                            page += 4
                                        elif page == bookallpage:
                                            continue
                                        else:
                                            page = bookallpage
                                    if reaction.emoji == '⏪':
                                        await bookresult.remove_reaction('⏪', user)
                                        if page > 4:
                                            page -= 4
                                        elif page == 0:
                                            continue
                                        else:
                                            page = 0
                                    await bookresult.edit(embed=naverbookembed(page, 4))
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 책검색 정지]', fwhere_server=serverid_or_type)

                elif searchstr.startswith(prefix + '네이버검색 백과사전'):
                    cmdlen = 10
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        word = searchstr[len(prefix)+1+cmdlen:]
                        encysc = naverSearch(word, 'encyc', naversortcode)
                        if encysc == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                        elif type(encysc) == int:
                            await message.channel.send(f'오류! 코드: {encysc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                        elif encysc['total'] == 0:
                            await message.channel.send('검색 결과가 없습니다!')
                        else:
                            for linenum in range(len(encysc['items'])):
                                for encyreplaces in [['`', '\`'], ['&quot;', '"'], ['&lsquo;', "'"], ['&rsquo;', "'"], ['<b>', '`'], ['</b>', '`']]:
                                    encysc['items'][linenum]['title'] = encysc['items'][linenum]['title'].replace(encyreplaces[0], encyreplaces[1])
                                    encysc['items'][linenum]['description'] = encysc['items'][linenum]['description'].replace(encyreplaces[0], encyreplaces[1])
                            def naverencyembed(pg, one=4):
                                embed=discord.Embed(title=f'🔍📚 네이버 백과사전 검색 결과 - `{word}`', color=color['websearch'], timestamp=datetime.datetime.utcnow())
                                for af in range(one):
                                    if page*one+af+1 <= encysc['total']:
                                        title = encysc['items'][page*one+af]['title']
                                        link = encysc['items'][page*one+af]['link']
                                        description = encysc['items'][page*one+af]['description']
                                        if description == '':
                                            description = '(설명 없음)'
                                        embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}", inline=False)
                                    else:
                                        break
                                if encysc['total'] > 100: max100 = ' 중 상위 100건'
                                else: max100 = ''
                                if encysc['total'] < one: allpage = 0
                                else: 
                                    if max100: allpage = (100-1)//one
                                    else: allpage = (encysc['total']-1)//one
                                builddateraw = encysc['lastBuildDate']
                                builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
                                if builddate.strftime('%p') == 'AM':
                                    builddayweek = '오전'
                                elif builddate.strftime('%p') == 'PM':
                                    builddayweek = '오후'
                                buildhour12 = builddate.strftime('%I')
                                embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {encysc['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
                                embed.set_author(name=botname, icon_url=boticon)
                                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                return embed
                            
                            if encysc['total'] < 4: encyallpage = 0
                            else: 
                                if encysc['total'] > 100: encyallpage = (100-1)//4
                                else: encyallpage = (encysc['total']-1)//4
                            
                            encyresult = await message.channel.send(embed=naverencyembed(page, 4))
                            for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await encyresult.add_reaction(emoji)
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 백과사전검색]', fwhere_server=serverid_or_type)
                            def naverencycheck(reaction, user):
                                return user == message.author and encyresult.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                            while True:
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=naverencycheck)
                                except asyncio.TimeoutError:
                                    await encyresult.clear_reactions()
                                    break
                                else:
                                    if reaction.emoji == '⏹':
                                        await encyresult.clear_reactions()
                                        break
                                    if reaction.emoji == '▶':
                                        await encyresult.remove_reaction('▶', user)
                                        if page < encyallpage:
                                            page += 1
                                        else:
                                            continue
                                    if reaction.emoji == '◀':
                                        await encyresult.remove_reaction('◀', user)
                                        if page > 0: 
                                            page -= 1
                                        else:
                                            continue
                                    if reaction.emoji == '⏩':
                                        await encyresult.remove_reaction('⏩', user)
                                        if page < encyallpage-4:
                                            page += 4
                                        elif page == encyallpage:
                                            continue
                                        else:
                                            page = encyallpage
                                    if reaction.emoji == '⏪':
                                        await encyresult.remove_reaction('⏪', user)
                                        if page > 4:
                                            page -= 4
                                        elif page == 0:
                                            continue
                                        else:
                                            page = 0
                                    await encyresult.edit(embed=naverencyembed(page, 4))
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 백과사전검색 정지]', fwhere_server=serverid_or_type)

                elif searchstr.startswith(prefix + '네이버검색 영화'):
                    cmdlen = 8
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        word = searchstr[len(prefix)+1+cmdlen:]
                        moviesc = naverSearch(word, 'movie', naversortcode)
                        if moviesc == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                        elif type(moviesc) == int:
                            await message.channel.send(f'오류! 코드: {moviesc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                        elif moviesc['total'] == 0:
                            await message.channel.send('검색 결과가 없습니다!')
                        else:
                            for linenum in range(len(moviesc['items'])):
                                for moviereplaces in [['`', '\`'], ['&quot;', '"'], ['&lsquo;', "'"], ['&rsquo;', "'"], ['<b>', '`'], ['</b>', '`']]:
                                    moviesc['items'][linenum]['title'] = moviesc['items'][linenum]['title'].replace(moviereplaces[0], moviereplaces[1])
                            def navermovieembed(pg, one=4):
                                embed=discord.Embed(title=f'🔍📰 네이버 영화 검색 결과 - `{word}`', color=color['websearch'], timestamp=datetime.datetime.utcnow())
                                for af in range(one):
                                    if page*one+af+1 <= moviesc['total']:
                                        title = moviesc['items'][page*one+af]['title']
                                        link = moviesc['items'][page*one+af]['link']
                                        subtitle = moviesc['items'][page*one+af]['subtitle']
                                        pubdate = moviesc['items'][page*one+af]['pubDate']
                                        director = moviesc['items'][page*one+af]['director'].replace('|', ', ')[:-2]
                                        actor = moviesc['items'][page*one+af]['actor'].replace('|', ', ')[:-2]
                                        userrating = moviesc['items'][page*one+af]['userRating']
                                        userratingbar = ('★' * round(float(userrating)/2)) + ('☆' * (5-round(float(userrating)/2)))

                                        embed.add_field(name="ㅤ", value=f"**[{title}]({link})** ({subtitle})\n`{userratingbar} {userrating}`\n감독: {director} | 출연: {actor} | {pubdate}", inline=False)
                                    else:
                                        break
                                if moviesc['total'] > 100: max100 = ' 중 상위 100건'
                                else: max100 = ''
                                if moviesc['total'] < one: allpage = 0
                                else: 
                                    if max100: allpage = (100-1)//one
                                    else: allpage = (moviesc['total']-1)//one
                                builddateraw = moviesc['lastBuildDate']
                                builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
                                if builddate.strftime('%p') == 'AM':
                                    builddayweek = '오전'
                                elif builddate.strftime('%p') == 'PM':
                                    builddayweek = '오후'
                                buildhour12 = builddate.strftime('%I')
                                embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {moviesc['total']}건{max100}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
                                embed.set_author(name=botname, icon_url=boticon)
                                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                return embed
                            
                            if moviesc['total'] < 4: movieallpage = 0
                            else: 
                                if moviesc['total'] > 100: movieallpage = (100-1)//4
                                else: movieallpage = (moviesc['total']-1)//4
                            
                            movieresult = await message.channel.send(embed=navermovieembed(page, 4))
                            for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await movieresult.add_reaction(emoji)
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 영화검색]', fwhere_server=serverid_or_type)
                            def navermoviecheck(reaction, user):
                                return user == message.author and movieresult.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                            while True:
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navermoviecheck)
                                except asyncio.TimeoutError:
                                    await movieresult.clear_reactions()
                                    break
                                else:
                                    if reaction.emoji == '⏹':
                                        await movieresult.clear_reactions()
                                        break
                                    if reaction.emoji == '▶':
                                        await movieresult.remove_reaction('▶', user)
                                        if page < movieallpage:
                                            page += 1
                                        else:
                                            continue
                                    if reaction.emoji == '◀':
                                        await movieresult.remove_reaction('◀', user)
                                        if page > 0: 
                                            page -= 1
                                        else:
                                            continue
                                    if reaction.emoji == '⏩':
                                        await movieresult.remove_reaction('⏩', user)
                                        if page < movieallpage-4:
                                            page += 4
                                        elif page == movieallpage:
                                            continue
                                        else:
                                            page = movieallpage
                                    if reaction.emoji == '⏪':
                                        await movieresult.remove_reaction('⏪', user)
                                        if page > 4:
                                            page -= 4
                                        elif page == 0:
                                            continue
                                        else:
                                            page = 0
                                    await movieresult.edit(embed=navermovieembed(page, 4))
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 영화검색 정지]', fwhere_server=serverid_or_type)

                if searchstr.startswith(prefix + '네이버검색 카페글'):
                    cmdlen = 9
                    if len(prefix + searchstr) >= len(prefix)+1+cmdlen and searchstr[1+cmdlen] == ' ':
                        page = 0
                        word = searchstr[len(prefix)+1+cmdlen:]
                        cafesc = naverSearch(word, 'cafearticle', naversortcode)
                        if cafesc == 429:
                            await message.channel.send('봇이 하루 사용 가능한 네이버 검색 횟수가 초과되었습니다! 내일 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 횟수초과]', fwhere_server=serverid_or_type)
                        elif type(cafesc) == int:
                            await message.channel.send(f'오류! 코드: {cafesc}\n검색 결과를 불러올 수 없습니다. 네이버 API의 일시적인 문제로 예상되며, 나중에 다시 시도해주세요.')
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 오류]', fwhere_server=serverid_or_type)
                        elif cafesc['total'] == 0:
                            await message.channel.send('검색 결과가 없습니다!')
                        else:
                            for linenum in range(len(cafesc['items'])):
                                for cafereplaces in [['`', '\`'], ['&quot;', '"'], ['&lsquo;', "'"], ['&rsquo;', "'"], ['<b>', '`'], ['</b>', '`']]:
                                    cafesc['items'][linenum]['title'] = cafesc['items'][linenum]['title'].replace(cafereplaces[0], cafereplaces[1])
                                    cafesc['items'][linenum]['description'] = cafesc['items'][linenum]['description'].replace(cafereplaces[0], cafereplaces[1])
                            def navercafeembed(pg, one):
                                embed=discord.Embed(title=f'🔍☕ 네이버 카페글 검색 결과 - `{word}`', color=color['websearch'], timestamp=datetime.datetime.utcnow())
                                for af in range(one):
                                    if page*one+af+1 <= cafesc['total']:
                                        title = cafesc['items'][page*one+af]['title']
                                        link = cafesc['items'][page*one+af]['link']
                                        description = cafesc['items'][page*one+af]['description']
                                        if description == '':
                                            description = '(설명 없음)'
                                        cafename = cafesc['items'][page*one+af]['cafename']
                                        cafeurl = cafesc['items'][page*one+af]['cafeurl']
                                        embed.add_field(name="ㅤ", value=f"**[{title}]({link})**\n{description}\n- *[{cafename}]({cafeurl})*", inline=False)
                                    else:
                                        break
                                if cafesc['total'] > 100: max100 = ' 중 상위 100건'
                                else: max100 = ''
                                if cafesc['total'] < one: allpage = 0
                                else: 
                                    if max100: allpage = (100-1)//one
                                    else: allpage = (cafesc['total']-1)//one
                                builddateraw = cafesc['lastBuildDate']
                                builddate = datetime.datetime.strptime(builddateraw.replace(' +0900', ''), '%a, %d %b %Y %X')
                                if builddate.strftime('%p') == 'AM':
                                    builddayweek = '오전'
                                elif builddate.strftime('%p') == 'PM':
                                    builddayweek = '오후'
                                buildhour12 = builddate.strftime('%I')
                                embed.add_field(name="ㅤ", value=f"```{page+1}/{allpage+1} 페이지, 총 {cafesc['total']}건{max100}, {naversort}\n{builddate.year}년 {builddate.month}월 {builddate.day}일 {builddayweek} {buildhour12}시 {builddate.minute}분 기준```", inline=False)
                                embed.set_author(name=botname, icon_url=boticon)
                                embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
                                return embed
                            
                            if cafesc['total'] < 4: cafeallpage = 0
                            else: 
                                if cafesc['total'] > 100: cafeallpage = (100-1)//4
                                else: cafeallpage = (cafesc['total']-1)//4

                            caferesult = await message.channel.send(embed=navercafeembed(page, 4))
                            for emoji in ['⏪', '◀', '⏹', '▶', '⏩']:
                                await caferesult.add_reaction(emoji)
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 카페글검색]', fwhere_server=serverid_or_type)
                            def navercafecheck(reaction, user):
                                return user == message.author and caferesult.id == reaction.message.id and str(reaction.emoji) in ['⏪', '◀', '⏹', '▶', '⏩']
                            while True:
                                msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 반응 추가함]', fwhere_server=serverid_or_type)
                                try:
                                    reaction, user = await client.wait_for('reaction_add', timeout=300.0, check=navercafecheck)
                                except asyncio.TimeoutError:
                                    await caferesult.clear_reactions()
                                    break
                                else:
                                    if reaction.emoji == '⏹':
                                        await caferesult.clear_reactions()
                                        break
                                    if reaction.emoji == '▶':
                                        await caferesult.remove_reaction('▶', user)
                                        if page < cafeallpage:
                                            page += 1
                                        else:
                                            continue
                                    if reaction.emoji == '◀':
                                        await caferesult.remove_reaction('◀', user)
                                        if page > 0: 
                                            page -= 1
                                        else:
                                            continue
                                    if reaction.emoji == '⏩':
                                        await caferesult.remove_reaction('⏩', user)
                                        if page < cafeallpage-4:
                                            page += 4
                                        elif page == cafeallpage:
                                            continue
                                        else:
                                            page = cafeallpage
                                    if reaction.emoji == '⏪':
                                        await caferesult.remove_reaction('⏪', user)
                                        if page > 4:
                                            page -= 4
                                        elif page == 0:
                                            continue
                                        else:
                                            page = 0
                                    await caferesult.edit(embed=navercafeembed(page, 4))
                                        
                            msglog(message.author.id, message.channel.id, message.content, '[네이버검색: 카페글검색 정지]', fwhere_server=serverid_or_type)

            elif message.content.startswith(prefix + '//'):
                if cur.execute('select * from userdata where id=%s and type=%s', (message.author.id, 'Master')) == 1:
                    if message.content == prefix + '//i t':
                        config['inspection'] = True
                        await message.channel.send('관리자 외 사용제한 켜짐.')
                        print(config['inspection'])
                    elif message.content == prefix + '//i f':
                        config['inspection'] = False
                        await message.channel.send('관리자 외 사용제한 꺼짐.')
                        print(config['inspection'])
                    elif message.content.startswith(prefix + '//exec'):
                        exec(message.content[len(prefix)+7:])
                    elif message.content.startswith(prefix + '//eval'):
                        eval(message.content[len(prefix)+7:])
                    elif message.content.startswith(prefix + '//await'):
                        await eval(message.content[len(prefix)+8:])
                    elif message.content == prefix + '//p':
                        print(message.channel.permissions_for(message.author).manage_guild)
                    elif message.content.startswith(prefix + '//noti '):
                        cmdlen = 8
                        print(cur.execute('select * from serverdata where noticechannel is not NULL'))
                        servers = cur.fetchall()
                        await message.channel.send(f'{len(servers)}개의 서버에 공지를 보냅니다.')
                        for notichannel in servers:
                            await client.get_guild(notichannel['id']).get_channel(notichannel['noticechannel']).send(message.content[8:])
                        await message.channel.send('공지 전송 완료.')

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

def errormsg(error, where='idk'):
    embed=discord.Embed(title='**❌ 무언가 오류가 발생했습니다!**', description='오류가 기록되었습니다. 시간이 되신다면, 오류 정보를 개발자에게 알려주시면 감사하겠습니다.\n오류 코드: ```{error}```', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=globalmsg.author, icon_url=globalmsg.author.avatar_url)
    msglog(globalmsg.author.id, globalmsg.channel.id, globalmsg.content, '[존재하지 않는 명령어입니다!]', fwhere_server=where)
    return embed

def onlyguild(where='idk'):
    embed=discord.Embed(title='**❌ 서버에서만 사용 가능한 명령입니다!**', description='DM이나 그룹 메시지에서는 사용할 수 없어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=globalmsg.author, icon_url=globalmsg.author.avatar_url)
    msglog(globalmsg.author.id, globalmsg.channel.id, globalmsg.content, '[서버에서만 사용 가능한 명령어]', fwhere_server=where)
    return embed

client.run(token)