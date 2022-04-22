import json
from collections import OrderedDict
from time import sleep, time
from uuid import uuid4

Position = {"left", "right", "mid"}
PointType = {
    "left",
    "curved left",
    "wye",
    "right",
    "curved right",
    "double",
    "triple",
}


class Point:
    def __init__(self, port, name, pwm=None, default="left", pointtype="left"):
        self.index = uuid4().hex
        self.setport(port)
        self.name = name if name else f"Point on port {port}"
        self.setpwm(pwm)
        self.enabled = False
        self._mid = 0.0  # range [-1.0, 1.0]
        self._left = 0.0  # range [-1.0, 1.0]
        self._right = 0.0  # range [-1.0, 1.0]
        self.speed = 2.0  # change in position per second when changing position (default is 1 seconds to travel from full left to right)
        self.setdefault(default)  # left, right, mid
        self.current = 0.0  # range [-1.0, 1.0]
        self.deltat = 0.02  # seconds between micro steps
        self.setpointtype(pointtype)
        self.description = "A point"

    def getindex(self):
        return self.index

    def setport(self, port):
        p = int(port)
        if p < 0 or p > 15:
            raise ValueError("port not in range [0,15]")
        self.port = p

    def getport(self):
        return self.port

    def setname(self, name):
        self.name = name

    def getname(self):
        return self.name

    def setpwm(self, pwm):
        if not hasattr(pwm, "setServoPulse"):
            raise ValueError("pwm object has no setServoPulse attribute")
        self.pwm = pwm

    # there is no getpwm

    def setdefault(self, default):
        if default not in Position:
            raise ValueError(f"default not one of {Position}")
        self.default = default

    def getdefault(self):
        return self.default

    def setspeed(self, speed):
        if speed < 0.05 or speed > 4:
            raise ValueError("speed not in range [0.05, 4]")
        self.speed = speed

    def getspeed(self):
        return self.speed

    def setdeltat(self, deltat):
        if deltat < 0.005 or deltat > 0.1:
            raise ValueError("deltat not in range [0.005, 0.1]")
        self.deltat = deltat

    def getdeltat(self):
        return self.deltat

    # actions that move the point
    def movemid(self):
        self.move(self._mid)

    def moveleft(self):
        self.position(self.current, self._left, self.speed)

    def moveright(self):
        self.position(self.current, self._right, self.speed)

    def movestart(self):
        self.move(self._left if self.default == "left" else self._right)

    def position(self, start, end, speed):
        if start > end:
            speed = -speed
        stepsize = speed * self.deltat
        steps = int((end - start) / stepsize)
        print(f"{start=} {end=} {steps=} {stepsize=}")
        for _ in range(steps):
            self.delay()
            self.move(start)
            self.delay()
            start += stepsize
        self.move(end)

    def delay(self):
        sleep(self.deltat)

    def move(self, position):
        if self.enabled:
            p = (
                (position + 1.0) / 2.0
            ) * 2000 + 500  # map [-1, 1] -> [500, 2500] i.e. 0.5 to 2.5 μs
            self.pwm.setServoPulse(self.port, p)
            self.current = position

    # set.get configuration
    def enable(self):
        self.enabled = True

    def enabled(self):
        return self.enabled

    def disable(self):
        self.enabled = False

    def getmid(self):
        return self._mid

    def setmid(self, pos):
        if pos < -1 or pos > 1:
            raise ValueError("pos not in range [-1, 1]")
        self._mid = pos

    def getleft(self):
        return self._left

    def setleft(self, pos):
        if pos < -1 or pos > 1:
            raise ValueError("pos not in range [-1, 1]")
        self._left = pos

    def getright(self):
        return self._right

    def setright(self, pos):
        if pos < -1 or pos > 1:
            raise ValueError("pos not in range [-1, 1]")
        self._right = pos

    def setdescription(self, s):
        s = json.dumps(s[:1024].strip().expandtabs(4))[1:-1]
        self.description = s

    def getdescription(self):
        return self.description

    def getpointtype(self):
        return self.pointtype

    def setpointtype(self, t):
        if t not in PointType:
            raise ValueError(f"type not one of {PointType}")
        self.pointtype = t

    def __repr__(self):
        return f'Point({self.port},"{self.name}",{self.pwm=},default="{self.default})'

    def dumps(self):
        return f"""{{"index": "{self.index}", "port":{self.port}, "name":"{self.name}", "enabled":{"true" if self.enabled else "false"}, "current":{self.current:.5f}, "description":"{self.description}","_left":{self._left:.5f}, "_right":{self._right:.5f}, "_mid":{self._mid:.5f}, "speed":{self.speed:.5f}, "default":"{self.default}", "deltat":{self.deltat:.5f}, "pointtype":"{self.pointtype}"}}"""

    @staticmethod
    def loads(s) -> "Point":
        d = json.loads(s)
        return Point.loadd(d)

    @staticmethod
    def loadd(d, pwm) -> "Point":
        p = Point(d["port"], d["name"], pwm)
        p.__dict__.update(d)
        return p

    def save(self, d):
        """Note that this function will update fields without any bounds checking!"""
        self.__dict__.update(d)


class PointCollection(OrderedDict):
    def __init__(self, *args, pwm=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pwm = pwm
        for p in self.values():
            p.pwm = self.pwm
        self.start_time = time()

    def __setitem__(self, __k: str, __v: Point) -> None:
        __v.pwm = self.pwm
        return super().__setitem__(__k, __v)

    def dumps(self):
        return "{" + ",".join([f'"{k}":{v.dumps()}' for k, v in self.items()]) + "}"

    @staticmethod
    def loads(s, pwm):
        d = json.loads(s)
        pc = PointCollection(pwm=pwm)
        for index, point in d.items():
            pc[index] = Point.loadd(point, pwm)
        return pc

    def getfreeports(self):
        used = set(p.port for p in self.values())
        possible = set(range(16))
        return possible - used

    def getfreeport(self):
        return self.getfreeports().pop()

    def info(self):
        return json.dumps({"uptime": time() - self.start_time})


class PointEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Point):
            return {
                "index": obj.index,
                "port": obj.port,
                "name": obj.name,
                "enabled": obj.enabled,
                "current": obj.current,
                "description": obj.description,
                "_left": obj._left,
                "_right": obj._right,
                "_mid": obj._mid,
                "speed": obj.speed,
                "default": obj.default,
                "deltat": obj.deltat,
                "pointtype": obj.pointtype,
            }
        return json.JSONEncoder.default(self, obj)
