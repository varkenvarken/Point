# Point
Some code to control model railroad points (switches) with Raspberry Pi controlled servos.

It provides a Point and a PointCollection class that encapsulate a single point and a collection of points respectively. The PointCollection class can read and write to a json file.

A simple REST server manages a single PointCollection and persists all information in a file points.json. The idea here is to provide a simple remote control mechanism for the collection of points.

The server can be run even without a PCA9685 controller present on the i2c bus, so that development and testing is possible outside a RaspberryPi environment.

The servo controller hat I use is from [Waveshare](https://www.waveshare.com/wiki/Servo_Driver_HAT) and it is available from various RaspberryPi resellers. I guess it will work with any PCA9685 based controller (which is actually a programmable LED driver) but as always, anything you do with the software is completely at your own risk. 

# Running

To run a server that listens on http://127.0.0.1:8080 simply do

```
python -m point
```

The synopsis for the program is

```
usage: python -m point [-h] [-c CONFIG] [-s SERVER] [-p PORT] [-m] [-i I2C]

A REST server to control a PCA9685 based servo hat on a RaspberryPi

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        location of the json file that stores the point data
  -s SERVER, --server SERVER
                        hostname or ip address the server will listen on
  -p PORT, --port PORT  port the server will listen on
  -m, --mock            do not run an actual servo controller
  -i I2C, --i2c I2C     address of the controller on the i2c bus
```


# REST interface

All methods return JSON

GET /points

return info about all points

GET /point/NAME

return info about a single named point

GET /server/info

return some general server info

POST /points/add/NAME

add a new point. It must have unique name and will start in a disabled state.

PUT /point/NAME/ACTION
PUT /point/NAME/ATTRIBUTE/VALUE

NAME is the name of a point.
ACTION is

- **moveleft**    switches the point to its leftmost position
- **moveright**   switches the point to its rightmost position
- **enable**      enables the switch
- **disable**     disables the swich (servo commands are not executed)
- **start**       switches the point to its default position (left or right)

ATTRIBUTE is

- **left**        set the leftmost position to VALUE ( between -1.0 and 1.0 )       
- **right**       set the rightmost position to VALUE ( between -1.0 and 1.0 )       
- **mid**         set the middle position to VALUE ( between -1.0 and 1.0 )       
- **deltat**      set the time to wait (in seconds) between servo steps
- **speed**       set the speed of the point in units per second
- **port**        set the port of the point (between 0 and 15)
- **pointtype**   set the point type (left, right, curved left, curved right, wye, double, triple)
- **default**     set the default position (left or right)
- **description** set a description for this point (max 1024 characters)

# Dependencies
- python 3.8.9
- smbus2

# Installing

```
python -m pip install smbus2
git clone https://github.com/varkenvarken/Point.git
```

There is no setup script included for now, but at this point you could simply do

```
sudo PYTHONPATH=./Point/src python -m point
```

The sudo is only needed if your user does not have access to the i2c bus.
(And of course i2c must be enabled and your servo hat installed :-)


