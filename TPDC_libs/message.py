# Copyright (C) 2016, see AUTHORS.md
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import struct
# define bit parameters
relay  = 0x01
power  = 0x02
reset  = 0x04
analog = 0x10
ctrl   = 0x20
profBus= 0x40
disp   = 0x80 
# custom functions
def a2i(number):
    if isinstance(number, str):
        return int(number, 16)
    elif isinstance(number, int):
        return number
    else:
        raise ValueError('Unknown number type')
      

# %% ------ Message = RS232-framedefinition -------------

class Message(object):
    def __init__(self):
        self.do_allocate(23)
        self.set_length(0)
        self.set_command(0x6040)
        self.bits_state = 0
        
    def do_allocate(self, length):
        self.msg = length*[0]
        
    def set_length(self, number):
        self.msg[0] = a2i(number)
        self.msg[1] = (~ a2i(number)) & 0xff
        
    def set_destination(self, dest):
        self.msg[3] = dest & 0xff
        self.msg[2] = dest >> 8 & 0xff
    
    def get_destination(self):
        return self.msg[2] << 8 | self.msg[3]
        
    def set_source(self, src):
        self.msg[5] = src & 0xff
        self.msg[4] = src >> 8 & 0xff
        
    def get_source(self):
        return self.msg[4] << 8 | self.msg[5]
        
    def set_command(self, cmd):
        self.msg[7] = cmd & 0xff
        self.msg[6] = cmd >> 8 & 0xff
        
    def get_command(self):
        return self.msg[6] << 8 | self.msg[7]
    
    def set_voltage(self, number):
        self.msg[8:12] = list(struct.pack("<f", float(number)))
        
    def get_voltage(self, resp_msg):
        pos = 10
        b_str = resp_msg[pos] + resp_msg[pos+1] + resp_msg[pos+2] + resp_msg[pos+3]
        return struct.unpack('<f', b_str)[0]
    
    def set_current(self, number):
        self.msg[12:16] = list(struct.pack("<f", float(number)))
        
    def get_current(self, resp_msg):
        pos = 14
        b_str = resp_msg[pos] + resp_msg[pos+1] + resp_msg[pos+2] + resp_msg[pos+3]
        return struct.unpack('<f', b_str)[0]
    
    def set_power(self, number):
        self.msg[16:20] = list(struct.pack("<f", float(number)))
        
    def get_power(self, resp_msg):
        pos = 18
        b_str = resp_msg[pos] + resp_msg[pos+1] + resp_msg[pos+2] + resp_msg[pos+3]
        return struct.unpack('<f', b_str)[0]
    
    def get_arc_Im_count(self, resp_msg):
        pos = 25
        return int.from_bytes(resp_msg[pos] + resp_msg[pos+1], byteorder='big')
    
    def get_arc_UxI_count(self, resp_msg):
        pos = 27
        return int.from_bytes(resp_msg[pos] + resp_msg[pos+1], byteorder='big')
    
    def get_arc_dU_count(self, resp_msg):
        pos = 29
        return int.from_bytes(resp_msg[pos] + resp_msg[pos+1], byteorder='big')
        
    def set_bits(self, number):
        self.msg[20] = int(number) & 0xff
        
    def power_on(self):
        self.bits_state |= power 
        self.msg[20] = int(self.bits_state) & 0xff
        
    def power_off(self):
        self.bits_state &= ~power
        self.msg[20] = int(self.bits_state) & 0xff
        
    def relay_on(self):
        self.bits_state |= relay 
        self.msg[20] = int(self.bits_state) & 0xff
        
    def relay_off(self):
        self.bits_state &= ~relay
        self.msg[20] = int(self.bits_state) & 0xff
        
    def add_parameter(self, number):
        self.msg.append(number & 0xff)
        
    def get_parameter(self, index):
        return self.msg[index]
    
    def get_length(self):
        return len(self.msg)
        
    def compute_crc(self):
        return sum(self.msg[2:]) & 0xffff
        
    def finish(self):
        crc = self.compute_crc()
        self.msg[len(self.msg)-2] = crc >> 8 & 0xff
        self.msg[len(self.msg)-1] = crc & 0xff
        self.set_length(len(self.msg))
    
    def __str__(self):
        return " ".join(map(hex, self.msg))    
    
# %% ------- test the funcionality ------
"""        
frame = Message()
frame.set_destination(0xFFFF)
frame.set_source(0x0000)
frame.set_voltage(50.5)
frame.set_current(0.100)
frame.set_power(30)
frame.power_on()
frame.finish()

print (frame.msg)
print (frame.__str__())

print ('-----------')
print (list(struct.pack("!f", 50.5)))
print (list(struct.pack("!f", 0.1)))
print (list(struct.pack("!f", 30)))
"""