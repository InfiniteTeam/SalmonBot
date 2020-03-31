import asyncio
import discord
from discord.ext import commands, tasks
import datetime
import traceback
import requests

@tasks.loop(seconds=5)
async def send_pulse(client, user, token=None, tokenfile=None):
    try:
        if token != None:
            headers = {
                'IMS-User': user,
                'IMS-Token': token
            }
        elif tokenfile != None:

            headers = {
                'IMS-User': user,
                'IMS-Token': tokenfile.read()
            }
        dataset = {
            'client.users/len': len(client.users),
            'client.guilds/len': len(client.guilds),
            'client.latency': client.latency
            }
        resp = requests.post('http://arpa.kro.kr:5000/ims/dataset', json=dataset, headers=headers)
    except:
        traceback.print_exc()