#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from decimal import Decimal
from time import sleep, gmtime, strftime

from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from serial import Serial
from serial.serialutil import SerialException


logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/qgpsemu'

AP_CMD_ENGINE0_THROTTLE = 1
AP_CMD_ENGINE1_THROTTLE = 2

FG_COMMANDS = {
    AP_CMD_ENGINE0_THROTTLE: '/controls/engines/engine[0]/throttle {}',
    AP_CMD_ENGINE1_THROTTLE: '/controls/engines/engine[1]/throttle {}'
}

LAST_FG_COMMANDS = {}


def generate_nmea_sentences(telemetry):
    dt = gmtime()
    t = strftime('%H%M%S', dt)
    d = strftime('%d%m%y', dt)
    alt = Decimal(telemetry['altitude-ft']) * Decimal('0.3048')
    lat = telemetry['latitude-deg']
    lon = telemetry['longitude-deg']
    lat_half = 'N' if lat > 0 else 'S'
    lon_half = 'E' if lon > 0 else 'W'
    lat = lat*100 if lat > 0 else lat * -100
    lon = lon*100 if lon > 0 else lon * -100

    heading = telemetry['heading-deg']
    roll_x = telemetry['roll-deg']
    pitch_y = telemetry['pitch-deg']
    # yaw-deg is '' for some reason
    yaw_z = heading

    speed_over_ground = telemetry['groundspeed-kt']

    gpgga = '$GPGGA,{}.000,{:09.4f},{},{:010.4f},{},1,7,1.15,{},M,23.7,M,,*6F'.format(t, lat, lat_half, lon, lon_half, alt)
    gprmc = '$GPRMC,{}.000,A,{:09.4f},{},{:010.4f},{},{:.2f},267.70,{},,,A*6D'.format(t, lat, lat_half, lon, lon_half, speed_over_ground, d)
    exinj = '$EXINJ,{},{},{},{},NA'.format(heading, roll_x, pitch_y, yaw_z)

    return [gpgga, gprmc, exinj]


class UAVAdapterComponent(ApplicationSession):
    def __init__(self, config=None):
        self.serial_port = Serial(args.serial)
        ApplicationSession.__init__(self, config)

    @wamp.register('uav.send_nmea_line')
    async def send_nmea_line(self, line):
        self.serial_port.write('{}\n'.format(line).encode('utf-8'))
        return None

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        while True:
            try:
                self.serial_port = Serial(args.serial)
                logger.info('Connected to serial port {}'.format(args.serial))

                while True:
                    try:
                        if self.serial_port.in_waiting:
                            line = self.serial_port.readline().decode('utf-8').rstrip('\n')

                            logger.debug(line)

                            cmd_id, *data = line.split(',')
                            cmd_id = int(cmd_id)
                            last_cmd = LAST_FG_COMMANDS.get(cmd_id)

                            logger.debug('{} {}'.format(cmd_id, last_cmd))

                            if last_cmd == data:
                                return

                            print('uav.cmd', cmd_id, data)
                            self.publish('uav.cmd', cmd_id, data)

                        await asyncio.sleep(0.5)
                    except (EOFError, ConnectionResetError, BrokenPipeError, KeyError, OSError, SerialException):
                        await asyncio.sleep(5)
                        break
            except SerialException:
                await asyncio.sleep(5)
            finally:
                self.serial_port.close()


def join_to_router(component_class):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(
        CROSSBAR_ROUTE,
        'qgpsemu'
    )

    rerun = True

    while rerun:
        rerun = False

        try:
            runner.run(component_class)
        # except gaierror:
        except OSError:
            # TODO: log about [Errno -3] Temporary failure in name resolution
            rerun = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='NMEA sender and telemetry receiver via serial port',
    )
    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        action='store_true',
        help='Turn on verbose messages',
        default=False
    )
    parser.add_argument(
        '--serial',
        dest='serial',
        help='Send data over a serial port',
        default=None
    )

    args = parser.parse_args(sys.argv[1:])

    if not args.serial:
        logger.error('No comms method specified')
        exit(-1)

    join_to_router(UAVAdapterComponent)