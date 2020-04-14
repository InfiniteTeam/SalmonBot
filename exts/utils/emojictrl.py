import discord

class Emoji:
    def __init__(self, client: discord.Client, guild: int, emojis: dict):
        self.guild = guild
        self.emojis = emojis
        self.client = client

    def get(self, name):
        return self.client.get_emoji(self.emojis[name])

    def getid(self, name):
        return self.emojis[name]