#!/usr/bin/env python3
#
#  main.py
#  
#
#  Created by Luis Pequeno on 22/07/09.
#  Copyright (c) 2009 Indra. All rights reserved.


import sys
import json
from functools import reduce
from pathlib import Path
from typing import *
import re

from config import *
from modules.spec import Spec

    
class Template:

    def __init__(self):

        self.data = {
            'category': '',
            'version':  '',
            'version_major':'',
            'version_minor':'',
            'cat':      '',
            'major':    '',
            'minor':    '',
            'title':    '',
            'preamble': '',
            'uap':      '',
            'catalogue':    '',
            'fspec_max_len':    '',
            'fspec_max_len_plot':    '',
            'fspec_max_len_track':    '',
        }

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]

    def __setitem__(self, key, value):
        if key in self.data:
            self.data[key]=value

    @property
    def keys(self):
        return self.data.keys()
    
    @property
    def fields(self):
        return self.data.items()
    
    def __iter__(self):
        return iter(self.data.values())

    def load(self, spec:Spec):

        self.category = f'{spec.cat:03}'
        self.major    = f'{spec.major:02}'
        self.minor    = f'{spec.minor:02}'

        for key in self.keys:
            if key in dir(spec):
                self[key] = str(getattr(spec,key))

    def fill(self):

        match self.category: #seleccionamos la plantilla segun la categoria
            case "001":
#                cat_template = template_dir / f'cat_001{ksy_version}.ksy'
                cat_template = template_dir / f'cat_001.ksy'

            case _:                    
#                cat_template = template_dir / f'cat_000{ksy_version}.ksy'
                cat_template = template_dir / f'cat_000.ksy'

        #generamos el archivo de salida
        ksy_cat_out = ksy_dir / f'cat_{self.category}_{self.major}_{self.minor}.ksy'

        try:
            template = cat_template.open().read()
            
            for key, value in self.fields:
                mark = f'{{{key}}}'
                template = template.replace(mark, str(value))

            ksy_cat_out.open('w').write(template)
            
            print(f"Plantilla rellenada y guardada en {ksy_cat_out}")

        except Exception as e:
            print(f"Error: {e}")

def main():

    for spec_path in specs_list:
        spec     = Spec(spec_path)
        template = Template()
        template.load(spec)
        template.fill()
        
if __name__ == "__main__":

    main()


