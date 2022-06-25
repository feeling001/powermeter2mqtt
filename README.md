# Powermeter 2 MQTT

This piece of code intend to send the powermeter data trough mqtt.




# Code

## HOWTO Run

  $ mkdir /srv/powermeter
  $ docker run --device=/dev/serial/by-ipd/***name_of_your_device***:/dev/ttyUSB0 -v /srv/powermeter:/powermeter laurentddd/powermeter2mqtt:latest

### Or with docker compose:
Into your docker-compose.yml file, put :

  version: '3'
  services:
    powermeter:
      container_name: powermeter2mqtt
      image: laurentddd/powermeter2mqtt:latest
      restart: unless-stopped
      environment:
        - TZ=Europe/Brussels
      volumes:
        - /srv/powermeter:/powermeter
      devices:
        - /dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0:/dev/ttyUSB0
        
Then run

  $ docker-compose up -d

## Configuration file

    [DEFAULT]
    UsbDevice = /dev/ttyUSB0 # path to the rs485 usb device
    LogLevel  = WARNING      # log level (info will dump the collected data into the logfile)

    [MQTT]
    Server = 127.0.0.1          # MQTT Server address
    Port   = 1883               # MQTT Port
    User   = mqtt_username      # MQTT Username
    Pass   = mqtt_password      # MQTT Password
    Topic  = path/to/mqtt/topic # Path under wich the data is published (json data)


## Basic schematic


Collect the power data trough Modbus

```mermaid
graph LR
A[Powermeter - MODBUS] -- RS485 --> C(USB device)
C -- tty USB --> D(powermeter2mqtt)
```
