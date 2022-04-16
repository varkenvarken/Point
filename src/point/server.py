import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError
from os.path import exists
from urllib.parse import unquote

from .point import Point, PointCollection


class Server(HTTPServer):
    def __init__(self, address, handler, dbfile, pwm):
        self.pc = None
        if exists(dbfile):
            with open(dbfile) as f:
                config = "\n".join(f.readlines())
                try:
                    self.pc = PointCollection.loads(config, pwm=pwm)
                except JSONDecodeError as e:
                    raise ValueError(f"could not correctly read config file {e}")
        if self.pc is None:
            self.pc = PointCollection(pwm=pwm)
        self.dbfile = dbfile
        super().__init__(address, handler)

    def writeDBfile(self):
        with open(self.dbfile, "w") as f:
            f.write(self.pc.dumps())


class RESTHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        elements = unquote(self.path).split("/")
        if elements[1] == "points":
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(self.server.pc.dumps().encode())
        elif elements[1] == "point" and elements[2] in self.server.pc:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(self.server.pc[elements[2]].dumps().encode())
        elif elements[1] == "server" and elements[2] in {"info"}:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(getattr(self.server.pc, elements[2])().encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        commands = {
            "moveleft": 0,
            "moveright": 0,
            "enable": 0,
            "disable": 0,
            "start": 0,
            "setleft": 1,
            "setright": 1,
            "setmid": 1,
            "setdeltat": 1,
            "setspeed": 1,
            "setport": 1,
            "setpointtype": "str",
            "setdefault": "str",
            "setdescription": "str",
        }
        elements = unquote(self.path).split("/")
        if (
            elements[1] == "point"
            and elements[2] in self.server.pc
            and (
                elements[3] in commands
                or "set" + elements[3] in commands
                or "move" + elements[3] in commands
            )
        ):
            point = self.server.pc[elements[2]]
            cmd = elements[3]
            if cmd in commands and hasattr(
                point, cmd
            ):  # first check if it is in commands to prevent checking for an attribute instead of a method
                method = getattr(point, cmd)
            elif hasattr(point, "set" + elements[3]):
                cmd = "set" + elements[3]
                method = getattr(point, cmd)
            elif hasattr(point, "move" + elements[3]):
                cmd = "move" + elements[3]
                method = getattr(point, cmd)
            else:
                raise AttributeError(f"no such method [move|set]{elements[3]}")
            print(f">>>>>>>>>>>> {cmd=} {commands[cmd]}")
            try:
                if commands[cmd] == 1:
                    value = float(elements[4])
                    method(value)
                elif commands[cmd] == "str":
                    value = elements[4]
                    method(value)
                else:
                    method()
            except ValueError as e:
                self.send_error(404, str(e))
            self.server.writeDBfile()
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(point.dumps().encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        elements = unquote(self.path).split("/")
        if elements[1] == "points" and elements[2] == "add":
            try:
                name = elements[3]
                if name in self.server.pc:
                    raise IndexError(f"name already in use")
                point = Point(self.server.pc.getfreeport(), pwm=self.server.pc.pwm)
                self.server.pc[name] = point
                self.server.writeDBfile()
                self.send_response(200)
                self.send_header("Content-type", "text/json")
                self.end_headers()
                self.wfile.write(self.server.pc[name].dumps().encode())
            except IndexError as e:
                self.send_error(409, str(e))
        else:
            self.send_response(404)
            self.end_headers()


class MockPWM:
    def setServoPulse(self, port, pulse):
        pulse = int(pulse)
        print(f"setServoPulse {port=} {pulse=}")
