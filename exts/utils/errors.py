from discord.ext import commands
from typing import List, Tuple, Union

class NotRegistered(commands.CheckFailure):
    pass

class NotMaster(commands.CheckFailure):
    pass

class GlobaldataAlreadyAdded(Exception):
    pass

class SentByBotUser(commands.CheckFailure):
    pass

class LockedExtensionUnloading(Exception):
    pass

class ArpaIsGenius(Exception):
    pass

class ParamsNotExist(Exception):
    def __init__(self, param):
        self.param = param
        super().__init__('존재하지 않는 옵션값입니다: {}'.format(param))

class NotGuildChannel(commands.CheckFailure):
    pass