import json
from base64 import b64decode
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError
from os.path import exists
from urllib.parse import unquote

from .point import Point, PointCollection, PointEncoder


class Server(HTTPServer):
    def __init__(self, address, handler, dbfile, pwm, secret):
        self.pc = None
        if exists(dbfile):
            with open(dbfile) as f:
                config = "\n".join(f.readlines())
                try:
                    self.pc = PointCollection.loads(config, pwm=pwm)
                except JSONDecodeError as e:
                    raise ValueError(f"could not correctly read config file {e}")
        if secret is not None and exists(secret):
            with open(secret) as f:
                self.secret = f.readline().strip()
        else:
            raise ValueError(f"could not correctly read file with secret {secret}")
        if self.pc is None:
            self.pc = PointCollection(pwm=pwm)
        self.dbfile = dbfile
        super().__init__(address, handler)

    def writeDBfile(self):
        with open(self.dbfile, "w") as f:
            f.write(self.pc.dumps())


class RESTHandler(BaseHTTPRequestHandler):
    def auth(self):
        # for header in self.headers:
        #    print(header, self.headers[header])
        try:
            auth = self.headers["Authorization"]
            if auth is None:
                raise KeyError
            basic, msg = auth.split()
            if basic != "Basic":
                raise KeyError
            if b64decode(msg).decode() == self.server.secret:
                return True
        except KeyError:
            pass
        self.send_response(401)
        self.end_headers()
        return False

    def do_GET(self):
        if not self.auth():
            return
        elements = unquote(self.path).split("/")
        if elements[1] == "points":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(self.server.pc.dumps().encode())
        elif elements[1] == "point" and elements[2] in self.server.pc:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            d = {
                "point": self.server.pc[elements[2]],
                "freeports": list(self.server.pc.getfreeports()),
            }
            print(json.dumps(d, cls=PointEncoder))
            self.wfile.write(json.dumps(d, cls=PointEncoder).encode())
        elif elements[1] == "server" and elements[2] in {"info"}:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(getattr(self.server.pc, elements[2])().encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if not self.auth():
            return
        commands = {
            "moveleft": 0,
            "moveright": 0,
            "enable": 0,
            "disable": 0,
            "start": 0,
            "move": 1,
            "setleft": 1,
            "setright": 1,
            "setmid": 1,
            "setdeltat": 1,
            "setspeed": 1,
            "setport": 1,
            "setpointtype": "str",
            "setdefault": "str",
            "setdescription": "str",
            "save": None,
        }
        elements = unquote(self.path).split("/")
        if (
            elements[1] == "point"
            and elements[2] in self.server.pc
            and (
                elements[3] in commands
                or "move" + elements[3] in commands
                or "set" + elements[3] in commands
            )
        ):
            d = {}
            point = self.server.pc[elements[2]]
            cmd = elements[3]
            if cmd == "save":
                method = getattr(point, cmd)
                d = json.loads(
                    self.rfile.read(int(self.headers.get("Content-Length", -1)))
                )
                self.rfile.close()
            elif cmd in commands and hasattr(
                point, cmd
            ):  # first check if it is in commands to prevent checking for an attribute instead of a method
                method = getattr(point, cmd)
            elif hasattr(point, "move" + elements[3]):
                cmd = "move" + elements[3]
                method = getattr(point, cmd)
            elif hasattr(point, "set" + elements[3]):
                cmd = "set" + elements[3]
                method = getattr(point, cmd)
            else:
                raise AttributeError(f"no such method [move|set]{elements[3]}")
            try:
                if commands[cmd] == 1:
                    value = float(elements[4])
                    method(value)
                elif commands[cmd] == "str":
                    value = elements[4]
                    method(value)
                elif commands[cmd] is None:
                    method(d)
                else:
                    method()
            except ValueError as e:
                self.send_error(404, str(e))
            self.server.writeDBfile()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            d = {
                "point": point,
                "freeports": list(self.server.pc.getfreeports()),
            }
            j = json.dumps(d, cls=PointEncoder)
            self.wfile.write(j.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        if not self.auth():
            return
        elements = unquote(self.path).split("/")
        if elements[1] == "point" and elements[2] in self.server.pc:
            del self.server.pc[elements[2]]
            self.server.writeDBfile()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(self.server.pc.dumps().encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if not self.auth():
            return
        elements = unquote(self.path).split("/")
        if elements[1] == "points" and elements[2] == "add":
            try:
                point = Point(
                    self.server.pc.getfreeport(), None, pwm=self.server.pc.pwm
                )
                self.server.pc[point.getindex()] = point
                self.server.writeDBfile()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                d = {
                    "point": point,
                    "freeports": list(self.server.pc.getfreeports()),
                }
                j = json.dumps(d, cls=PointEncoder)
                self.wfile.write(j.encode())
            except IndexError as e:
                self.send_error(409, str(e))
        else:
            self.send_response(404)
            self.end_headers()


class MockPWM:
    def setServoPulse(self, port, pulse):
        pulse = int(pulse)
        print(f"setServoPulse {port=} {pulse=}")
