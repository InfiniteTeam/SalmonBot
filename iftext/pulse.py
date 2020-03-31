import asyncio
import discord
from discord.ext import commands, tasks
import datetime
import traceback
import requests

@tasks.loop(seconds=5)
async def send_pulse(client, user, token):
    try:
        headers = {
            'IMS-User': user,
            'IMS-Token': str(token)
        }
        dataset = {
            'client.users/len': len(client.users),
            'client.guilds/len': len(client.guilds),
            'client.latency': client.latency
            }
        resp = requests.post('http://arpa.kro.kr:5000/ims/dataset', json=dataset, headers=headers)
    except:
        traceback.print_exc()