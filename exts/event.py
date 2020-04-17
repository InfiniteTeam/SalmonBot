import discord
from discord.ext import commands
import traceback

class Event(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = client.get_data('color')
        self.emj = client.get_data('emojictrl')
        self.msglog = client.get_data('msglog')
        self.errors = client.get_data('errors')
        self.cur = client.get_data('cur')

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if self.cur.execute('select * from serverdata where id=%s', guild.id):
            self.msglog.print(f'이미 등록된 서버: ' + guild.name + f'({guild.id})')
            return
        self.msglog.print(f'새 서버: ' + guild.name + f'({guild.id})')
        try:
            sendables = list(filter(lambda ch: ch.permissions_for(guild.get_member(self.client.user.id)).send_messages, guild.text_channels))
            if sendables:
                selected = []
                for sch in sendables:
                    sname = sch.name.lower()
                    if '공지' in sname and '봇' in sname:
                        pass
                    elif 'noti' in sname and 'bot' in sname:
                        pass

                    elif '공지' in sname:
                        pass
                    elif 'noti' in sname:
                        pass

                    elif '봇' in sname:
                        pass
                    elif 'bot' in sname:
                        pass

                    else:
                        continue
                    selected.append(sch)
                
                if not selected:
                    selected.append(sendables[0])
                self.cur.execute('insert into serverdata(id, noticechannel, master) values (%s, %s, %s)', (guild.id, sendables[0].id, 0))
                self.msglog.print(f'서버 추가 성공: ' + guild.name + f'({guild.id})')
                embed = discord.Embed(title='🎉 안녕하세요!', description=f'안녕하세요! 연어봇을 초대해 주셔서 감사합니다. `{self.client.command_prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요!\n혹시 이 채널이 공지 채널이 아닌가요? `{self.client.command_prefix}공지채널` 명령으로 선택하세요!', color=self.color['salmon'])
                await sendables[0].send(embed=embed)
            else:
                self.cur.execute('insert into serverdata(id, noticechannel, master) values (%s, %s, %s)', (guild.id, None, 0))
                self.msglog.print(f'접근 가능한 채널이 없는 서버 추가 성공: ' + guild.name + f'({guild.id})')
        except:
            self.client.get_data('errlogger').error(traceback.format_exc())

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        if self.cur.execute('select * from serverdata where id=%s', guild.id):
            self.cur.execute('delete from serverdata where id=%s', guild.id)
            self.msglog.print(f'서버에서 제거됨: ' + guild.name + f'({guild.id})')
        else:
            self.msglog.print(f'이미 제거된 서버에서 제거됨: ' + guild.name + f'({guild.id})')

def setup(client):
    cog = Event(client)
    for cmd in cog.get_commands():
        cmd.add_check(client.get_data('check').master)
    client.add_cog(cog)
