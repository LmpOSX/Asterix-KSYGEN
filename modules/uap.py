
#import sys
#import json
#from functools import reduce
#from pathlib import Path
#from typing import *
#import re

from .item import Item
from .catalogue import Catalogue

class UAP:
    def __init__(self, uap, catalogue:Catalogue):
        self._uaps = {}

        match uap['tag']:
            case 'Uap':
                self._uaps['uap']={}
                self.fspec_max_len = (len(uap['contents'])+6)//7
                for frn in range(0,len(uap['contents'])):
#                    print("estoy en UAP init, frn: ", frn)
                    match uap['contents'][frn]['tag']:
                        case 'UapItem':
                            self._uaps['uap'][frn] = catalogue[uap['contents'][frn]['contents']]
                        case 'UapItemSpare':
                            self._uaps['uap'][frn] = Item()
                        case 'UapItemRFS':        
                            self._uaps['uap'][frn] = Item(item_root={'tag':"RFS"}  , item_path=catalogue.path)
                            print(repr(self._uaps['uap'][frn]), self._uaps['uap'][frn].is_none, self._uaps['uap'][frn].is_rfs)
                                            
                    #si es un UapItemSpare, es un Item vacio, sino es un Item con el contenido del catalogue, pero revisar "UapItemRFS"

            case 'Uaps':
#                for uv in uap['variations']:
                name  = 0
                items = 1
                for uv in uap["contents"]['cases']:
                    self._uaps[uv[name]]={}
                    setattr(self, 'fspec_max_len_'+f"{uv[name]}" , (len(uv[items])+6)//7)
                    for frn in range(0,len(uv[items])):
#                        self._uaps[uv[name]][frn] = Item() if uv[items][frn]['tag'] in ( "UapItemSpare", "UapItemRFS" ) else catalogue[uv[items][frn]['contents']]
                        match uv[items][frn]['tag']:
                            case 'UapItem':
                                self._uaps[uv[name]][frn] = catalogue[uv[items][frn]['contents']]
                            case 'UapItemSpare':
                                self._uaps[uv[name]][frn] = Item()
                            case 'UapItemRFS':        
                                self._uaps[uv[name]][frn] = Item(item_root={'tag':"RFS"}  , item_path=catalogue.path)
                                print(repr(self._uaps[uv[name]][frn]), self._uaps[uv[name]][frn].is_none, self._uaps[uv[name]][frn].is_rfs)

        #print("UAP init")
        #print([f for f in dir(self) if f.startswith('fspec_max_len')], [getattr(self, f) for f in dir(self) if f.startswith('fspec_max_len')] )

    def __getattr__(self, uap_name):
        if uap_name in self._uaps:
            return self._uaps[uap_name]

    @property
    def uaps(self):
        return self._uaps.keys()

    @property        
    def is_unique(self):
        return 'uap' in self._uaps

    def __str__(self):

        rfs_type_h  = ''
        result      = ''
        indent      = '  '

        uap_type =  indent+'{nombre}_t:\n\n'+\
                    indent+'  params:\n'+\
                    indent+'    - id: cat\n'+\
                    indent+'      type: u1\n'+\
                    indent+'    - id: major\n'+\
                    indent+'      type: u1\n'+\
                    indent+'    - id: minor\n'+\
                    indent+'      type: u1\n\n'+\
                    indent+'    - id: fspec_max_len\n'+\
                    indent+'      type: u1\n\n'+\
                    indent+'  seq:\n'+\
                    indent+'    - id: fspec\n'+\
                    indent+'      type: field_spec(fspec_max_len)\n\n'

        uap_item =  indent*3+'- id: {nombre_item}\n'+\
                    indent*3+'  type: sub_{path_item}_t\n'+\
                    indent*3+'  if: fspec.octects.size > {octect_count} and fspec.flags[{frn}].flag\n\n'


        rfs_type =  indent+'\n'+\
                    indent+'sub_rfs_{ext_rfs}_t:\n'+\
                    indent+'  instances:\n'+\
                    indent+'    name:\n'+\
                    indent+'      value: \'"RFS"\'\n'+\
                    indent+'    title:\n'+\
                    indent+'      value: \'"Random Field Sequencing"\'\n\n'+\
                    indent+'  seq:\n'+\
                    indent+'    - id: num_irfs_list\n'+\
                    indent+'      type: u1\n'+\
                    indent+'    - id: irfs_list\n'+\
                    indent+'      type: sub_irfs_t\n'+\
                    indent+'      repeat: expr\n'+\
                    indent+'      repeat-expr: num_irfs_list\n\n'+\
                    indent+'  types:\n'+\
                    indent+'    sub_irfs_t:\n'+\
                    indent+'      seq:\n'+\
                    indent+'        - id: frn\n'+\
                    indent+'          type: u1\n'+\
                    indent+'        - id: value\n'+\
                    indent+'          type:\n'+\
                    indent+'            switch-on: frn\n'+\
                    indent+'            cases:\n'
        
        rfs_case =  indent*8+'{frn}: sub_{path_item}_t\n'



        for uap_name in self.uaps: #voy a recorrer self.uaps, cuyas keys son 'uap' si solo tiene un uap, o por ej cat1 'plot' y 'track'

            uap = getattr(self,uap_name) #en caso de varios UAP lo va a hacer para todos, en caso de un solo UAP lo haría para el unico UAP

            if not self.is_unique: #no hay un solo uap, por ej CAT001, es como que preparamos este encabezado solo para los que tienen varios UAPs
                result+=uap_type.format(nombre=uap_name)
            
            ext_rfs = uap_name if not self.is_unique else ''
            
            rfs_type_h += rfs_type.format(ext_rfs=ext_rfs)

            for idx in uap: #ahora recorremos el UAP y armamos el UAP
                if uap[idx].is_none:
                    continue

                path_item=uap[idx].ksy_path if not uap[idx].is_rfs else uap[idx].ksy_path+'_'+ext_rfs

                result += uap_item.format(nombre_item=uap[idx].uap_s, path_item=path_item, octect_count=idx//7, frn=idx)
            
                if not uap[idx].is_rfs:
                    rfs_type_h += rfs_case.format(frn=idx, path_item=uap[idx].ksy_path)


        result += rfs_type_h

        return result
