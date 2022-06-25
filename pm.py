#!/usr/bin/python
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


def start_mqtt() :
  global client
  global cl
  logging.warning(" Connecting to MQTT with user : " + mqtt_user) 
  client = mqtt.Client("P1", clean_session=False)
  client.username_pw_set(username=mqtt_user,password=mqtt_pass)
  client.connect( mqtt_host , mqtt_port ) #connect to broker
  client.on_disconnect = on_disconnect
  client.on_connect    = on_connect
  client.loop_start()
  cl     = pymodbus.client.sync.ModbusSerialClient('rtu', port=config['DEFAULT']['UsbDevice'], baudrate=9600, parity='N',stopbits=2, timeout=0.125)

def on_disconnect(client, userdata, rc) :
  if rc != 0:
    logging.warning(" Unexpected disconnection with result code %s" % rc)

def on_connect(client, userdata, flags, rc) :
  logging.warning(" Connected with result code %s" % rc)

def config_init() : 
  global config
  global mqtt_user
  global mqtt_pass
  global mqtt_host
  global mqtt_port
  global mqtt_topic
  if os.path.isfile('/powermeter/config.ini'):
    logging.warning(" Config file found")
  else:
    logging.warning(" Config file not found, place a default config.ini")
    shutil.copyfile('config.ini','/powermeter/config.ini')
  
  config = configparser.ConfigParser()
  config.read('/powermeter/config.ini')
  mqtt_user  = config['MQTT']['User']
  mqtt_pass  = config['MQTT']['Pass']
  mqtt_host  = config['MQTT']['Server']
  mqtt_port  = int(config['MQTT']['Port'])
  mqtt_topic = config['MQTT']['Topic']
  logging.basicConfig(filename='/powermeter/powermeter.log', level=config['DEFAULT']['LogLevel'])

def read_float_reg(client, basereg, unit=1) :
  resp = client.read_input_registers(basereg,2, unit=1)   
  if resp == None :
    return None
    # according to spec, each pair of registers returned
    # encodes a IEEE754 float where the first register carries
    # the most significant 16 bits, the second register carries the 
    # least significant 16 bits.
  return struct.unpack('>f',struct.pack('>HH',*resp.registers))

def fmt_or_dummy(regfmt, val) :
  if val is None :
    return '.'*len(regfmt[2]%(0))
  return regfmt[2]%(val)

def main() :
  regs = [
    # Symbol    Reg#  Format
    ( 'U',        0x00, '%6.2f' ), # Voltage [V]
    ( 'I',        0x06, '%6.2f' ), # Current [A]
    ( 'Pact',     0x0c, '%6.0f' ), # Active Power ("Wirkleistung") [W]
    ( 'Papp',     0x12, '%6.0f' ), # Apparent Power ("Scheinl.") [W]
    ( 'Prea',     0x18, '%6.0f' ), # Reactive Power ("Blindl.") [W]
    ( 'PF',       0x1e, '%6.3f' ), # Power Factor   [1]
    ( 'Phi',      0x24, '%6.1f' ), # cos(Phi)?      [1]
    ( 'Freq',     0x46, '%6.2f' ), # Line Frequency [Hz]
    ( 'Ptot',     0x48, '%8d' )    # Total power    [kw]
  ]

  pValues = {}
  # if client is set to odd or even parity, set stopbits to 1
  # if client is set to 'none' parity, set stopbits to 2

  N=0
  while True :
    N += 1
    if N % 32 == 1 :
        headstr = ' Date                 '
        for x in regs:
            headstr += ' %-7s' % x[0]
        logging.info(headstr)
        headstr = '---------------------'
        for x in regs:
            headstr += ':-------'
        logging.info(headstr)
        
    values = [ read_float_reg(cl, reg[1], unit=1) for reg in regs ]
    logstr = " " + time.strftime('%Y-%m-%d %H:%M:%S') + " "
  
    for x in zip(regs,values):
      val = fmt_or_dummy(*x)
      logstr+= '%8s' % val
      pValues[x[0][0]] = val;
          
    logging.info(logstr)
    client.publish(mqtt_topic,json.dumps(pValues))
    time.sleep(1)
  conn.close()

if __name__ == '__main__' :
  config_init()
  start_mqtt()
  main()
