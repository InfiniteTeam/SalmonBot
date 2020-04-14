import discord
from discord.ext import commands

class Checks:
    def __init__(self, cur, error):
        self.cur = cur
        self.error = error

    def set_cursor(self, cur):
        self.cur = cur

    def set_error(self, error):
        self.error = error

    async def registered(self, ctx: commands.Context):
        if self.cur.execute('select * from userdata where id=%s', ctx.author.id):
            return True
        raise self.error.NotRegistered('가입되지 않은 사용자입니다: {}'.format(ctx.author.id))
    
    def is_registered(self):
        return commands.check(self.registered)

    async def master(self, ctx: commands.Context):
        if self.cur.execute('select * from userdata where id=%s and type=%s', (ctx.author.id, 'Master')):
            return True
        raise self.error.NotMaster('마스터 유저가 아닙니다: {}'.format(ctx.author.id))

    def is_master(self):
        return commands.check(self.master)