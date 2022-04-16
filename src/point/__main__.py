import argparse
from sys import stderr
import ssl

from .server import MockPWM, RESTHandler, Server

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        prog="python -m point",
        description="A REST server to control a PCA9685 based servo hat on a RaspberryPi",
    )
    argparser.add_argument(
        "-c",
        "--config",
        type=str,
        default="points.json",
        help="location of the json file that stores the point data, default points.json",
    )
    argparser.add_argument(
        "-s",
        "--server",
        type=str,
        default="0.0.0.0",
        help="hostname or ip address the server will listen on, default 0.0.0.0",
    )
    argparser.add_argument(
        "-p", "--port", type=int, default=8080, help="port the server will listen on, default 8080"
    )
    argparser.add_argument(
        "--key",
        type=str,
        default="key.pem",
        help="location of the key file, default key.pem",
    )
    argparser.add_argument(
        "--cert",
        type=str,
        default="cert.pem",
        help="location of the key file, default cert.pem",
    )
    argparser.add_argument(
        "-x",
        "--nossl",
        default=False,
        action="store_true",
        help="Use http instead of https",
    )
    argparser.add_argument(
        "--secret",
        type=str,
        default="secret",
        help="Filename of server name:password to use in basic authentication, default secret",
    )
    argparser.add_argument(
        "-m",
        "--mock",
        default=False,
        action="store_true",
        help="do not run an actual servo controller",
    )
    argparser.add_argument(
        "-i", "--i2c", default=0x40, help="address of the controller on the i2c bus, default 0x40"
    )
    args = argparser.parse_args()
    if args.mock:
        pwm = MockPWM()
    else:
        from .pca9685 import PCA9685

        pwm = PCA9685(args.i2c, debug=False)
        pwm.setPWMFreq(50)

    server = Server((args.server, args.port), RESTHandler, args.config, pwm, args.secret)
    if not args.nossl:
        server.socket = ssl.wrap_socket (server.socket,
            keyfile=args.key,
            certfile=args.cert, server_side=True)

    print(
        f"Listening on {args.server}:{args.port}. JSON file used: {args.config}. {args.mock=}",
        file=stderr,
        flush=True,
    )
    server.serve_forever()
