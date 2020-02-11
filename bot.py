# -*-coding: utf-8-*-

import discord
from discord.ext import tasks
import asyncio
import json
import time
import platform

# ========== 설정 데이터 불러오기 ==========
with open('./data/config.json', encoding='utf-8') as config_file:
        config = json.load(config_file)
if platform.system() == 'Windows':
    with open(config['secureDirWin'] + config['tokenFileName']) as token_file:
        token = token_file.readline()
elif platform.system() == 'Linux':
    with open(config['secureDirLnx'] + config['tokenFileName']) as token_file:
        token = token_file.readline()

prefix = config['prefix']
activity = config['activity']
status = config['status']

# ========== 봇 준비 ==========
client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as{}'.format(client.user))
    await client.change_presence(status=eval('discord.Status.{}'.format(status)), activity=discord.Game(activity)) # presence 를 설정 데이터로 적용합니다.

client.run(token)