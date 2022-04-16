# Point
Some code to control model railroad points (switches) with Raspberry Pi controlled servos.

It provides a Point and a PointCollection class that encapsulate a single point and a collection of points respectively. The PointCollection class can read and write to a json file.

A simple REST server manages a single PointCollection and persists all information in a file points.json. The idea here is to provide a simple remote control mechanism for the collection of points.

The server can be run even without a PCA9685 controller present on the i2c bus, so that development and testing is possible outside a RaspberryPi environment.

The servo controller hat I use is from [Waveshare](https://www.waveshare.com/wiki/Servo_Driver_HAT) and it is available from various RaspberryPi resellers. I guess it will work with any PCA9685 based controller (which is actually a programmable LED driver) but as always, anything you do with the software is completely at your own risk. 

# Running

To run a server that listens on http://0.0.0.0:8080 (i.e. all interfaces) simply do

```
python -m point
```

The synopsis for the program is

```
usage: python -m point [-h] [-c CONFIG] [-s SERVER] [-p PORT] [--key KEY]
                       [--cert CERT] [-m] [-i I2C]

A REST server to control a PCA9685 based servo hat on a RaspberryPi

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        location of the json file that stores the point data,
                        default points.json
  -s SERVER, --server SERVER
                        hostname or ip address the server will listen on,
                        default 0.0.0.0
  -p PORT, --port PORT  port the server will listen on, default 8080
  --key KEY             location of the key file, default key.pem
  --cert CERT           location of the key file, default cert.pem
  -m, --mock            do not run an actual servo controller
  -i I2C, --i2c I2C     address of the controller on the i2c bus, default 0x40
```


# REST interface

The whole purpose of the server is to provide a REST interface to control the points connected to the servo hat. The idea is to build an Android app for that, but as you
can see in the [Example](#Example) section you can use a command line tool like httpie or curl to test it.

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

**NAME** is the name of a point.
**ACTION** is

- **moveleft**  or **left**, this switches the point to its leftmost position
- **moveright** or **right**, this switches the point to its rightmost position
- **enable**      enables the switch
- **disable**     disables the swich (servo commands are not executed)
- **start**       switches the point to its default position (left or right)

**ATTRIBUTE** is

- **left**        set the leftmost position to **VALUE** ( between -1.0 and 1.0 )       
- **right**       set the rightmost position to **VALUE** ( between -1.0 and 1.0 )       
- **mid**         set the middle position to **VALUE** ( between -1.0 and 1.0 )       
- **deltat**      set the time to wait to **VALUE** (in seconds) between servo steps
- **speed**       set the speed of the point to **VALUE** (in units per second)
- **port**        set the port of the point to **VALUE** (between 0 and 15)
- **pointtype**   set the point type to **VALUE** (`left`, `right`, `curved left`, `curved right`, `wye`, `double`, `triple`)
- **default**     set the default position to **VALUE** (`left` or `right`)
- **description** set a description for this point (**VALUE** is max 1024 characters)

# Dependencies

The code is developed for Python 3.8 and newer and as far as I can tell the `smbus` module on the Raspberry only works for Python < 3.5. To deal with that we need the [smbus2](https://pypi.org/project/smbus2/) package, which can be installed from PyPi. 

- python 3.8.9 (including all standard modules)
- smbus2

Note that I followed the installation instruction fro Python from https://itheo.tech/ultimate-python-installation-on-a-raspberry-pi-and-ubuntu-script but it wasn quite the ultimate answer to everything. 

I had to install libssl-dev (to get pip to work) and libffi-dev (because otherwise smbus2 complained about missing a _ctypes module):
```bash
sudo apt-get install libssl-dev
sudo apt-get install libffi-dev
```
only then could I succesfully compile python 3.8.9 from scratch.

# Installing

Installing requires installing the one external dependency, cloning the repository and generating a self signed certificate
```bash
python -m pip install smbus2
git clone https://github.com/varkenvarken/Point.git
cd Point
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365
```

There is no setup script included for now, but at this point you could simply do

```bash
sudo PYTHONPATH=./src python -m point
```

The sudo is only needed if your user does not have access to the i2c bus.
(And of course i2c must be enabled and your servo hat installed :-)

# Example
After running the server for the first time, you could run the following commands to create and test a single point. We use https (from https://github.com/httpie/httpie) to test againts the server running with a self signed certificate (hence the `--verify no`).

Tip: if you want to test the server or just make sure that new points will not actually issues commands on the i2c bus, run the server with the `--mock` option. It will then still populate and update the points database, but never try to move the servo.

```bash
 https --verify no GET '127.0.0.1:8080/points'
 https --verify no POST '127.0.0.1:8080/points/add/Point 1'
 https --verify no PUT '127.0.0.1:8080/point/Point 1/setleft/0.3'
 https --verify no PUT '127.0.0.1:8080/point/Point 1/setright/-0.3'
 https --verify no PUT '127.0.0.1:8080/point/Point 1/setspeed/0.5'
 https --verify no PUT '127.0.0.1:8080/point/Point 1/enable'
```
Every command returns a chunk of JSON data representing the state of the object last touched, so the last one will show

```json
{
    "_left": 0.3,
    "_mid": 0.0,
    "_right": -0.3,
    "current": 0.0,
    "default": "left",
    "deltat": 0.02,
    "description": "A point",
    "enabled": true,
    "pointtype": "left",
    "port": 0,
    "speed": 0.5
}
```

You could now move the new point (assuming you don't run the server with `--mock`)

```bash
https --verify no PUT '127.0.0.1:8080/point/Point 1/left'
https --verify no PUT '127.0.0.1:8080/point/Point 1/right'
``` 



# Security

The current setup is incredibly insecure: connections to the REST server use https but the is no user authentication!

And the server is required to run with elevated privileges to access the i2c bus.


# Acknowledgements

The PCA9685 module is largely based on the original one supplied with the Waveshare Servo hat. I replaced the `smbus` import for a `smbus2` import (to make everything work with Python versions newer than 3.5)
