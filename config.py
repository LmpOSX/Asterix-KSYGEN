#!/usr/bin/env python3
#
#  main.py
#  
#
#  Created by Luis Pequeno on 22/07/09.
#  Copyright (c) 2009 Indra. All rights reserved.


import sys
#import json
#from functools import reduce
from pathlib import Path
#from typing import *
import re

base_dir        = Path('.')
template_dir    = base_dir / 'plantillas'
specs_dir       = base_dir / 'specs'
#specs_dir       = base_dir / 'spec_dev'
#ksy_dir         = base_dir / 'ksy'
ksy_dir         = base_dir / '../CTkAstMgr/ksy'
#specs_list      = list(specs_dir.glob('cat???/cats/cat*/definition.json'))
specs_list      = list(specs_dir.glob('cat???/cat*.json'))
#ksy_version     = re.search(r'(_v\d+\.\d+\.\d+)',str(Path(sys.argv[0]))).group(1) if not Path(sys.argv[0]).is_symlink() else re.search(r'(_v\d+\.\d+\.\d+)',str(Path(sys.argv[0]).readlink())).group(1)

ospecs_list = [
specs_dir/'cat001/cats/cat1.4/definition.json',
specs_dir/'cat062/cats/cat1.18/definition.json',
specs_dir/'cat002/cats/cat1.1/definition.json',
specs_dir/'cat011/cats/cat1.3/definition.json',
specs_dir/'cat018/cats/cat1.7/definition.json',
]

