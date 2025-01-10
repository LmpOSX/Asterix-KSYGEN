

import sys
#import json
from functools import reduce
#from pathlib import Path
from typing import *
#import re

from .content import Content

class Item:
    
    @classmethod
    def init_none(cls, item_root, item_path):
        print("item_root is None")
        return (None, "None", item_path, "Fixed", 0)

    @classmethod
    def init_int(cls, item_root, item_path):
        print("item_root is Int")
        return (f'fx{item_root}', f'Extension bit fx{item_root}', item_path + [f'fx{item_root}'],'Fixed', 1 )

    @classmethod
    def init_spare(cls, item_root, item_path):
        #print("item_root is Spare")
        return ('spare', 'Spare bits', item_path + ['spare'], 'Fixed', item_root.get('contents'))

    @classmethod
    def init_rfs(cls, item_root, item_path):
        #print("item_root is Spare")
        return (item_root.get('tag'), 'Random Field Sequencing', item_path + ['rfs'], 'RFS', 1)

    @classmethod
    def init_element(cls, item_root:Dict[str,Any], path:list):
        type_str = 'Fixed'
        size     = item_root['bitSize']
        content = None
        selectors = []
        cases = []
        contents = []

        if '/'.join(path) in ("001/100/MODEC", "020/100/MODEC", "048/100/MODEC"): #hack, para detectar cuando tenemos un item que esta coficado en gray_code
            item_root['rule']['contents']['tag']='ContentGray'

        if item_root['rule']['tag'] == 'ContextFree':
            try:
                content = Content(content=item_root['rule']['contents'], size=size)
            except:
                content = None
    

        elif item_root['rule']['tag'] == 'Dependent':
           type_str, size, selectors, cases, contents = Item.init_dependent(item_root['rule']['contents'], path, implicit_size=size, implicit_type="Element")

        #print("item_root is Element", path)
        return (type_str, size, selectors, cases, contents, content)

    @classmethod
#    def init_group(cls, item_root:Dict[str,Any], path:list):
    def init_group(cls, item_root:List[Dict[str,Any]], path:list):

        type_str = 'Fixed'
        spare_count = 0
        sub_items:List[Item] = []
        for j in item_root:
            sub_items.append(Item(j,path))
            if sub_items[-1].is_spare:
                spare_count+=1
                sub_items[-1].name+=f'_{spare_count}'
                sub_items[-1].path[-1]+=f'_{spare_count}'

        size = reduce(lambda acc, obj: acc + obj.size, sub_items, 0)
        
        #print("item_root is Group", path)
        return (type_str, size, sub_items)

    @classmethod
    def init_repetitive(cls, item_root:Dict[str,Any], path:list):
        #print("item_root is Repetitive", path)

        type_str = 'Repetitive'
        sub_items:List[Item] = []
        ir = {
                "rule": {
                    "tag": "ContextFree",
                    "contents": item_root['variation']
                },
        }

        match item_root['type']['tag']:
            case "RepetitiveRegular":
                type_str = 'Repetitive'
                match item_root['variation']['tag']:
                    case "Group":
                        sub_items.extend(Item(ir, path).sub_items)
                    case "Element":
                        sub_items.append(Item(ir,path))

            case "RepetitiveFx":
                type_str = 'Extended'
                match item_root['variation']['tag']:
                    case "Group":
                        sub_items.extend(Item(ir, path).sub_items)
                        sub_items.append(Item( 1, path))
                    case "Element":
                        sub_items.append(Item(ir, path))
                        sub_items.append(Item( 1, path))
                    case _:
                        sys.stderr.write(f"Error: Tipo Repetitive/FX, no contiene item type Element ni Group\n")
                        sys.exit(1)

        size = reduce(lambda acc, obj: acc + obj.size, sub_items, 0)
        return (type_str, size, sub_items)

    @classmethod
#    def init_extended(cls, item_root:Dict[str,Any], path:list):
    def init_extended(cls, item_root:List[Dict[str,Any]], path:list):
        #print("item_root is Extended", path)
        type_str = 'Extended'
        sub_items:List[Item] = []

        fx=0
        ext_sec_size = 0
        spare_count = 0
        for h in range(0,len(item_root)):
            if item_root[h] is None:
                fx+=1
                sub_items.append(Item( fx, path))
                if   fx == 1:
                    size = reduce(lambda acc, obj: acc + obj.size, sub_items, 0)
                elif fx == 2:
                    ext_sec_size = reduce(lambda acc, obj: acc + obj.size, sub_items, 0)-size
            else:
                sub_items.append(Item(item_root[h], path))
                if sub_items[-1].is_spare:
                    spare_count+=1
                    sub_items[-1].name     += f'_{spare_count}'
                    sub_items[-1].path[-1] += f'_{spare_count}'

        return (type_str, size, ext_sec_size, sub_items)

    @classmethod
    def init_compound(cls, item_root:Dict[str,Any], path:list):
        #print("item_root is Compound", path)

        type_str = 'Compound'
        sub_items:List[Item] = []

        for itm in item_root:
            sub_items.append(Item(itm, path))

        size = reduce(lambda acc, obj: acc + obj.size, sub_items, 0)
        ext_sec_size = reduce(lambda acc, obj: acc + obj.ext_sec_size, sub_items, 0)

        return (type_str, size, ext_sec_size, sub_items)

    @classmethod
    def init_dependent(cls, item_root:Dict[str,Any], path:list, implicit_size:int=None, implicit_type:str=None):
        #print("item_root is Dependent", path)

        type_str = 'Dependent'
        size     = item_root['default']["contents"]['bitSize'] if implicit_size is None else implicit_size

        selectors = item_root["path"]
        cases     = [ case[0] for case in item_root['cases']] + ['default']
        types     = [ case[1] for case in item_root['cases']] + [item_root['default']]

        ir_t = {
                "rule": {
                    "tag": "ContextFree",
                },
        }
        contents:List[Item, List[Item]] = []
        type_element:Dict[str,Any]= {}
#        print("Dependent", path, size, selectors, cases, types)
        for type_ in types:
            if implicit_type is not None:
                type_element["tag"] = implicit_type
                type_element["contents"] = {"bitSize": implicit_size, "rule": {"contents": type_, "tag": "ContextFree"}}
            else:
                type_element = type_

            if  type_element["tag"] == 'Element':
                content:Item = Item.init_element(type_element["contents"], path)[5]
                contents.append(content)
            elif type_element["tag"] == 'Group':
                content:List[Item] = Item.init_group(type_element["contents"], path)[2]
                contents.append(content)

#        print("Dependent", path, size, implicit_type)
#        print(type_str, path, size, selectors, cases, contents )
        return (type_str, size, selectors, cases, contents ) #content)

    @classmethod
    def init_all(cls, item_root:Dict[str,Any], item_path:list):
        name  = item_root.get('name', 'value')
        title = item_root.get('title', ' ').replace('\'', "`")
        path  = item_path + ([] if name == 'value' else [name])

        return (name, title, path )

    recursion = 0

    def __init__(self, item_root: dict[str, Any] = None, item_path:list[str] = []):
        
        #deb = debug.Debug(f"Item.__init__(*self, {''}, {item_path})")

        Item.recursion+=1
        self.root  = item_root
        self.sub_items:list[Item]       = []
        self.path:list[str]             = []
        self.size                       = 0
        self.ext_sec_size               = 0

        self.selectors:List[Any]        = []
        self.cases:List[Any]            = []

        self.type_str = 'Explicit'
        self.content = None
        self.contents:List[Any]         = []

#        print(f"\n\nITEM: >>>>>> ({Item.recursion})", item_path)

        #primero me fijo si es None, o sea si es un fx de un Extended
        if self.root is None:   #el item es un fx de un Extended sin embargo para compatibilidad creamos un elemento none
            self.name, self.title, self.path, self.type_str, self.size = Item.init_none(item_root, item_path)
            Item.recursion-=1
            return

        if isinstance(self.root, int): #el item es un fx de un Extended, y en general lo va a crear mas abajo esta rutina
            self.name, self.title, self.path, self.type_str, self.size = Item.init_int(item_root, item_path)
            Item.recursion-=1
            return

        #si no es None, entonces reviso si es spare, ya que el spare no tiene nombre
        #el spare siempre es un sub_item
        if self.root.get('tag')=='Spare': #spare is true
            self.name, self.title, self.path, self.type_str, self.size = Item.init_spare(item_root, item_path)
            Item.recursion-=1
            return

        #si no es None, ni es spare, reviso si es RFS
        if self.root.get('tag')=="RFS": #spare is true
            self.name, self.title, self.path, self.type_str, self.size = Item.init_rfs(item_root, item_path)
            Item.recursion-=1
            return

        #si no es None ni tampoco es spare entonces es un item completo
        #tiene un type, tiene name, y hay que analizarlo
        #deb.imp("item_root no es None ni spare, sigo")
        #print("item_root no es None, ni Int, ni Spare")

        # El objetivo ahora, es básicamente crear un nuevo ítem, clase Item y entrar en recursión
        #deb.imp(f"Recursion para buscar sub-items segun tipo: {self.var['type']}")

        if item_root.get('tag') == 'Item':
            item_root = item_root['contents']

        self.name, self.title, self.path = Item.init_all(item_root, item_path)
        match item_root['rule']['tag']:
            case 'ContextFree':
                match item_root['rule']['contents']['tag']:
                    case "Element":
                        self.type_str, self.size, self.selectors, self.cases, self.contents, self.content = Item.init_element(item_root['rule']['contents']['contents'], self.path )

                    case "Group":
                        self.type_str, self.size, self.sub_items = Item.init_group(item_root['rule']['contents']['contents'], self.path )

                    case "Repetitive":
                        self.type_str, self.size, self.sub_items = Item.init_repetitive(item_root['rule']['contents']['contents'], self.path )

                    case "Extended":
                        self.type_str, self.size, self.ext_sec_size, self.sub_items = Item.init_extended(item_root['rule']['contents']['contents'], self.path )

                    case "Compound":
                        self.type_str, self.size, self.ext_sec_size, self.sub_items = Item.init_compound(item_root['rule']['contents']['contents'], self.path )

                    case _:
                        pass
                        

            case 'Dependent':
#                print("Dependent")
                self.type_str, self.size, self.selectors, self.cases, self.contents = Item.init_dependent(item_root['rule']['contents'], self.path)
                pass

        
        #print(f'Tipo {self.type_str}: name: {self.name}, path: {self.path}, size: {self.size}, ext_sec_size: {self.ext_sec_size}')
#        print(self.type_str, Item.recursion)
        Item.recursion-=1



    def __repr__(self):

        my_repr = f'name: {self.name}, path: {self.path}, type: {self.type_str}, p size: {self.size}, s size: {self.ext_sec_size}'
        #\n\tuap_s {self.uap_s}, uap_i {self.uap_i}, ksy_id {self.ksy_id}, ksy_path {self.ksy_path}, ast_path {self.ast_path}, is_none {self.is_none}, is_spare {self.is_spare}, is_rfs {self.is_rfs}, is_fx {self.is_fx}, is_gray {self.is_gray}, has_items {self.has_items}'
        for i in self.sub_items:
            my_repr += f'\n    {i}'

        return my_repr

    @property
    def uap_i(self):
        match self.name:
            case "RE":
                return -4
            case "RFS":
                return -3
            case "SP":
                return -2
            case 'spare':
                return -1
            case None:
                return -1
            case _:
                return int(self.name)

    @property
    def uap_s(self):
        return 'spare' if self.is_none else (('i' if self.is_num else ('i_' if self.name in ("SP", "RE", "RFS") else ('' if self.is_fx or self.name == 'value' else 'si_' ))) + self.name.lower())

    @property
    def is_num(self):
        return self.name.isnumeric() if not self.is_none else False

    @property
    def ksy_id(self):
        return 'value' if self.is_none else (('i' if self.is_num else ('i_' if self.name in ("SP", "RE", "RFS") else ('' if self.is_fx or self.name == 'value' else 'si_' ))) + self.name.lower())

    @property
    def ksy_path(self):
        return '_'.join(self.path[1:]).lower()

    @property
    def ast_path(self):
        return '/'.join(self.path)

    @property
    def is_none(self):
        return not bool(self.name)
    
    @property
    def is_spare(self):
        return True if not self.is_none and self.name.startswith('spare') else False

    @property
    def is_rfs(self):
        return True if not self.is_none and self.name.startswith('RFS') else False

    @property
    def is_fx(self):
        return True if not self.is_none and self.name.startswith('fx') else False

    @property
    def is_gray(self):
        return True if not self.is_none and self.ast_path in ("001/100/MODEC", "020/100/MODEC", "048/100/MODEC") else False

    @property
    def has_items(self):
        return True if len(self.sub_items) > 0 else False

    def str_method(self, tabs=0, suffix:str=""):
        print(">>>>>", "STR_METHOD", self.type_str.lower(), self.name, self.content == None, "<<<<<")
        return getattr(Item, 'str_'+self.type_str.lower())(self, tabs, suffix)

    @classmethod
    def str_fixed(cls, item: 'Item', tabs:int = 0, suffix:str=""):
        #recorro el item para crear miembros de sub_type que tengan la longitud en bits dentro del
        #campo value

        print(">>>>>", "STR_FIXED", "<<<<<")
        selector_path = lambda a, b: next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))

        indent = ' '*2
        tab = indent*tabs
        templ_item_name = tab+indent+'sub_{ksy_path}{suffix}_t:\n\n' +\
                          tab+indent+'  instances:\n'  +\
                          tab+indent+'    name:\n' +\
                          tab+indent+'      value: \'"{name}"\'\n' +\
                          tab+indent+'    title:\n' +\
                          tab+indent+'      value: \'"{title}"\'\n\n'

        templ_content_table = tab+indent+'    table:\n' +\
                              tab+indent+'      value: |\n' +\
                              tab+indent+'        [\n' +\
                              tab+indent+'         {table_list}\n' +\
                              tab+indent+'        ]\n' +\
                              tab+indent+'    content:\n' +\
                              tab+indent+'      value: \'value.as<u1> < table.size ? table[value.as<u1>] : "Index Error"\'\n\n'
        
        templ_content_qty   = tab+indent+'    content:\n' +\
                              tab+indent+'      value: {content_value}\n\n' +\
                              tab+indent+'    signed_value:\n' +\
                              tab+indent+'      value: {content_signed_value}\n'+\
                              tab+indent+'    unit:\n' +\
                              tab+indent+'      value: \'\"{content_unit}\"\'\n\n'

        templ_seconds_qty   = tab+indent+'    hours:\n' +\
                              tab+indent+'      value: {hours_value}\n' +\
                              tab+indent+'    minutes:\n' +\
                              tab+indent+'      value: {minutes_value}\n' +\
                              tab+indent+'    seconds:\n' +\
                              tab+indent+'      value: {seconds_value}\n' +\
                              tab+indent+'    mseconds:\n' +\
                              tab+indent+'      value: {mseconds_value}\n\n'

        templ_grades_qty    = tab+indent+'    grades:\n' +\
                              tab+indent+'      value: {grades_value}\n' +\
                              tab+indent+'    minutes:\n' +\
                              tab+indent+'      value: {minutes_value}\n' +\
                              tab+indent+'    seconds:\n' +\
                              tab+indent+'      value: {seconds_value}\n' +\
                              tab+indent+'    dseconds:\n' +\
                              tab+indent+'      value: {dseconds_value}\n\n'

        templ_content_str   = tab+indent+'    string:\n' +\
                              tab+indent+'      value:  \'\"{string_format}\"\'\n\n'

        templ_content_gry   = tab+indent+'    is_gray:\n' +\
                              tab+indent+"      value: 'true'\n" +\
                              tab+indent+'    uscr_value:\n' +\
                              tab+indent+"      value: '((value>>7)&0o0001)+((value>>8)&0o0002)+((value>>9)&0o0004)+((value<<2)&0o0010)+((value<<1)&0o0020)+((value>>0)&0o0040)+((value>>0)&0o0100)+((value>>1)&0o0200)+((value>>2)&0o0400)+((value<<9)&0o1000)+((value<<8)&0o2000)'\n" +\
                              tab+indent+'    gray2dec:\n' +\
                              tab+indent+"      value: '[-1,0,2,1,4,-1,3,12]'\n" +\
                              tab+indent+'    ungray:\n' +\
                              tab+indent+'      type: ungrayf(uscr_value>>3, 0, 8)\n' +\
                              tab+indent+'    content:\n' +\
                              tab+indent+"      value: '((ungray.u.u.u.u.u.u.u.u.stop*5)+((ungray.u.u.u.u.u.u.u.u.stop&1) == 0 ? gray2dec[uscr_value&0b111] : 4 - gray2dec[uscr_value&0b111]))-12'\n\n" +\
                              tab+indent+'  types:\n\n' +\
                              tab+indent+'    ungrayf:\n' +\
                              tab+indent+'      params:\n' +\
                              tab+indent+'        - id: c\n' +\
                              tab+indent+'          type: b12\n' +\
                              tab+indent+'        - id: b\n' +\
                              tab+indent+'          type: b12\n' +\
                              tab+indent+'        - id: l\n' +\
                              tab+indent+'          type: u1\n\n' +\
                              tab+indent+'      instances:\n' +\
                              tab+indent+'        stop:\n' +\
                              tab+indent+'          value: b\n' +\
                              tab+indent+'          if: l == 0\n' +\
                              tab+indent+'        u:\n' +\
                              tab+indent+'          type: ungrayf(c, (b^(((b>>1)^c)&(1<<(l-1)))), l-1)\n' +\
                              tab+indent+'          if: l > 0\n\n'

        templ_content_int   = tab+indent+'    content:\n' +\
                              tab+indent+'      value: {content_value}\n\n'

        templ_item_seq  = tab+indent+'    - id: {it_name}\n' +\
                          tab+indent+'      {it_type}\n'

        templ_case_inst = tab+indent+'    {it_name}:\n'+\
                          tab+indent+'      type:\n'+\
                          tab+indent+"        switch-on: 'true'\n"+\
                          tab+indent+'        cases:\n'+\
                          tab+indent+'          {cases}\n'
    
        templ_case_seq   = tab+indent+'    - id: default_{it_name}\n' +\
                           tab+indent+'      type: sub_120_cc_cpc{it_size}\n'

        templ_item_types =  tab+indent+'  types:\n\n' +\
                            '{sub_items_types}'

        item_type_name = templ_item_name.format(ksy_path=(item.ksy_path), suffix=suffix, name=(item.name if not item.is_none else 'value'), title=item.title)

        item_content = ''
        item_case_instance = ''

        print(item.content, "En STR_FIXED")
        if item.content is not None:
            print(">>>>>", item.content.type, "<<<<<")
            match item.content.type:
                case 'ContentTable':
                    print(item.content.table)
                    item_content = templ_content_table.format(table_list = (',\n'+tab+indent+'         ').join(item.content.table))
                    print(item_content)

                case 'ContentQuantity':
                    item_content = templ_content_qty.format(content_value = item.content.value, content_signed_value=item.content.signed_value, content_unit=item.content.unit)
                    if item.content.unit == 's' and hasattr(item.content, 'hours_value'):
                        item_content += templ_seconds_qty.format( hours_value=item.content.hours_value, minutes_value=item.content.minutes_value, seconds_value=item.content.seconds_value, mseconds_value=item.content.mseconds_value)
                    if item.content.unit == '°' and hasattr(item.content, 'grades_value'):
                        item_content += templ_grades_qty.format( grades_value=item.content.grades_value, minutes_value=item.content.minutes_value, seconds_value=item.content.seconds_value, dseconds_value=item.content.dseconds_value)

                case 'ContentString':
                    item_content = templ_content_str.format(string_format = item.content.format)

                case 'ContentGray':
                    item_content = templ_content_gry

                case 'ContentInteger':
                    item_content = templ_content_int.format(content_value = item.content.value)

        item_type_seq = tab+indent+'  seq:\n'
        sub_items_types=''        

        if not item.has_items: 
            item_type_seq += templ_item_seq.format( it_name='value' , it_type=f'type: b{item.size}' )
        
        else: #entonces estamos en un grupo (type: Group), vamos a ver si algun sub_item, es dependent
            for i in item.sub_items:

                if not i.is_none:
                    if i.type_str == "Dependent":

                        selector_items=['.'.join(['_parent']*(len(item.path)-1)+[f'i{selector[0]}']+[f'si_{j.lower()}' for j in selector[1:]]+['value.as<u2>']) for selector in i.selectors ]
                        cases_ = [[f'=={case}' for case in c ] for c in i.cases[:-1]]
                        cases_selectors = [" and ".join(map("".join, zip(selector_items, case))) for case in cases_]
                        cases_types     = ["_".join(['sub',f'{item.ksy_path}', i.name.lower(), 'case']+[f'{case}' for case in j ]+[f't(default_{i.ksy_id}.value, {i.size}, 0)']) for j in i.cases[:-1]]
                        filler_cases = map(" and 1==1 : ".join, map(list, zip(cases_selectors, cases_types)))

                        item_type_name     += templ_case_inst.format( it_name=i.ksy_id, cases=('\n'+tab+indent+'          ').join(filler_cases) )
                        item_type_name     += tab+indent+'          '+f'_ : sub_{i.ksy_path}_default_t(default_{i.ksy_id}.value, {i.size}, 0)\n\n'

                        item_type_seq      += templ_item_seq.format( it_name=f'default_{i.ksy_id}', it_type=f'type: sub_{i.ksy_path}_t')
                        sub_items_types    += Item.str_dependent(i, 2+tabs )

                    else:
                        item_type_seq += templ_item_seq.format( it_name=i.ksy_id , it_type=f'type: sub_{i.ksy_path}_t')
                        sub_items_types += i.str_method(2+tabs)

            sub_items_types = templ_item_types.format(sub_items_types = sub_items_types)

        item_type_seq += '\n'
        return item_type_name+item_content+item_type_seq+sub_items_types

    @classmethod
    def str_explicit(cls, item: 'Item', tabs:int = 0, suffix:str=""):

        indent = ' '*2
        tab = indent*tabs
        templ_item_name = tab+indent+'sub_{ksy_path}{suffix}_t:\n\n' +\
                          tab+indent+'  instances:\n'  +\
                          tab+indent+'    name:\n' +\
                          tab+indent+'      value: \'"{name}"\'\n' +\
                          tab+indent+'    title:\n' +\
                          tab+indent+'      value: \'"{title}"\'\n\n' +\
                          tab+indent+'  seq:\n'
        
        item_subtype_seq =  tab + indent*3 + '- id: {nombre}\n'+\
                            tab + indent*3 + '  type: u1\n'+\
                            tab + indent*3 + '- id: value\n'+\
                            tab + indent*3 + '  size: {size}\n\n'

        return templ_item_name.format(ksy_path=(item.ksy_path), suffix=suffix , name=(item.name if not item.is_none else 'value'), title=item.title)+\
               item_subtype_seq.format(nombre=f'{item.ksy_id}_size' if not item.is_none else 'f_size', size=f'{item.ksy_id}_size - 1' if not item.is_none else 'f_size -1')

    @classmethod
    def str_extended(cls, item: 'Item', tabs:int = 0, suffix:str=""):#
        #Hay 2 tipo de Extended, los que tienen mas de un fx y los que solo
        #tienen un fx. En este ultimo caso se trata mas bien como repetitivo#

        indent = ' '*2
        tab = indent*tabs
        templ_item_name = tab+indent+'sub_{ksy_path}{suffix}_t:\n\n' +\
                          tab+indent+'  instances:\n'  +\
                          tab+indent+'    name:\n' +\
                          tab+indent+'      value: \'"{name}"\'\n' +\
                          tab+indent+'    title:\n' +\
                          tab+indent+'      value: \'"{title}"\'\n\n' +\
                          tab+indent+'  seq:\n'
        
        templ_type_repeat = tab + indent*3 + '- id: items\n' +\
                            tab + indent*3 + '  type: sub_{ksy_path}_t\n' +\
                            tab + indent*3 + '  repeat: until\n' +\
                            tab + indent*3 + '  repeat-until: not _.fx1\n\n' +\
                            tab + indent*2 + 'types:\n\n' +\
                            tab + indent*3 + 'sub_{ksy_path}_t:\n' +\
                            tab + indent*3 + '  seq:\n'

        templ_item_seq  = tab + indent*5 +'- id: {it_name}\n' +\
                          tab + indent*5 +'  type: {it_type}\n'

        templ_type_seq_id = tab + indent*5 + '- id: {name}\n' +\
                            tab + indent*5 + '  type: b{size}\n'
                            
        templ_type_seq_ids = tab + indent*3 + '- id: {it_name}\n' +\
                             tab + indent*3 + '  type: {it_type}\n' +\
                             '{condition}'

        templ_repeat_item_types = tab + indent*4 + 'types:\n\n' +\
                                                    '{sub_items_types}'

        templ_item_types =  tab+indent+'  types:\n\n' +\
                            '{sub_items_types}'

        item_type_seq_id = templ_item_name.format(ksy_path=item.ksy_path, suffix=suffix , name = item.name, title=item.title)
        sub_items_types=''        

        if item.ext_sec_size == 0:
            item_type_seq_id += templ_type_repeat.format(ksy_path=item.ksy_path)
#            for i in item.sub_items:
#                item_type_seq_id += templ_type_seq_id.format(name= i.ksy_id , size=i.size )

            for i in item.sub_items:
                if not i.is_none:
                    item_type_seq_id += templ_item_seq.format( it_name=i.ksy_id , it_type='b1' if i.is_fx else f'sub_{i.ksy_path}_t')
#            item_type_seq_id += '\n'

            sub_items_types=''        
            for i in item.sub_items:
#                if not i.is_none:
                sub_items_types += i.str_method(4+tabs)
            sub_items_types = templ_repeat_item_types.format(sub_items_types = sub_items_types)

#            item_type_seq_id +='\n'

        else: #item.ext_sec_size es distinto de cero, entonces tiene mas de un fx
            fx_flags = [] #contador de fx_bit
            for i in item.sub_items:
                item_type_seq_id += templ_type_seq_ids.format(it_name=i.ksy_id, \
                                                              it_type='b1' if i.is_fx else f'sub_{i.ksy_path}_t', \
                                                              condition = tab + indent*3 + ('  if: '+' and '.join(fx_flags)+'\n') if len(fx_flags) > 0 else '')
                fx_flags += [f'{i.name}'] if i.is_fx else []

            for i in item.sub_items:
                sub_items_types += i.str_method(2+tabs)

            sub_items_types = templ_item_types.format(sub_items_types = sub_items_types)

        item_type_seq_id +='\n'

        return item_type_seq_id+sub_items_types
    
    @classmethod
    def str_repetitive(cls, item: 'Item', tabs:int = 0, suffix:str=""):
        #recorro el item para crear miembros de sub_type
        #que tengan la longitud en bits dentro del
        indent = ' '*2
        tab = indent*tabs
        templ_item_name = tab + indent + 'sub_{ksy_path}{suffix}_t:\n\n' +\
                          tab + indent + '  instances:\n'  +\
                          tab + indent + '    name:\n' +\
                          tab + indent + '      value: \'"{name}"\'\n' +\
                          tab + indent + '    title:\n' +\
                          tab + indent + '      value: \'"{title}"\'\n\n' +\
                          tab + indent + '  seq:\n' +\
                          tab + indent + '    - id: num_{list_name}\n' +\
                          tab + indent + '      type: u1\n' +\
                          tab + indent + '    - id: {list_name}\n' +\
                          tab + indent + '      type: sub_{list_item}\n' +\
                          tab + indent + '      repeat: expr\n' +\
                          tab + indent + '      repeat-expr: num_{list_name}\n\n' +\
                          tab + indent + '  types:\n\n' +\
                          tab + indent + '    sub_{list_item}:\n' +\
                          tab + indent + '      seq:\n'

        templ_item_seq  = tab+indent+'        - id: {it_name}\n' +\
                          tab+indent+'          {it_type}\n'


        templ_item_types =  tab+indent+'      types:\n\n' +\
                            '{sub_items_types}'

        item_type_seq_id = templ_item_name.format( ksy_path = item.ksy_path, suffix=suffix, name = item.name, title=item.title,
#                    list_name =  ('items' if tabs == 0 else ('values' if item.is_none else f'{item.ksy_id}' + ('' if item.is_num else '_list'))), \
                    list_name =  (('values' if item.is_none else f'{item.ksy_id}_list')),
                    list_item =  (f'{item.ksy_id}_t' if tabs == 0 else f'{item.ksy_path}' + '_element_t')
                    )
        
        for i in item.sub_items:
            if not i.is_none:
                item_type_seq_id += templ_item_seq.format( it_name=i.ksy_id , it_type=f'type: sub_{i.ksy_path}_t')
        item_type_seq_id += '\n'

        sub_items_types=''        
        for i in item.sub_items:
            if not i.is_none:
                sub_items_types += i.str_method(4+tabs)
        sub_items_types = templ_item_types.format(sub_items_types = sub_items_types)

        item_type_seq_id +='\n'
        return  item_type_seq_id+sub_items_types

    @classmethod
    def str_compound(cls, item: 'Item', tabs:int = 0, suffix:str=""):

        indent = ' '*2
        tab = indent*tabs

        templ_item_name = indent + 'sub_{ksy_path}{suffix}_t:\n\n' +\
                          indent + '  instances:\n'  +\
                          indent + '    name:\n' +\
                          indent + '      value: \'"{name}"\'\n\n' +\
                          indent + '    title:\n' +\
                          indent + '      value: \'"{title}"\'\n' +\
                          indent + '  seq:\n' +\
                          indent + '    - id: fspec\n'+\
                          indent + '      type: field_spec({fspec_max_len})\n'

        temp_subtype_seq =  indent*3 + '- id: {name}\n'+\
                            indent*3 + '  type: sub_{ksy_path}_t\n'+\
                            indent*3 + '  if: fspec.octects.size > {oct_cnt} and fspec.flags[{flag_cnt}].flag\n'
        
        item_type_seq = templ_item_name.format(ksy_path=item.ksy_path, suffix=suffix, name=item.name, title=item.title, fspec_max_len = (len(item.sub_items)+6)//7)

        item_subtype_seq = ''
        it_c = 0 #contador de items
        for i in item.sub_items:
            if not i.is_none:
                item_subtype_seq += temp_subtype_seq.format(name=i.ksy_id, ksy_path=i.ksy_path, oct_cnt=it_c//7, flag_cnt=it_c)
            it_c += 1

        item_subtype_seq+='\n'
        item_subtype_types = indent*2 + 'types:\n\n'
        temp_subtype_types = '{item_str}'
        
        for i in item.sub_items:
            if i.is_spare:
                print("spare")
            if not i.is_none:
                item_subtype_types += temp_subtype_types.format(item_str=i.str_method(2))

        return item_type_seq+item_subtype_seq+item_subtype_types

    @classmethod
    def str_dependent(cls, item: 'Item', tabs:int = 0, suffix:str=""):
        #recorro el item para crear miembros de sub_type que tengan la longitud en bits dentro del
        #campo value

        indent = ' '*2
        tab = indent*tabs

        templ_item_name = tab+indent+'sub_{ksy_path}{suffix}_t:\n\n' +\
                          tab+indent+'  params:\n'  +\
                          tab+indent+'    - id: default\n'  +\
                          tab+indent+'      type: u4\n'  +\
                          tab+indent+'    - id: size\n'  +\
                          tab+indent+'      type: u1\n'  +\
                          tab+indent+'    - id: shift\n'  +\
                          tab+indent+'      type: u1\n\n'  +\
                          tab+indent+'  instances:\n'  +\
                          tab+indent+'    name:\n' +\
                          tab+indent+'      value: \'"{name}"\'\n' +\
                          tab+indent+'    title:\n' +\
                          tab+indent+'      value: \'"{title}"\'\n\n'

        templ_content_table = tab+indent+'    table:\n' +\
                              tab+indent+'      value: |\n' +\
                              tab+indent+'        [\n' +\
                              tab+indent+'         {table_list}\n' +\
                              tab+indent+'        ]\n' +\
                              tab+indent+'    content:\n' +\
                              tab+indent+'      value: \'value.as<u1> < table.size ? table[value.as<u1>] : "Index Error"\'\n\n'
        
        templ_content_qty   = tab+indent+'    content:\n' +\
                              tab+indent+'      value: {content_value}\n\n' +\
                              tab+indent+'    signed_value:\n' +\
                              tab+indent+'      value: {content_signed_value}\n'+\
                              tab+indent+'    unit:\n' +\
                              tab+indent+'      value: \'\"{content_unit}\"\'\n\n'

        templ_seconds_qty   = tab+indent+'    hours:\n' +\
                              tab+indent+'      value: {hours_value}\n' +\
                              tab+indent+'    minutes:\n' +\
                              tab+indent+'      value: {minutes_value}\n' +\
                              tab+indent+'    seconds:\n' +\
                              tab+indent+'      value: {seconds_value}\n' +\
                              tab+indent+'    mseconds:\n' +\
                              tab+indent+'      value: {mseconds_value}\n\n'

        templ_grades_qty    = tab+indent+'    grades:\n' +\
                              tab+indent+'      value: {grades_value}\n' +\
                              tab+indent+'    minutes:\n' +\
                              tab+indent+'      value: {minutes_value}\n' +\
                              tab+indent+'    seconds:\n' +\
                              tab+indent+'      value: {seconds_value}\n' +\
                              tab+indent+'    dseconds:\n' +\
                              tab+indent+'      value: {dseconds_value}\n\n'

        templ_content_str   = tab+indent+'    string:\n' +\
                              tab+indent+'      value:  \'\"{string_format}\"\'\n\n'

        templ_content_gry   = tab+indent+'    is_gray:\n' +\
                              tab+indent+"      value: 'true'\n" +\
                              tab+indent+'    uscr_value:\n' +\
                              tab+indent+"      value: '((value>>7)&0o0001)+((value>>8)&0o0002)+((value>>9)&0o0004)+((value<<2)&0o0010)+((value<<1)&0o0020)+((value>>0)&0o0040)+((value>>0)&0o0100)+((value>>1)&0o0200)+((value>>2)&0o0400)+((value<<9)&0o1000)+((value<<8)&0o2000)'\n" +\
                              tab+indent+'    gray2dec:\n' +\
                              tab+indent+"      value: '[-1,0,2,1,4,-1,3,12]'\n" +\
                              tab+indent+'    ungray:\n' +\
                              tab+indent+'      type: ungrayf(uscr_value>>3, 0, 8)\n' +\
                              tab+indent+'    content:\n' +\
                              tab+indent+"      value: '((ungray.u.u.u.u.u.u.u.u.stop*5)+((ungray.u.u.u.u.u.u.u.u.stop&1) == 0 ? gray2dec[uscr_value&0b111] : 4 - gray2dec[uscr_value&0b111]))-12'\n\n" +\
                              tab+indent+'  types:\n\n' +\
                              tab+indent+'    ungrayf:\n' +\
                              tab+indent+'      params:\n' +\
                              tab+indent+'        - id: c\n' +\
                              tab+indent+'          type: b12\n' +\
                              tab+indent+'        - id: b\n' +\
                              tab+indent+'          type: b12\n' +\
                              tab+indent+'        - id: l\n' +\
                              tab+indent+'          type: u1\n\n' +\
                              tab+indent+'      instances:\n' +\
                              tab+indent+'        stop:\n' +\
                              tab+indent+'          value: b\n' +\
                              tab+indent+'          if: l == 0\n' +\
                              tab+indent+'        u:\n' +\
                              tab+indent+'          type: ungrayf(c, (b^(((b>>1)^c)&(1<<(l-1)))), l-1)\n' +\
                              tab+indent+'          if: l > 0\n\n'

        templ_content_int   = tab+indent+'    content:\n' +\
                              tab+indent+'      value: {content_value}\n\n'



        templ_def_name  = tab+indent+'sub_{ksy_path}_t:\n\n' +\
                          tab+indent+'  instances:\n'  +\
                          tab+indent+'    name:\n'  +\
                          tab+indent+"      value: '\"{it_name}\"'\n"  +\
                          tab+indent+'    title:\n'  +\
                          tab+indent+"      value: '\"{it_title}\"'\n"  +\
                          tab+indent+'  seq:\n'  +\
                          tab+indent+'    - id: value\n'  +\
                          tab+indent+'      type: b{it_size}\n'  +\
                          tab+indent+'sub_{ksy_path}_default_t:\n'  +\
                          tab+indent+'  params:\n'  +\
                          tab+indent+'    - id: default\n'  +\
                          tab+indent+'      type: u4\n'  +\
                          tab+indent+'    - id: size\n'  +\
                          tab+indent+'      type: u1\n'  +\
                          tab+indent+'    - id: shift\n'  +\
                          tab+indent+'      type: u1\n'  +\
                          tab+indent+'  instances:\n'  +\
                          tab+indent+'    name:\n'  +\
                          tab+indent+"      value: '\"{it_name}\"'\n"  +\
                          tab+indent+'    title:\n'  +\
                          tab+indent+"      value: '\"{it_title}\"'\n"  +\
                          tab+indent+'    table:\n'  +\
                          tab+indent+'      value: |\n'  +\
                          tab+indent+'        [\n'  +\
                          tab+indent+'        "Invalid Case values",\n'  +\
                          tab+indent+'        ]\n'  +\
                          tab+indent+'    content:\n'  +\
                          tab+indent+"      value: 'value.as<u1> < table.size ? table[value.as<u1>] : \"Invalid Case values\"'\n"  +\
                          tab+indent+'    value:\n'  +\
                          tab+indent+"      value: '(default >> shift) & ((1<<size)-1)'\n" +\
                          tab+indent+'  seq:\n' +\
                          tab+indent+'    - id: dummy\n' +\
                          tab+indent+'      type: b0\n'



        templ_case_name = tab+indent+'{case_type}:\n\n' +\
                          tab+indent+'  params:\n'  +\
                          tab+indent+'    - id: default\n'  +\
                          tab+indent+'      type: u4\n'  +\
                          tab+indent+'    - id: size\n'  +\
                          tab+indent+'      type: u1\n'  +\
                          tab+indent+'    - id: shift\n'  +\
                          tab+indent+'      type: u1\n\n'  +\
                          tab+indent+'  instances:\n'  +\
                          tab+indent+'    name:\n' +\
                          tab+indent+'      value: \'"{name}"\'\n' +\
                          tab+indent+'    title:\n' +\
                          tab+indent+'      value: \'"{title}"\'\n\n'

        templ_case_seq  = tab+indent+'    value:\n' +\
                          tab+indent+"      value: '(default >> shift) & ((1<<size)-1)'\n" +\
                          tab+indent+'  seq:\n' +\
                          tab+indent+'    - id: dummy\n' +\
                          tab+indent+'      type: b0\n'

        templ_case_sel   = tab+indent+'          {case}'

        templ_item_seq  = tab+indent+'    {it_name}:\n' +\
                          tab+indent+'      type: {it_type}(default, {p_size}, {p_shift})\n'

        item_type_name = ''
#        if hasattr(item, 'cases'): #llamado desde str_fixed, armo type para lectura, default_type, y la lista de types para cada caso
        if item.cases: #llamado desde str_fixed, armo type para lectura, default_type, y la lista de types para cada caso
            print(len(item.cases), item.cases, item.content)
            item_type_name += templ_def_name.format(ksy_path=item.ksy_path,  it_name=(item.name if not item.is_none else 'value'), it_title=item.title, it_size=item.size)
            cases_types = ["_".join(['sub',f'{item.ksy_path}', 'case']+[f'{case}' for case in j ]+['t']) for j in item.cases[:-1]]

            for i, case_type in enumerate(cases_types):
                print("ESTOY EN STR_DEPENDENT RECORRIENDO CONTENTS")
                item_type_name += templ_case_name.format(case_type=case_type,  name=(item.name if not item.is_none else 'value'), title=item.title)
                item_content = ''
                sub_items_types = ''
                content = item.contents[i]
                if isinstance(content, Content):
                    print(">>>>> contents[i] es Content <<<<<")
                    match content.type:
                        case 'ContentTable':
                            item_content += templ_content_table.format(table_list = (',\n'+tab+indent+'         ').join(content.table))

                        case 'ContentQuantity':
                            item_content += templ_content_qty.format(content_value = content.value, content_signed_value=content.signed_value, content_unit=content.unit)
                            if content.unit == 's' and hasattr(content, 'hours_value'):
                                item_content += templ_seconds_qty.format( hours_value=content.hours_value, minutes_value=content.minutes_value, seconds_value=content.seconds_value, mseconds_value=content.mseconds_value)
                            if content.unit == '°' and hasattr(content, 'grades_value'):
                                item_content += templ_grades_qty.format( grades_value=content.grades_value, minutes_value=content.minutes_value, seconds_value=content.seconds_value, dseconds_value=content.dseconds_value)

                        case 'ContentString':
                            item_content += templ_content_str.format(string_format = content.format)

                        case 'ContentGray':
                            item_content += templ_content_gry

                        case 'ContentInteger':
                            item_content += templ_content_int.format(content_value = content.value)

                    item_content += templ_case_seq.format(size=item.size)

                elif isinstance(content, list):
                    print(">>>>> contents[i] es una lista <<<<<")
                    sub_items_types  = '\n'
                    sub_items_types  = tab+indent+f'  types:\n\n'
                    si:Item
                    p_shift = 0
                    for k, si in enumerate(content):
                        item_content    += templ_item_seq.format(it_name= f'si_{si.name.lower()}', it_type=f'sub_{si.ksy_path}_t', p_size=si.size, p_shift=p_shift )
                        p_shift+=si.size
                        sub_items_types += f'{Item.str_dependent(si, 2+tabs)}'

                    item_content += '\n'
                    item_content += sub_items_types+'\n'

                item_type_name+=item_content

        else: #llamado desde str_dependent, y por tanto debo rellenar el tipo si tiene content o armar un spare
            if not item.is_none:
                item_content = ''
                item_type_name = templ_item_name.format(ksy_path=(item.ksy_path), suffix=suffix, name=(item.name if not item.is_none else 'value'), title=item.title)
                if isinstance(item.content, Content):
#                if hasattr(item, 'content'):#, Content):
                    match item.content.type:
                        case 'ContentTable':
                            item_content += templ_content_table.format(table_list = (',\n'+tab+indent+'         ').join(item.content.table))

                        case 'ContentQuantity':
                            item_content += templ_content_qty.format(content_value = item.content.value, content_signed_value=item.content.signed_value, content_unit=item.content.unit)
                            if item.content.unit == 's' and hasattr(item.content, 'hours_value'):
                                item_content += templ_seconds_qty.format( hours_value=item.content.hours_value, minutes_value=item.content.minutes_value, seconds_value=item.content.seconds_value, mseconds_value=item.content.mseconds_value)
                            if content.unit == '°' and hasattr(content, 'grades_value'):
                                item_content += templ_grades_qty.format( grades_value=item.content.grades_value, minutes_value=item.content.minutes_value, seconds_value=item.content.seconds_value, dseconds_value=item.content.dseconds_value)

                        case 'ContentString':
                            item_content += templ_content_str.format(string_format = item.content.format)

                        case 'ContentGray':
                            item_content += templ_content_gry

                        case 'ContentInteger':
                            item_content += templ_content_int.format(content_value = item.content.value)

                item_content += templ_case_seq.format(size=item.size)
                item_type_name+=item_content

#                else:
#                seq:
#                  - id: value
#                    type: b2



        return item_type_name+'\n'
        return item_type_name+item_content+'\n'


#                sub_items_types    += Item.str_dependent(i, 2+tabs,  "_".join(['','case']+[f'{case}' for case in j]))
#        selector_items=['.'.join(['_parent']*(len(item.path)-1)+[f'i{selector[0]}']+[f'si_{i.lower()}' for i in selector[1:]]+['value.as<u2>']) for selector in item.selectors ]
#        cases_ = [[f'=={case}' for case in c ] for c in item.cases[:-1]]
#        cases_selectors = [" and ".join(map("".join, zip(selector_items, case))) for case in cases_]
#        cases_types     = ["_".join(['sub',f'{item.ksy_path}', 'case']+[f'{case}' for case in j ]+['t']) for j in item.cases[:-1]]
#        filler_cases = map(" : ".join, map(list, zip(cases_selectors, cases_types)))
#        item_type_name +=  "\n".join([templ_case_sel.format(case=case) for case in filler_cases])+'\n\n'
#                item_type_name += tab+indent+'  types:\n'
#                if hasattr(item, 'contents'):
#                    for i, content in enumerate(item.contents[:-1]):
#            #            item_content += templ_case_name.format(case_type=cases_types[i] , name=(item.name if not item.is_none else 'value'), title=item.title)




#                    item_content    += tab+indent+'      seq:\n'


    def __str__(self):
        print("En Item.__str__", self.name)
        return self.str_method()
