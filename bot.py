# -*- coding: utf-8 -*-

import discord
from discord.ext import commands, tasks
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
from exts import errors

# Local Data Load
with open('./data/config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)
with open('./data/version.json', encoding='utf-8') as version_file:
    version = json.load(version_file)
with open('./data/color.json', encoding='utf-8') as color_file:
    color = json.load(color_file)
with open('./langs/ko-kr.json', encoding='utf-8') as langs_file:
    pass

logger = logging.getLogger('salmonbot')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_streamh = logging.StreamHandler()
log_streamh.setFormatter(log_formatter)
logger.addHandler(log_streamh)
log_fileh = logging.handlers.RotatingFileHandler('./logs/salmon/salmon.log', maxBytes=config['maxlogbytes'], backupCount=10)
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
err_fileh = logging.handlers.RotatingFileHandler('./logs/error/error.log', maxBytes=config['maxlogbytes'], backupCount=10)
err_fileh.setFormatter(err_formatter)
errlogger.addHandler(err_fileh)

logger.info('========== START ==========')

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
    else:
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

# Make Dir
reqdirs = ['./logs', './logs/salmon', './logs/error', './logs/ping']
for dit in reqdirs:
    if not os.path.isdir(dit):
        os.makedirs(dit)

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

logger.info('Ready to start bot.')

# Start Bot
client = commands.Bot(command_prefix=prefix, status=discord.Status.dnd, activity=discord.Game('연어봇 시작'))
client.remove_command('help')

# Event Functions

@client.event
async def on_ready():
    logger.info(f'로그인: {client.user.id}')
    if config['betamode']:
        pulse.send_pulse.start(client=client, user='salmonbot-beta', token=token.strip(), host='arpa.kro.kr', version=version['versionPrefix'] + version['versionNum'])
    else:
        pulse.send_pulse.start(client=client, user='salmonbot', token=token.strip(), host='arpa.kro.kr', version=version['versionPrefix'] + version['versionNum'])

@client.event
async def on_error(event, *args, **kwargs):
    ignoreexc = [discord.http.NotFound]
    excinfo = sys.exc_info()
    errstr = f'{"".join(traceback.format_tb(excinfo[2]))}{excinfo[0].__name__}: {excinfo[1]}'

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, errors.NotRegistered):
        await ctx.send('등록되지 않은 사용자입니다!')

# Command Checks

def is_registered():
    async def check(ctx: commands.Context):
        if cur.execute('select * from userdata where id=%s', ctx.author.id):
            return True
        raise errors.NotRegistered('가입되지 않은 사용자입니다: {}'.format(ctx.author.id))
    return commands.check(check)

# Salmon Commands

@client.command(name='help', aliases=['도움'])
@is_registered()
async def _help(ctx: commands.Context):
    embed = discord.Embed(title=)
    await ctx.send()

client.run(token)