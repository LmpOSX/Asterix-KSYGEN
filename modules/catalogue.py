
#import sys
#import json
#from functools import reduce
#from pathlib import Path
#from typing import *
#import re

from .item import Item

class Catalogue:
    def __init__(self, catalogue:dict[str,dict], path:list[str]):
        self.catalogue:dict[str,dict] = {}
        self.path:list[str] = path
        for itm in catalogue:
            print(">>>>>" "En Catalogue__init__", itm.get('name'), path, "<<<<<")
            self.catalogue[itm.get('name')]=Item(itm, path)

    def __getitem__(self, key):
        if key is None:
            return Item(item_path=self.path)
        elif key in self.catalogue:
            return self.catalogue[key]
        
    def __iter__(self):
        return iter(self.catalogue.values())

    def __str__(self):

        result = ''

        for item in self:
            print("En Catalogue__str__", str(item.name))
            result += str(item)
            
        return result
