class ParamCtrl:
    def __init__(self, paramlist):
        self.params = paramlist

    def is_exists(self, param):
        return param in self.params