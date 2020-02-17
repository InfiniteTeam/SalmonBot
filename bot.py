# -*-coding: utf-8-*-

import discord
from discord.ext import tasks, commands
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
if platform.system() == 'Windows': # 시스템 종류에 맞게 중요 데이터 불러옵니다.
    with open('C:/salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('C:/salmonbot/' + config['userdataFileName'], encoding='utf-8') as userdata_file:
        userdata = json.load(userdata_file)
    with open('C:/salmonbot/' + config['serverdataFileName'], encoding='utf-8') as serverdata_file:
        serverdata = json.load(serverdata_file)
elif platform.system() == 'Linux':
    with open('/.salmonbot/' + config['tokenFileName'], encoding='utf-8') as token_file:
        token = token_file.readline()
    with open('/.salmonbot/' + config['userdataFileName'], encoding='utf-8') as userdata_file:
        userdata = json.load(userdata_file)
    with open('/.salmonbot/' + config['serverdataFileName'], encoding='utf-8') as serverdata_file:
        serverdata = json.load(serverdata_file)

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
    latency.start()
    await client.change_presence(status=eval(f'discord.Status.{status}'), activity=discord.Game(activity)) # presence 를 설정 데이터 첫째로 적용합니다. 

@tasks.loop(seconds=30)
async def latency():
    global ping, pinglevel
    ping = round(1000 * client.latency)
    if ping <= 100: pinglevel = '🔵 매우좋음'
    elif ping > 100 and ping <= 250: pinglevel = '🟢 양호함'
    elif ping > 250 and ping <= 400: pinglevel = '🟡 보통'
    elif ping > 400 and ping <= 550: pinglevel = '🔴 나쁨'
    elif ping > 550: pinglevel = '⚫ 매우나쁨'

    print('LATENCY:', ping, pinglevel.split(' ')[1])

@client.event
async def on_message(message):
    # 메시지 발신자가 다른 봇이거나 자기 자신인 경우, 접두사 뒤 명령어가 없는 경우 무시합니다.
    if message.author.bot or message.author == client.user or message.content == '%':
        return
    # 메시지를 수신한 곳이 서버인 경우 True, 아니면 False.
    if message.channel.type == discord.ChannelType.group or message.channel.type == discord.ChannelType.private: serverid_or_type = message.channel.type
    else: serverid_or_type = message.guild.id

    if message.content == prefix + '등록':
        if str(message.author.id) in userdata:
            await message.channel.send(f'<@{message.author.id}> 이미 등록되어 있어요!')
            log(message.author.id, message.channel.id, message.content, '[이미 등록된 사용자]', fwhere_server=serverid_or_type)
        else:
            await message.channel.send(f'<@{message.author.id}>')
            embed = discord.Embed(title='약관', description='추가예정\n동의하시면 20초 안에 `동의`를 입력해주세요.', color=color['ask'], timestamp=datetime.datetime.utcnow())
            await message.channel.send(embed=embed)
            log(message.author.id, message.channel.id, message.content, '[약관]', fwhere_server=serverid_or_type)
            def check(m):
                return m.channel == message.channel and m.author == message.author
            try:
                msg = await client.wait_for(('message'), timeout=20.0, check=check)
            except asyncio.TimeoutError:
                await message.channel.send('시간이 초과되었습니다.')
            else:
                if msg.content == '동의':
                    today = datetime.datetime.today()
                    userdata[str(message.author.id)] = {'level': 1, 'type': 'User', 'date': f'{today.year}-{today.month}-{today.day}'}
                    savedata(user=userdata)
                    await message.channel.send(f'등록되었습니다. `{prefix}도움` 을 입력해서 전체 명령어를 볼 수 있습니다.')
                    log(message.author.id, message.channel.id, msg.content, '[약관]', fwhere_server=serverid_or_type)
                else:
                    await message.channel.send('취소되었습니다. 다시 시도해 주세요.')
                
        return

    # 등록되지 않은 유저일 경우
    if message.content.startswith(prefix) and not str(message.author.id) in userdata:
        embed=discord.Embed(title='❔ 미등록 사용자', description=f'**등록되어 있지 않은 사용자입니다!**\n`{prefix}등록`명령을 입력해서, 약관에 동의해주세요.', color=color['error'], timestamp=datetime.datetime.utcnow())
        embed.set_author(name=botname, icon_url=boticon)
        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)
        log(message.author.id, message.channel.id, message.content, '[미등록 사용자]', fwhere_server=serverid_or_type)
        return

    # 수신 위치가 서버이고 미등록 서버인 경우. 그리고 설치 명령 실행 시에는 이 알림이 발신되지 않음.
    if message.content.startswith(prefix) and type(serverid_or_type) == int and not str(message.guild.id) in serverdata:
        embed=discord.Embed(title='⏰미등록 서버', description=f'**등록되어 있지 않은 서버입니다!**\n`{prefix}설치`명령을 입력해서, 봇 설정을 완료해주세요.', color=color['error'], timestamp=datetime.datetime.utcnow())
        embed.set_author(name=botname, icon_url=boticon)
        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)
        log(message.author.id, message.channel.id, message.content, '[미등록 서버]', fwhere_server=serverid_or_type)
        return

    elif message.content == prefix + '탈퇴':
        pass

    elif message.content == prefix + '도움':
        embed=discord.Embed(title='전체 명령어 목록', color=color['default'], timestamp=datetime.datetime.utcnow())
        embed.add_field(name='**연어봇**', value=f'**`{prefix}정보`**: {botname}의 버전, 개발자 정보 등 확인', inline=True)
        embed.set_author(name=botname, icon_url=boticon)
        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)
        log(message.author.id, message.channel.id, message.content, '[도움]', fwhere_server=serverid_or_type)

    elif message.content == prefix + '정보': #
        embed=discord.Embed(title='봇 정보', description=f'봇 이름: {botname}\n봇 버전: {versionPrefix}{versionNum}', color=color['info'], timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=thumbnail)
        embed.set_author(name=botname, icon_url=boticon)
        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)
        log(message.author.id, message.channel.id, message.content, '[정보]', fwhere_server=serverid_or_type)

    elif message.content == prefix + '설정':
        pass

    elif message.content == prefix + '핑':
        embed=discord.Embed(title='🏓 퐁!', description=f'**현재 지연시간: {ping}ms - {pinglevel}**\n지연시간은 디스코드 웹소켓 프로토콜의 지연 시간(latency)을 뜻합니다.', color=color['error'], timestamp=datetime.datetime.utcnow())
        embed.set_author(name=botname, icon_url=boticon)
        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)
        log(message.author.id, message.channel.id, message.content, '[핑]', fwhere_server=serverid_or_type)

    elif message.content.startswith(prefix):
        embed=discord.Embed(title='**❌ 존재하지 않는 명령어입니다!**', description=f'`{prefix}도움`을 입력해서 전체 명령어를 볼 수 있어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
        embed.set_author(name=botname, icon_url=boticon)
        embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)
        log(message.author.id, message.channel.id, message.content, '[존재하지 않는 명령어입니다!]', fwhere_server=serverid_or_type)

#  멤버의 역할에 권한이 있는지 확인합니다.
def has_perm(member, perm):
    roles = member.roles
    for x in roles:
        if eval(f'x.permissions.{perm}'):
            return True
    return False

def setembed_onlyserver(message):
    embed=discord.Embed(title='**❌ DM 또는 그룹 메시지에서는 사용할 수 없는 명령어입니다!**', description='이 명령어는 서버에서만 사용할 수 있습니다.', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
    return embed

def setembed_donthaveperm(message, permname):
    embed=discord.Embed(title='**🛑 권한이 없습니다!**', description=f'이 명령어는 `{permname}` 권한이 있는 멤버 또는 개발자만 사용 가능합니다.', color=color['error'], timestamp=datetime.datetime.utcnow())
    embed.set_author(name=botname, icon_url=boticon)
    embed.set_footer(text=message.author, icon_url=message.author.avatar_url)
    return embed

def savedata(server=None, user=None):
    if platform.system() == 'Windows':
        if server != None:
            with open('C:/salmonbot/' + config['serverdataFileName'], 'w', encoding='utf-8') as serverdata_save:
                json.dump(server, serverdata_save, indent=4)
        if user != None:
            with open('C:/salmonbot/' + config['userdataFileName'], 'w', encoding='utf-8') as userdata_save:
                json.dump(user, userdata_save, indent=4)
    if platform.system() == 'Linux':
        if server != None:
            with open('/.salmonbot/' + config['serverdataFileName'], 'w', encoding='utf-8') as serverdata_save:
                json.dump(server, serverdata_save, indent=4)
        if user != None:
            with open('/.salmonbot/' + config['userdataFileName'], 'w', encoding='utf-8') as userdata_save:
                json.dump(user, userdata_save, indent=4)

# 로그 출력기 - 
# 함수 인자: fwho: 수신자, fwhere_channel: 수신 채널 아이디, freceived: 수신한 메시지 내용, fsent: 발신한 메시지 요약, fetc: 기타 기록, fwhere_server: 수신 서버 아이디
# 출력 형식: [날짜&시간] [ChannelType:] (채널 유형- DM/Group/서버아이디), [Author:] (수신자 아이디), [RCV:] (수신한 메시지 내용), [Sent:] (발신한 메시지 내용), [etc:] (기타 기록)
def log(fwho, fwhere_channel, freceived, fsent, fetc=None, fwhere_server=None):
    now = datetime.datetime.today()
    fwhen = f'{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}:{now.microsecond}'
    if fwhere_server == discord.ChannelType.group:
        print(f'[{fwhen}] [ChannelType:] Group, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}')
    elif fwhere_server == discord.ChannelType.private:
        print(f'[{fwhen}] [ChannelType:] DM, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV]: {freceived}, [Sent]: {fsent}, [etc]: {fetc}')
    else:
        print(f'[{fwhen}] [ServerID:] {fwhere_server}, [ChannelID:] {fwhere_channel}, [Author:] {fwho}, [RCV:] {freceived}, [Sent:] {fsent}, [etc:] {fetc}')

client.run(token)