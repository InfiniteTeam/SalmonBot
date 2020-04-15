from discord.ext import commands

class NotRegistered(commands.CheckFailure):
    pass

class NotMaster(commands.CheckFailure):
    pass

class GlobaldataAlreadyAdded(Exception):
    pass

class SentByBotUser(Exception):
    pass

class LockedExtensionUnloading(Exception):
    pass