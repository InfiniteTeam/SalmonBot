class Lang:
    def __init__(self, langs: dict):
        self.langs = langs

    def getall(self, path: str):
        pathkeys = path.split('.')
        results = []
        for onelang in self.langs.keys():
            proc = self.langs[onelang]
            for key in pathkeys:
                proc = proc[key]
            results.append(proc)
        return results

    def langlist(self):
        return self.langs.keys()