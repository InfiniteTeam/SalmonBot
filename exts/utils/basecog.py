from discord.ext import commands

class BaseCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = client.get_data('color')
        self.emj = client.get_data('emojictrl')
        self.msglog = client.get_data('msglog')
        self.errors = client.get_data('errors')