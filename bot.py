# -*-coding: utf-8-*-

import discord
from discord.ext import tasks
import asyncio
import json
import time
import platform

# ========== config data import ==========
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
color = config['color']
for i in color.keys(): # convert HEX to DEC
    color[i] = int(color[i], 16)

# ========== prepair bot ==========
client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as{}'.format(client.user))
    await client.change_presence(status=eval('discord.Status.{}'.format(status)), activity=discord.Game(activity)) # presence 를 설정 데이터로 적용합니다.

@client.event
async def on_message(message):
    if message.author.bot or message.author == client.user:
        return
    
    if message.content.startswith(prefix + ' 도움'):
        embed=discord.Embed(title="연어봇 - 명령어", description="추가될 예정입니다.", color=color['default'])
        await message.channel.send(embed=embed)
        return

client.run(token)