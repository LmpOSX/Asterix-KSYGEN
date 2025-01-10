import sys
from typing import *

class Content:
    def __init__(self, content, size=0):

        self.type = content['tag']
        print(self.type)

        self.size = size

        match self.type:
            case 'ContentTable':
                print(self.type)
                self.dict = {numero: cadena for numero, cadena in content['contents']}
                print(self.dict)
                self.table:List[str] = []
#                for i in range(0, max(self.dict.keys())+1):
                for i in range(0, 1<<self.size):
                    if i in self.dict:
                        self.table.append("\""+self.dict[i]+"\"")
                    else:
                        self.table.append("\"N/D\"")
                print(self.table)

            case 'ContentQuantity':
                print(self.type)
                self.unit = content['contents']['unit']
                print (self.unit)

                if content['contents']['lsb']['tag'] in ('NumDiv', 'NumInt'):
                    self.signed_value = f"'((value >> {self.size-1}).as<bool> ? - ((value ^ 0b{'1'*self.size}) +1 ) : value)'" if content['contents']['signedness']['tag']=="Signed" else "value"
                else:
                    self.signed_value = "value"
                print(self.signed_value)

                if content['contents']['lsb']['tag'] == 'NumDiv':

                    if content['contents']['lsb']['contents']['numerator']['tag'] == 'NumInt':
                        numerator = content['contents']['lsb']['contents']['numerator']['contents']

                    if content['contents']['lsb']['contents']['denominator']['tag'] == 'NumInt':
                        denominator = content['contents']['lsb']['contents']['denominator']['contents']

                    elif content['contents']['lsb']['contents']['denominator']['tag'] == 'NumPow':
                        denominator = f" (1 << {content['contents']['lsb']['contents']['denominator']['contents']['exponent']})"

#                    self.value = (f"'((value >> {self.size-1}).as<bool> ? -((value ^ 0b{'1'*self.size}) +1 ) : value)" if content['signed'] else "'value") + f" * ({numerator}.0 / {denominator})'" 
                    self.value = "'signed_value" + f" * ({numerator}.0 / {denominator})'" 
                    print(self.value)
                elif content['contents']['lsb']['tag'] == 'NumInt':
                    numerator=1
                    denominator=1
                    self.value = (f"'((value >> {self.size-1}).as<bool> ? -((value ^ 0b{'1'*self.size}) +1 ) : value)" if content['signed'] else "'value") + f" * {content['lsb']['value']}'"
                    self.value = "'signed_value" + f" * {content['contents']['lsb']['contents']}.0'"
                    print(self.value)
                else:
                    self.value = ''

                if True:
                    if self.unit == 's':
                        self.hours_value    = f"'(({numerator}*value)/{denominator})/(3600)'"
                        self.minutes_value  = f"'((({numerator}*value)/{denominator})-(hours*3600))/60'"
                        self.seconds_value  = f"'(({numerator}*value)/{denominator})-(hours*3600+minutes*60)'"
                        self.mseconds_value = f"'1000*(value-(({denominator}/{numerator})*(hours*3600+minutes*60+seconds)))/({denominator}/{numerator})'"
                        print(self.hours_value)
                    if self.unit == '°':
                        self.grades_value   = "content"
                        self.minutes_value  = "'((content*(content > 0 ? 1:-1))%1)*60'" #)/{denominator})/60'"
                        self.seconds_value  = "'((((content*(content > 0 ? 1:-1))%1)*60)%1)*60'"
                        self.dseconds_value = 0#f"'((((((({numerator}*signed_value)-(grades*{denominator}))*60)%{denominator})*60)%{denominator})*1000)/{denominator}'"

                else:
                    if self.unit == 's':
                        self.hours_value    = f"'(({numerator}*value)/{denominator})/(3600)'"
                        self.minutes_value  = f"'((({numerator}*value)/{denominator})-(hours*3600))/60'"
                        self.seconds_value  = f"'(({numerator}*value)/{denominator})-(hours*3600+minutes*60)'"
                        self.mseconds_value = f"'1000*(value-(({denominator}/{numerator})*(hours*3600+minutes*60+seconds)))/({denominator}/{numerator})'"

                    if self.unit == '°':
                        self.grades_value    = f"'(({numerator}*value)/{denominator})'"#/(3600)'"
                        self.minutes_value  = f"'(({numerator}*value)%{denominator})*60/{denominator}'" #)/{denominator})/60'"
                        self.seconds_value  = f"'((((({numerator}*value)-(grades*{denominator}))*60)%{denominator})*60)/{denominator}'" #f"'(({numerator}*value)%{denominator})%60'"
                        self.dseconds_value = f"'((((((({numerator}*value)-(grades*{denominator}))*60)%{denominator})*60)%{denominator})*1000)/{denominator}'"

            case 'ContentString':
                print(self.type)
                self.format = content['contents']['tag'].replace("String", "")
                print(self.format)
            
            case 'ContentInteger':
                print(self.type, content['contents']['signedness']['tag'])
                self.value = (f"'((value >> {self.size-1}).as<bool> ? -((value ^ 0b{'1'*self.size}) +1 ) : value)'") if content['contents']['signedness']['tag']=="Signed" else "value"
                print(self.value)