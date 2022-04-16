import argparse
from sys import stderr

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
        help="location of the json file that stores the point data",
    )
    argparser.add_argument(
        "-s",
        "--server",
        type=str,
        default="0.0.0.0",
        help="hostname or ip address the server will listen on",
    )
    argparser.add_argument(
        "-p", "--port", type=int, default=8080, help="port the server will listen on"
    )
    argparser.add_argument(
        "-m",
        "--mock",
        default=False,
        action="store_true",
        help="do not run an actual servo controller",
    )
    argparser.add_argument(
        "-i", "--i2c", default=0x40, help="address of the controller on the i2c bus"
    )
    args = argparser.parse_args()
    if args.mock:
        pwm = MockPWM()
    else:
        from .pca9685 import PCA9685

        pwm = PCA9685(args.i2c, debug=False)
        pwm.setPWMFreq(50)

    server = Server((args.server, args.port), RESTHandler, args.config, pwm)
    print(
        f"Listening on {args.server}:{args.port}. JSON file used: {args.config}. {args.mock=}",
        file=stderr,
        flush=True,
    )
    server.serve_forever()
