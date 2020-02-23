# -*-coding: utf-8-*-

import discord
from discord.ext import tasks, commands
import asyncio
import json
import time
import platform
import datetime
import pymysql

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

# 데이터베이스 서버 연결
def loaddata():
    db = pymysql.connect(host=dbac['host'], user=dbac['dbUser'], password=dbac['dbPassword'], db=dbac['dbName'], charset='utf8')
    cur = db.cursor(pymysql.cursors.DictCursor)