#!/usr/bin/python

# VERSION 0.8.0

from __future__ import print_function
import struct
import os
import shutil
import pymodbus.client.sync
import binascii
import time
import sys
import json
import paho.mqtt.client as mqtt
import configparser
import logging

class MyConfig:
  def __init__(self,fpath) :
    self.configfile = fpath
    logging.info(" Init Config file %s " % self.configfile ) 
    self.cf_file_init()
    self.cf_load()
    
  def cf_file_init(self) : 
    if os.path.isfile(self.configfile):
      logging.info(" Config file found")
    else:
      logging.warning(" Config file not found, place a default config.ini; Please adapt it !")
      shutil.copyfile('config.default.ini',self.configfile)
  
  def get_config(self,key,value):
    return self.config[key][value]
   
  def cf_load(self) :
    self.config = configparser.ConfigParser()
    self.config.read(self.configfile)
    self.mqtt_user     = self.config['MQTT']['User']
    self.mqtt_pass     = self.config['MQTT']['Pass']
    self.mqtt_host     = self.config['MQTT']['Server']
    self.mqtt_port     = int(self.config['MQTT']['Port'])
    self.mqtt_topic    = self.config['MQTT']['Topic']
    self.usb_device    = self.config['DEFAULT']['UsbDevice']
    self.log_level     = self.config['DEFAULT']['LogLevel']


class MyMqtt:
  def __init__(self,cfg):
    logging.info(" Init MQTT ") 
    self.config = cfg
    self.mqtt_connect()   
    logging.info(" Loaded registers from config : ")
    self.cfgregs = json.loads(self.config.get_config("REGISTERS","Registers"))
    logging.info(self.cfgregs)
   
  def on_connect(self, client, userdata, flags, rc):
    logging.info(" MQTT reconnect with result code %s" % rc) 
  
  def on_disconnect(self, client, userdata, rc):
    logging.warning(" MQTT disconneceted with result code %s" % rc) 
    
  def mqtt_connect(self) :
    logging.info(" Connecting to MQTT with user : " + self.config.mqtt_user) 
    self.client = mqtt.Client("P1", clean_session=False)
    self.client.username_pw_set(username=self.config.mqtt_user,password=self.config.mqtt_pass)
    self.client.connect( self.config.mqtt_host , self.config.mqtt_port ) #connect to broker
    self.client.on_disconnect = self.on_disconnect
    self.client.on_connect    = self.on_connect
    self.client.loop_start()
    
  def publish(self,values) :
    self.client.publish(self.config.mqtt_topic,json.dumps(values))

class MyModbus(MyMqtt):
  def modbus_init(self) :
    logging.info(" Connecting to modbus on device %s" % self.config.usb_device);
    self.cl     = pymodbus.client.sync.ModbusSerialClient('rtu', port=self.config.usb_device, baudrate=9600, parity='N',stopbits=2, timeout=0.125)
    
  def set_regs(self) :
    print("a")

  def read_float_reg(self, client, basereg, unit=1) :
    resp = client.read_input_registers(basereg,2, unit=1)   
    if resp == None :
      return None
      # according to spec, each pair of registers returned
      # encodes a IEEE754 float where the first register carries
      # the most significant 16 bits, the second register carries the 
      # least significant 16 bits.
    return struct.unpack('>f',struct.pack('>HH',*resp.registers))
    
  def format_output(self, regfmt, val) :
    outformat = "%12."+str(regfmt[2])+"f"
    if val is None :
      return '.'*len(outformat%(0))
    return outformat%(val)  
    
  def read_modbusdata(self) :
    pValues = {}
    N=0
    while True :
      N += 1

      # PRINTING HEADERS      
      if N % 32 == 1 :
          headstr = '[        Date        ]'
          for x in self.cfgregs:
              headstr += '[%10s]' % x[0].center(6)
          logging.info(headstr)
          
      # RETREIVE VALUES
      values = [ self.read_float_reg(self.cl, reg[1], unit=1) for reg in self.cfgregs ]
      logstr = " " + time.strftime('%Y-%m-%d %H:%M:%S') + " "
    
      for x in zip(self.cfgregs,values):
        val = self.format_output(*x)
        logstr+= '%10s' % val
        pValues[x[0][0]] = val;
        
      logging.info(logstr)
      self.publish(pValues)
      time.sleep(1)
    conn.close()

def main() :
  logger = logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  mycf   = MyConfig("/powermeter/config.ini")
  mymb   = MyModbus(mycf)
  mymb.modbus_init()
  mymb.read_modbusdata()

if __name__ == '__main__' :
  main()
