import discord
import urlextract
import math

def accessibleChannelsMention(guild, clientid):
    alltext = []
    allvoice = []
    for ch in guild.channels:
        if ch.type == discord.ChannelType.text:
            alltext.append(ch)
        elif ch.type == discord.ChannelType.voice:
            allvoice.append(ch)
    oktextchs = []
    for textch in alltext:
        textchperms = textch.permissions_for(guild.get_member(clientid))
        if not (False in [textchperms.read_messages, textchperms.send_messages]):
            oktextchs.append(textch.mention)
    okvoicechs = []
    for voicech in allvoice:
        voicechperms = voicech.permissions_for(guild.get_member(clientid))
        if not (False in [voicechperms.connect, voicechperms.speak]):
            okvoicechs.append(f'[{voicech.name}](https://discordapp.com/channels/{guild.id}/{voicech.id})')
    return oktextchs, okvoicechs

def urlExtract(text):
    extr = urlextract.URLExtract()
    urls = extr.find_urls(text=text)
    return urls

