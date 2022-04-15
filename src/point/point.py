import json
from collections import OrderedDict
from time import sleep, time


class Point:
    def __init__(self, port, pwm=None, default="left", pointtype="left"):
        self.setport(port)
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

    def setport(self, port):
        p = int(port)
        if p < 0 or p > 15:
            raise ValueError("port not in range [0,15]")
        self.port = p

    def getport(self):
        return self.port

    def setpwm(self, pwm):
        if not hasattr(pwm, "setServoPulse"):
            raise ValueError("pwm object has no setServoPulse attribute")
        self.pwm = pwm

    # there is no getpwm

    def setdefault(self, default):
        defaults = {"left", "mid", "right"}
        if default not in defaults:
            raise ValueError(f"default not one of {defaults}")
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
            p = ((position + 1.0) / 2.0) * 4095  # map [-1, 1] -> [0, 4095]
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
        types = {
            "left",
            "curved left",
            "wye",
            "right",
            "curved right",
            "double",
            "triple",
        }
        if t not in types:
            raise ValueError(f"type not one of {types}")
        self.pointtype = t

    def __repr__(self):
        return f"Point({self.port},{self.pwm=},default='{self.default}')"

    def dumps(self):
        return f"""{{"port":{self.port}, "enabled":{"true" if self.enabled else "false"}, "current":{self.current:.5f}, "description":"{self.description}","_left":{self._left:.5f}, "_right":{self._right:.5f}, "_mid":{self._mid:.5f}, "speed":{self.speed:.5f}, "default":"{self.default}", "deltat":{self.deltat:.5f}, "pointtype":"{self.pointtype}"}}"""

    @staticmethod
    def loads(s) -> "Point":
        d = json.loads(s)
        return Point.loadd(d)

    @staticmethod
    def loadd(d, pwm) -> "Point":
        p = Point(d["port"], pwm)
        p.__dict__.update(d)
        return p


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
        for name, point in d.items():
            pc[name] = Point.loadd(point, pwm)
        return pc

    def getfreeport(self):
        used = set(p.port for p in self.values())
        possible = set(range(16))
        return (possible - used).pop()

    def info(self):
        return json.dumps({"uptime": time() - self.start_time})


if __name__ == "__main__":

    class MockPWM:
        def setServoPulse(self, port, pulse):
            pulse = int(pulse)
            print(f"setServoPulse {port=} {pulse=}")

    a = Point(4, MockPWM())
    a.setleft(-1)
    assert a.getleft() == -1.0
    a.setright(1)
    assert a.getright() == 1.0

    print(a.dumps())
    b = Point.loads(a.dumps())
    print(b.dumps())

    pc = PointCollection(pwm=MockPWM())
    pc["point 2"] = Point(2)
    pc["point 3"] = Point(3)
    d = pc.dumps()
    print(d)
    print(PointCollection.loads(d, pwm=MockPWM()).dumps())

    print(f"moving left from {a.current=}")
    start = time()
    a.moveleft()
    print(f"half swing to the left took {time()-start:.1f}s")
    print(f"moving right from {a.current=}")
    start = time()
    a.moveright()
    print(f"full swing to the right took {time()-start:.1f}s")
