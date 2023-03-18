import json
from demhack.utils import SystemObject

USER = 1
MANAGER = 2

class AccessManager (SystemObject): 
    def __init__(self):
        self.keys = dict() 
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
            
