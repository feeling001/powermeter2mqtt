# Powermeter 2 MQTT

This piece of code intend to send the powermeter data trough mqtt.


# Code
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
