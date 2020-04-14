# -*- coding: utf-8 -*-

import discord
from discord.ext import commands, tasks
from exts.utils.salmon import Salmon
import asyncio
import platform
import json
import os
import paramiko
import datetime
import logging
import logging.handlers
import pymysql
import sys
import traceback
from iftext import pulse
from exts.utils import checks, errors, emojictrl, msglogger

# Local Data Load
with open('./data/config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)
with open('./data/version.json', encoding='utf-8') as version_file:
    version = json.load(version_file)
with open('./data/color.json', encoding='utf-8') as color_file:
    color = json.load(color_file)
with open('./data/emojis.json', encoding='utf-8') as emojis_file:
    emojis = json.load(emojis_file)

# Make Dir
reqdirs = ['./logs', './logs/salmon', './logs/error', './logs/ping']
for dit in reqdirs:
    if not os.path.isdir(dit):
        os.makedirs(dit)

logger = logging.getLogger('salmonbot')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_streamh = logging.StreamHandler()
log_streamh.setFormatter(log_formatter)
logger.addHandler(log_streamh)
log_fileh = logging.handlers.RotatingFileHandler('./logs/salmon/salmon.log', maxBytes=config['maxlogbytes'], backupCount=10, encoding='utf-8')
log_fileh.setFormatter(log_formatter)
logger.addHandler(log_fileh)

pinglogger = logging.getLogger('ping')
pinglogger.setLevel(logging.INFO)
ping_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ping_fileh = logging.handlers.RotatingFileHandler('./logs/ping/ping.log', maxBytes=config['maxlogbytes'], backupCount=10, encoding='utf-8')
ping_fileh.setFormatter(ping_formatter)
pinglogger.addHandler(ping_fileh)

errlogger = logging.getLogger('error')
errlogger.setLevel(logging.DEBUG)
err_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
err_streamh = logging.StreamHandler()
err_streamh.setFormatter(err_formatter)
errlogger.addHandler(err_streamh)
err_fileh = logging.handlers.RotatingFileHandler('./logs/error/error.log', maxBytes=config['maxlogbytes'], backupCount=10, encoding='utf-8')
err_fileh.setFormatter(err_formatter)
errlogger.addHandler(err_fileh)

logger.info('========== START ==========')

langs = {}
for langfile in list(filter(lambda x: os.path.splitext(x)[1] == '.json', os.listdir('./langs'))):
    with open(f'./langs/{langfile}', encoding='utf-8') as langs_file:
        langs[os.path.splitext(langfile)[0]] = json.load(langs_file)

# IMPORTant data
if platform.system() == 'Windows':
    if config['betamode'] == False:
        with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['tokenFileName'], encoding='utf-8') as token_file:
            token = token_file.read()
    else:
        with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['betatokenFileName'], encoding='utf-8') as token_file:
            token = token_file.read()
    with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
    with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['openapiFileName'], encoding='utf-8') as openapi_file:
        openapi = json.load(openapi_file)
elif platform.system() == 'Linux':
    if config['is_android']:
        if config['betamode'] == False:
            with open(os.path.abspath(config['securedir']['Android']) + '/' + config['tokenFileName'], encoding='utf-8') as token_file:
                token = token_file.read()
        else:
            with open(os.path.abspath(config['securedir']['Android']) + '/' + config['betatokenFileName'], encoding='utf-8') as token_file:
                token = token_file.read()
        with open(os.path.abspath(config['securedir']['Android']) + '/' + config['dbacName'], encoding='utf-8') as dbac_file:
            dbac = json.load(dbac_file)
        with open(os.path.abspath(config['securedir']['Android']) + '/' + config['sshFileName'], encoding='utf-8') as ssh_file:
            ssh = json.load(ssh_file)
        with open(os.path.abspath(config['securedir']['Android']) + '/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
            openapi = json.load(openapi_file)
    else:
        if config['betamode'] == False:
            with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['tokenFileName'], encoding='utf-8') as token_file:
                token = token_file.read()
        else:
            with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['betatokenFileName'], encoding='utf-8') as token_file:
                token = token_file.read()
        with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['dbacName'], encoding='utf-8') as dbac_file:
            dbac = json.load(dbac_file)
        with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['sshFileName'], encoding='utf-8') as ssh_file:
            ssh = json.load(ssh_file)
        with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['openapiFileName'], encoding='utf-8') as openapi_file:
            openapi = json.load(openapi_file)

prefix = config['prefix']
activity = config['activity']
status = config['defaultStatus']
boticon = config['botIconUrl']
thumbnail = config['thumbnailUrl']
imshost = config['ims_host']
for i in color.keys(): # convert HEX to DEC
    color[i] = int(color[i], 16)

# SSH Connect
sshclient = paramiko.SSHClient()
sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy)
sshclient.connect(ssh['host'], username=ssh['user'], password=ssh['password'], port=ssh['port'])

# DB Connect
db = pymysql.connect(
    host=dbac['host'],
    user=dbac['dbUser'],
    password=dbac['dbPassword'],
    db=dbac['dbName'],
    charset='utf8',
    autocommit=True
)
cur = db.cursor(pymysql.cursors.DictCursor)

logger.info('확장 및 명령을 로드합니다.')

# Start Bot
client = Salmon(command_prefix=prefix, error=errors, status=discord.Status.dnd, activity=discord.Game('연어봇 시작'))
client.remove_command('help')
msglog = msglogger.Msglog(logger)

check = checks.Checks(cur=cur, error=errors)
emj = emojictrl.Emoji(client, emojis['emoji-server'], emojis['emojis'])
gamenum = 0

# Event Functions

@client.event
async def on_ready():
    logger.info(f'로그인: {client.user.id}')
    logger.info('백그라운드 루프를 시작합니다.')
    presence_loop.start()
    if config['betamode']:  
        logger.warning('BETA MODE ENABLED')
        # pulse.send_pulse.start(client=client, user='salmonbot-beta', token=token.strip(), host='arpa.kro.kr', version=version['versionPrefix'] + version['versionNum'])
    else:
        pass
        # pulse.send_pulse.start(client=client, user='salmonbot', token=token.strip(), host='arpa.kro.kr', version=version['versionPrefix'] + version['versionNum'])

@tasks.loop(seconds=5)
async def presence_loop():
    global gamenum
    games = [f'연어봇 - {prefix}도움 입력!', f'{len(client.guilds)}개의 서버와 함께', f'{len(client.users)}명의 사용자와 함께']
    await client.change_presence(status=discord.Status.online, activity=discord.Game(games[gamenum]))
    if gamenum == len(games) - 1:
        gamenum = 0
    else:
        gamenum += 1
client.invoke
@client.event
async def on_error(event, *args, **kwargs):
    ignoreexc = [discord.http.NotFound]
    excinfo = sys.exc_info()
    errstr = f'{"".join(traceback.format_tb(excinfo[2]))}{excinfo[0].__name__}: {excinfo[1]}'
    errlogger.error(errstr)

@client.event
async def on_command_error(ctx: commands.Context, error):
    if hasattr(ctx.command, 'on_error'):
        return
    elif isinstance(error, errors.NotRegistered):
        await ctx.send(f'등록되지 않은 사용자입니다! `{prefix}등록` 명령으로 등록해주세요!')
    elif isinstance(error, errors.NotMaster):
        await ctx.send(f'마스터 사용자가 아닙니다. 관리자만 사용 가능합니다.')
    elif isinstance(error, commands.errors.CommandInvokeError) and 'In embed.description: Must be 2048 or fewer in length.' in str(error):
        embed = discord.Embed(title='❗ 메시지 전송 실패', description='보내려고 하는 메시지가 너무 길어(2000자 이상) 전송에 실패했습니다.', color=color['error'])
        await ctx.send(embed=embed)
    elif isinstance(error, commands.errors.CommandNotFound):
        embed = discord.Embed(title='❓ 존재하지 않는 명령어입니다!', description=f'`{prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요.', color=color['error'])
        await ctx.send(embed=embed)
    else:
        # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        tb = traceback.format_exception(type(error), error.__cause__, error.__traceback__)
        err = []
        for line in tb:
            err.append(line.rstrip())
        errstr = '\n'.join(err)
        errlogger.error(errstr)
        embed = discord.Embed(title='❌ 오류!', description=f'무언가 오류가 발생했습니다!\n```python\n{errstr}```\n오류가 기록되었습니다. 나중에 개발자가 확인하고 처리하게 됩니다.', color=color['error'])
        await ctx.send(embed=embed)

# Salmon Commands
@client.group(name='ext')
@check.is_master()
async def _ext(ctx: commands.Context):
    pass

@_ext.command(name='list')
async def _ext_list(ctx: commands.Context):
    allexts = ''
    for oneext in client.get_data('allexts'):
        if oneext in client.extensions:
            allexts += f'{emj.get("check")} {oneext}\n'
        else:
            allexts += f'{emj.get("cross")} {oneext}\n'
    embed = discord.Embed(title=f'🔌 전체 확장 목록', color=color['salmon'], description=
        f"""\
            총 {len(client.get_data('allexts'))}개 중 {len(client.extensions)}개 로드됨.
            {allexts}
        """
    )
    msglog.log(ctx, '[전체 확장 목록')
    await ctx.send(embed=embed)

@_ext.command(name='reload')
async def _ext_reload(ctx: commands.Context, *names):
    try:
        for onename in names:
            if not (onename in client.extensions):
                raise commands.ExtensionNotLoaded(f'로드되지 않은 확장: {onename}')
        for onename in names:
            client.reload_extension(onename)

    except commands.ExtensionNotLoaded:
        embed = discord.Embed(description=f'**❓ 로드되지 않았거나 존재하지 않는 확장입니다: `{onename}`**', color=color['error'])
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description=f'**{emj.get("check")} 확장 리로드를 완료했습니다: `{", ".join(names)}`**', color=color['info'])
        await ctx.send(embed=embed)
    
@_ext.command(name='load')
async def _ext_load(ctx: commands.Context, *names):
    try:
        for onename in names:
            if not (onename in client.get_data('allexts')):
                raise commands.ExtensionNotFound(f'존재하지 않는 확장: {onename}')
            if onename in client.extensions:
                raise commands.ExtensionAlreadyLoaded(f'이미 로드된 확장: {onename}')
        for onename in names:
            client.load_extension(onename)

    except commands.ExtensionNotFound:
        embed = discord.Embed(description=f'**❓ 존재하지 않는 확장입니다: `{onename}`**', color=color['error'])
        await ctx.send(embed=embed)
    except commands.ExtensionAlreadyLoaded:
        embed = discord.Embed(description=f'**❓ 이미 로드된 확장입니다: `{onename}`**', color=color['error'])
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description=f'**{emj.get("check")} 확장 로드를 완료했습니다: `{", ".join(names)}`**', color=color['info'])
        await ctx.send(embed=embed)

@_ext.command(name='unload')
async def _ext_unload(ctx: commands.Context, *names):
    try:
        for onename in names:
            if not (onename in client.extensions):
                raise commands.ExtensionNotLoaded(f'로드되지 않은 확장: {onename}')
        for onename in names:
            client.unload_extension(onename)

    except commands.ExtensionNotLoaded:
        embed = discord.Embed(description=f'**❓ 로드되지 않은 확장입니다: `{onename}`**', color=color['error'])
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description=f'**{emj.get("check")} 확장 언로드를 완료했습니다: `{", ".join(names)}`**', color=color['info'])
        await ctx.send(embed=embed)

"""
    elif args[0] == 'unload':
        name = args[1]
        try:
            client.unload_extension(name)
        except commands.ExtensionNotLoaded:
            embed = discord.Embed(description=f'**❓ 로드되지 않은 확장입니다: `{name}`**', color=color['error'])
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f'**{emj.get("check")} 확장 언로드를 완료했습니다: `{name}`**', color=color['info'])
            await ctx.send(embed=embed)
"""

# Salmon Commands
logger.info('봇 시작 준비 완료.')
client.add_data('color', color)
client.add_data('emojictrl', emj)
client.add_data('check', check)
client.datas['allexts'] = []
for ext in list(filter(lambda x: x.endswith('.py'), os.listdir('./exts'))):
    client.datas['allexts'].append('exts.' + os.path.splitext(ext)[0])
    client.load_extension('exts.' + os.path.splitext(ext)[0])
client.run(token)