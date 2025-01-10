
#import sys
import json
#from functools import reduce
from pathlib import Path
#from typing import *
#import re

from .uap import UAP
from .catalogue import Catalogue

class Spec:
    def __init__(self, spec_path:Path):
        print(spec_path)
        self.path = spec_path
        with self.path.open() as f: #abrimos archivo de specs, en formato json
            self.root = json.loads(f.read())
            
        #cargamos los principales valores que se usan para generar el archivo ksy
        self.contents       = self.root['contents']
        self.category   = '{:03}'.format(self.contents['category'])
        self.version    = '{}.{}'.format(self.contents['edition']['major'],self.contents['edition']['minor'])
        self.version_major      = '{:02}'.format(self.contents['edition']['major'])
        self.version_minor      = '{:02}'.format(self.contents['edition']['minor'])
        self.cat        = self.contents['category']
        self.major      = self.contents['edition']['major']
        self.minor      = self.contents['edition']['minor']
        self.title      = '\n  '.join(self.contents['title'].split('\n'))
        self.preamble   = '\n  '.join(self.contents['preamble'].split('\n'))
        #print(self.contents['catalogue'])
        print(self.category)
        self.catalogue  = Catalogue(catalogue=self.contents['catalogue'], path=[self.category])
        self.uap        = UAP(self.contents['uap'], self.catalogue)
        for f in [fspec for fspec in dir(self.uap) if fspec.startswith('fspec_max_len')]:
            #print("estoy en spec init, fspec_max_len name: ", f)
            setattr(self, f, getattr(self.uap, f))
