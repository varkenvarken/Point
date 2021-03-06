# Point
Some code to control model railroad points (switches) with Raspberry Pi controlled servos.

It provides a Point and a PointCollection class that encapsulate a single point and a collection of points respectively. The PointCollection class can read and write to a json file.

It also provides a simple Server class that provides REST services to manage a single PointCollection and persists all information in a file points.json. The idea here is to provide a simple remote control mechanism for the collection of points.

The server can be run even without a PCA9685 controller present on the i2c bus, so that development and testing is possible outside a RaspberryPi environment.

The servo controller hat I use is from [Waveshare](https://www.waveshare.com/wiki/Servo_Driver_HAT) and it is available from various RaspberryPi resellers. I guess it will work with any PCA9685 based controller (which is actually a programmable LED driver) but as always, anything you do with the software is completely at your own risk. 

An Android app to interact with the REST server is provided as well and is available in a [separate project](https://github.com/varkenvarken/PointApp)

# Table of contents

[Running](#Running)

[REST interface](#REST-interface)

[Dependencies](#Dependencies)

[Installing](#Installing)

[Example](#Example)

[Running as a daemon](#Running-as-a-daemon)

[Security](#Security)

[Acknowledgements](#Acknowledgements)

# Running

To run a server that listens on https://0.0.0.0:8080 (i.e. all interfaces on localhost) simply do

```
python -m point
```

The synopsis for the program is

```
usage: python -m point [-h] [-c CONFIG] [-s SERVER] [-p PORT] [--key KEY]
                       [--cert CERT] [-x] [--secret SECRET] [-m] [-i I2C]

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
  -x, --nossl           Use http instead of https
  --secret SECRET       Filename of server name:password to use in basic
                        authentication, default secret
  -m, --mock            do not run an actual servo controller
  -i I2C, --i2c I2C     address of the controller on the i2c bus, default 0x40
```


# REST interface

The whole purpose of the server is to provide a REST interface to control the points connected to the servo hat. The idea is to do this with the help of an Android app, but as you
can see in the [Example](#Example) section you can use a command line tool like httpie or curl to test it.

All methods return JSON

    GET /points

return info about all points

    GET /point/ID

return info about a single point with the given ID. It also returns a list of free ports. This is a bit a a dirty way to implement things but that way all information about a point, including which other ports it may be assigned to are present in one chunk of data. That makes an app designer's life a bit easier.

    GET /server/info

return some general server info

    POST /points/add

add a new point. It will be given an initial name and assigned the first free port and will start in a disabled state.

    PUT /point/ID/ACTION

    PUT /point/ID/ATTRIBUTE/VALUE

**ID** is the id of a point.
**ACTION** is

- **moveleft**  or **left**, this switches the point to its leftmost position
- **moveright** or **right**, this switches the point to its rightmost position
- **enable**      enables the switch
- **disable**     disables the swich (servo commands are not executed)
- **start**       switches the point to its default position (left or right)
- **save**        the body will contain a JSON object with the new values for a points attributes

**ATTRIBUTE** is

- **left**        set the leftmost position to **VALUE** ( between -1.0 and 1.0 )       
- **right**       set the rightmost position to **VALUE** ( between -1.0 and 1.0 )       
- **mid**         set the middle position to **VALUE** ( between -1.0 and 1.0 )       
- **deltat**      set the time to wait to **VALUE** (in seconds) between servo steps
- **speed**       set the speed of the point to **VALUE** (in units per second)
- **port**        set the port of the point to **VALUE** (between 0 and 15)
- **pointtype**   set the point type to **VALUE** (`left`, `right`, `curved left`, `curved right`, `wye`, `double`, `triple`)
- **default**     set the default position to **VALUE** (`left` or `right`)
- **description** set a description for this point (**VALUE** is max 1024 characters).

```
DELETE /point/ID
```

will delete the point with the given ID. The last point cannot be deleted.
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

Installing requires installing the one external dependency, cloning the repository, generating a self signed certificate and storing a key:password combo, for example:

```bash
python -m pip install smbus2
git clone https://github.com/varkenvarken/Point.git
cd Point
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365
echo key:secret > secret
mkdir backup
```

There is no setup script included for now, but at this point you could simply do

```bash
sudo PYTHONPATH=./src python -m point
```

The sudo is only needed if your user does not have access to the i2c bus.
(And of course i2c must be enabled and your servo hat installed :-)

# Example
After running the server for the first time, you could run the following commands to create and test a single point. We use https (from https://github.com/httpie/httpie) to test against the server running with a self signed certificate (hence the `--verify no`). Note that every request needs to be authenticated.

Tip: if you want to test the server or just make sure that new points will not actually issues commands on the i2c bus, run the server with the `--mock` option. It will then still populate and update the points database, but never try to move the servo.

```bash
 https --verify no -a key:secret GET '127.0.0.1:8080/points'
 https --verify no -a key:secret POST '127.0.0.1:8080/points/add'
 https --verify no -a key:secret PUT '127.0.0.1:8080/point/bd560...0c32a/setleft/0.3'
 https --verify no -a key:secret PUT '127.0.0.1:8080/point/bd560...0c32a/setright/-0.3'
 https --verify no -a key:secret PUT '127.0.0.1:8080/point/bd560...0c32a/setspeed/0.5'
 https --verify no -a key:secret PUT '127.0.0.1:8080/point/bd560...0c32a/enable'
```
We have abbreviated the GUID for the point added in the second line to `bd560...0c32a`.
Yours will be different.

Every command returns a chunk of JSON data representing the state of the object last touched, so a typical action will show: 

```json
{
    "freeports": [0,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
    "point": {
        "_left": -0.3,
        "_mid": -0.02,
        "_right": 0.3,
        "current": -0.3,
        "default": "left",
        "deltat": 0.02,
        "description": "A point",
        "enabled": true,
        "index": "bd560a2618854204a933f6950fd0c32a",
        "name": "Point 1",
        "pointtype": "right",
        "port": 1,
        "speed": 0.5
    }
}

```

You could now move the new point (assuming you don't run the server with `--mock`)

```bash
https --verify no -a key:secret PUT '127.0.0.1:8080/point/bd560...0c32a/left'
https --verify no -a key:secret PUT '127.0.0.1:8080/point/bd560...0c32a/right'
``` 

# Running as a daemon
On my Raspberry Pi with Ubuntu, I created the following file */home/michel/bin/point-daemon*

```bash
#!/bin/bash
PYTHONPATH=/home/michel/Point/src python -m point --config /home/michel/Point/points.json --secret /home/michel/Point/secret --backup /home/michel/Point/backup --key /home/michel/Certificates/michelanders.nl.key  --cert /home/michel/Certificates/michelanders.nl.crt --log /var/log/points.log
```
That is one long line gathering all relevant options and a proper PYTHONPATH.

I then created the file */lib/systemd/system/point-daemon.service*

```ini
[Unit]
Description=Point controller service
After=network.target network-online.target

[Service]
Type=simple
User=root
Group=root
Restart=always
ExecStartPre=/bin/mkdir -p /var/run/point-daemon
PIDFile=/var/run/point-deamon/service.pid
ExecStart=/home/michel/bin/point-daemon

[Install]
WantedBy=multi-user.target
```

I then restarted systemd, enabled this service (so it will start at reboot) and started it

```bash
sudo systemctl daemon-reload
sudo systemctl enable point-daemon.service
sudo systemctl start point-daemon.service
```

You can verify the status with `sudo systemctl status point-daemon.service`
It will show something like:
```
??? point-daemon.service - Point controller service
   Loaded: loaded (/lib/systemd/system/point-daemon.service; enabled; vendor preset: enabled)
   Active: active (running) since Sun 2022-05-01 17:06:16 CEST; 9min ago
  Process: 1735 ExecStartPre=/bin/mkdir -p /var/run/point-daemon (code=exited, status=0/SUCCESS)
 Main PID: 1738 (point-daemon)
    Tasks: 2 (limit: 4915)
   CGroup: /system.slice/point-daemon.service
           ??????1738 /bin/bash /home/michel/bin/point-daemon
           ??????1740 python -m point --config /home/michel/Point/points.json --secret /home/michel/Point/secret --backup /home/michel/Point/backup --key 

May 01 17:06:16 raspberrypi systemd[1]: Starting Point controller service...
May 01 17:06:16 raspberrypi systemd[1]: Started Point controller service.
May 01 17:06:16 raspberrypi point-daemon[1738]: Listening on 0.0.0.0:8080. JSON file used: /home/michel/Point/points.json. args.mock=False
```

Note that only things written to *stderr* will show up in the daemon log. You can inspect that too, with `sudo journalctl -u point-daemon`

The access log is written to the logfile specified with *--log*.

Note that after reboot it may take a few seconds before the service is accessible. Even though the daemon will show up in the process list and will be listening on 0.0.0.0, the actual network stack may need longer to fully setup.

# Security

The current setup is insecure: The server is required to run with elevated privileges to access the i2c bus and for now we do this by running the server as root.

It might be a better idea to create a dedicated user for this and add it to the i2c group as documented here: https://lexruee.ch/setting-i2c-permissions-for-non-root-users.html

Every REST call does need to be pre-authenticated, i.e. must supply a basic authentication header. It is therefore a good idea to always run the server with https enabled (the default) and make sure that both certificate files and the secret are stored in files that can only be read by the server process.
# Acknowledgements

The PCA9685 module is largely based on the original one supplied with the Waveshare Servo hat. I replaced the `smbus` import for a `smbus2` import (to make everything work with Python versions newer than 3.5)
