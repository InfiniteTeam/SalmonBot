from discord.ext import commands

class BaseCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = client.get_data('color')
        self.openapi = client.get_data('openapi')
        self.emj = client.get_data('emojictrl')
        self.msglog = client.get_data('msglog')
        self.logger = client.get_data('logger')
        self.errors = client.get_data('errors')
        self.cur = client.get_data('cur')
        self.check = client.get_data('check')
        self.errlogger = client.get_data('errlogger')