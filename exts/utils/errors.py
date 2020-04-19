from discord.ext import commands

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

class NotValidParam(Exception):
    pass

class NotGuildChannel(commands.CheckFailure):
    pass