import json

USER = 1
MANAGER = 2

class access_manager:
    keys = dict()
    def __init__(self):
        pass
    def load(self, filename):
        with open(filename) as f:
            self.keys = json.load(f)
    def dump(self, filename):
        with open(filename, 'w') as f:
            print(json.dumps(self.keys, ensure_ascii=False, indent=4), file=f)
    def set_status(self, id, status):
        if id in self.keys:
            self.keys[id] = (status, self.keys[id][1])
        else:
            self.keys[id] = (status, "None")
    def set_nickname(self, id, nickname):
        if id in self.keys:
            self.keys[id] = (self.keys[id][0], nickname)
        else:
            self.keys[id] = (USER, nickname)
    def get_status(self, id, nickname):
        self.set_nickname(id, nickname)    
        return self.keys[id][0]
    def get_managers(self):
        return [(key, self.keys[key][1]) for key in self.keys if self.keys[key][0] == MANAGER]
            
