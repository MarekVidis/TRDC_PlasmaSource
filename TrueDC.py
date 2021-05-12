# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27
@author: marekvidis@gmail.com
"""

# custom modules

# core GUI libraries
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow

import sys
import serial
import time
from TPDC_libs import message

class App(QMainWindow):  # create the main window

    ui_layout = 'C:\\TrueDC\\TrueDC_layout.ui'
    # load Qt designer XML .ui GUI file
    Ui_MainWindow, QtBaseClass = uic.loadUiType(ui_layout)    

    def __init__(self):  # initialize application
        super(App, self).__init__()
        self.ui = App.Ui_MainWindow()
        self.ui.setupUi(self)
        self.move(150, 150)  # set initial position of the window
        self.serial_port = serial.Serial(
        port=None,
        baudrate=38400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE
        )

        # create timer which updates fields on GUI (set interval in ms)
        self.loop_period = 1000
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.main_loop)
        self.timer.start(self.loop_period)
        
        # ramp variables
        self.P_inc = 0
        self.U_inc = 0
        self.I_inc = 0
        self.P_act = self.ui.P_setpoint.value()
        self.U_act = self.ui.U_setpoint.value()
        self.I_act = self.ui.I_setpoint.value()
        
        self.power_dict = {
            'act': self.P_act,
            'set': self.ui.P_setpoint,
            'rmp': self.ui.P_ramp,
            'inc': self.I_inc
            }
        self.voltage_dict = {
            'act': self.U_act,
            'set': self.ui.U_setpoint,
            'rmp': self.ui.U_ramp,
            'inc': self.U_inc
            }
        self.current_dict = {
            'act': self.I_act,
            'set': self.ui.I_setpoint,
            'rmp': self.ui.I_ramp,
            'inc': self.I_inc
            }
        
        self.p_dict = {
            'power': self.power_dict,
            'voltage': self.voltage_dict,
            'current': self.current_dict
            }

        # assign functions to top menu items
        # example: self.ui.MENU_ITEM_NAME.triggered.connect(self.FUNCTION_NAME)
        # system menu items
        self.ui.open_serial.clicked.connect(self.OpenSerial)
        self.ui.close_serial.clicked.connect(self.CloseSerial)
        self.ui.power_butt.clicked.connect(self.main_loop)
        self.ui.loop_period.valueChanged.connect(self.updateTimer)
        # ramp calculation events
        self.ui.P_setpoint.valueChanged.connect(self.calc_inc)
        self.ui.U_setpoint.valueChanged.connect(self.calc_inc)
        self.ui.I_setpoint.valueChanged.connect(self.calc_inc)
        self.ui.P_ramp.valueChanged.connect(self.calc_inc)
        self.ui.U_ramp.valueChanged.connect(self.calc_inc)
        self.ui.I_ramp.valueChanged.connect(self.calc_inc)
        #self.ui.U_ramp.valueChanged.connect(self.calc_ramp)
        #self.ui.file_quit.triggered.connect(self.quit_app)

# %% ----------- system control functions ------------------------------

    def main_loop(self):
        # Main loop to execute which keeps the app running.
        
        # build the message frame
        frame = message.Message()
        frame.set_destination(0xFFFF)
        frame.set_source(0x0000)
        frame.set_voltage(self.U_act)
        frame.set_current(self.ui.I_setpoint.value()*1000)
        frame.set_power(self.ui.P_setpoint.value())
        if self.ui.power_butt.isChecked():
            frame.power_on()
            frame.relay_on()
        else:
            frame.power_off()
            frame.relay_off()
        frame.finish()
        # %% ------ If port open do following
        if self.serial_port.is_open:
            self.update_parameters()
            self.serial_port.write(frame.msg)
            #self.ui.output_box.append('>> ' + str(frame.msg))
            time.sleep(0.1)
            resp = []
            while self.serial_port.inWaiting() > 0:
                resp.append(self.serial_port.read(1))
            #print (resp)
            #self.ui.output_box.append(str(resp))

            if len(resp) > 8:
               self.ui.ACK_byte_1.setValue(ord(resp[6]))
               self.ui.ACK_byte_2.setValue(ord(resp[7]))
               if resp[6] == b'@' and resp[7] == b'\x00':
                   self.ui.ACK_value.setText('OK')
               else:
                   self.ui.ACK_value.setText('Fault')
                    
               self.ui.U_act.setValue(frame.get_voltage(resp))
               self.ui.I_act.setValue(frame.get_current(resp))
               self.ui.P_act.setValue(frame.get_power(resp))
                
               self.ui.arc_Im_count.setValue(frame.get_arc_Im_count(resp))
               self.ui.arc_UxI_count.setValue(frame.get_arc_Im_count(resp))
               self.ui.arc_dU_count.setValue(frame.get_arc_Im_count(resp))
               

            
    # %% ---------- End of communication part
        
    def calc_inc(self):
        loop_dt = 0.001*self.ui.loop_period.value()
        for par in ('power','voltage','current'):
            p_act = self.p_dict[par]['act']
            p_set = self.p_dict[par]['set'].value()
            p_rmp = self.p_dict[par]['rmp'].value()
            direction = 1
            if p_set - p_act > 0: direction = 1
            if p_set - p_act < 0: direction =-1
            if p_set - p_act ==0: direction = 0
            self.p_dict[par]['inc'] = p_rmp * loop_dt * direction
        
            print (par+'_inc = %f' %(self.p_dict[par]['inc']))
            print (par+'_delta = %f' %(p_set - p_act))
        
    def update_parameters(self):
        for par in ('power','voltage','current'):
            
            self.p_dict[par]['act'] += self.p_dict[par]['inc']
            
            if self.p_dict[par]['act'] >= self.p_dict[par]['set'].value() and self.p_dict[par]['inc'] > 0:
               self.p_dict[par]['act'] = self.p_dict[par]['set'].value()
               self.p_dict[par]['inc'] = 0
            if self.p_dict[par]['act'] <= self.p_dict[par]['set'].value() and self.p_dict[par]['inc'] < 0:
               self.p_dict[par]['act'] = self.p_dict[par]['set'].value()
               self.p_dict[par]['inc'] = 0
                           
        print ('P_act: %f, P_inc: %f, U_act: %f, U_inc: %f, I_act: %f, I_inc: %f' 
               %(self.p_dict['power']['act'], self.p_dict['power']['inc'],
                 self.p_dict['voltage']['act'], self.p_dict['voltage']['inc'],
                 self.p_dict['current']['act'], self.p_dict['current']['inc']))
        

    def OpenSerial(self):
        com_port = self.ui.com_port.text()
        self.serial_port = serial.Serial(
        port=com_port,
        baudrate=38400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE
        )
        if self.serial_port.isOpen(): self.ui.output_box.append('Port '+com_port+' opened')
        else: self.ui.output_box.append('Error in opening '+com_port)
        
    def CloseSerial(self):
        self.serial_port.close()
        self.ui.output_box.append('Serial port closed')
        
    def updateTimer(self):
        self.timer.setInterval(self.ui.loop_period.value())
        self.calc_inc()
        
    def quit_app(self):
        # quit the application
        self.serial_port.close()
        self.timer.stop()  # stop timer
        self.close()  # close app window
        sys.exit()  # kill python kernel

# %% -------------------------- run application ----------------------------

if __name__ == '__main__':
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()

    window = App()
    window.show()
    sys.exit(app.exec_())
