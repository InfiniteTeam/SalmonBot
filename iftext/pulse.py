import asyncio
import discord
from discord.ext import commands, tasks
import datetime
import traceback
import requests

@tasks.loop(seconds=5)
async def send_pulse(client, user, token, host, version=None):
    try:
        headers = {
            'IMS-User': user,
            'IMS-Token': token.strip()
        }
        userids = []
        for u in client.users:
            userids.append(u.id)
        guildids = []
        for g in client.guilds:
            guildids.append(g.id)
        dataset = {
            'version': version,
            'last-alive-time': datetime.datetime.now().strftime('%Y-%m-%d %X'),
            'client.users/len': len(client.users),
            'client.guilds/len': len(client.guilds),
            'client.users;ids': userids,
            'client.guilds;ids': guildids,
            'client.latency': client.latency
            }
        resp = requests.post(f'http://{host}/ims/dataset', json=dataset, headers=headers)
    except:
        traceback.print_exc()
