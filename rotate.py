#!/usr/bin/env python

from time import sleep
from os import path as op
import sys
from subprocess import call, check_output
from glob import glob


def bdopen(fname):
    return open(op.join(basedir, fname))


def read(fname):
    return bdopen(fname).read()


def rotate(state):
    s = STATES[state]
    call(['xrandr', '-o', s['rot']])
    for dev in touchscreens if disable_touchpads else (touchscreens + touchpads):
        call([
            'xinput', 'set-prop', dev,
            'Coordinate Transformation Matrix',
        ] + s['coord'].split())
    if disable_touchpads:
        for dev in touchpads:
            call(['xinput', s['touchpad'], dev])


def read_accel(fp):
    fp.seek(0)
    return float(fp.read()) * scale


def find_xdevices():
    devices = check_output(['xinput', '--list', '--name-only']).decode().splitlines()

    touchscreen_names = ['touchscreen', 'wacom']
    touchscreens = [i for i in devices if any(j in i.lower() for j in touchscreen_names)]

    touchpad_names = ['touchpad', 'trackpoint']
    touchpads = [i for i in devices if any(j in i.lower() for j in touchpad_names)]

    return touchscreens, touchpads


def start_rotate_loop():
    current_state = None

    while True:
        x = read_accel(accel_x)
        y = read_accel(accel_y)
        for i in range(4):
            if i != current_state and STATES[i]['check'](x, y):
                current_state = i
                rotate(i)
                break
        sleep(1)


if __name__ == '__main__':
    for basedir in glob('/sys/bus/iio/devices/iio:device*'):
        if 'accel' in read('name'):
            break
    else:
        sys.stderr.write("Can't find an accelerator device!\n")
        sys.exit(1)

    touchscreens, touchpads = find_xdevices()

    scale = float(read('in_accel_scale'))
    g = 7.0 # (m^2 / s) sensibility, gravity trigger

    STATES = [
        {'rot': 'normal', 'coord': '1 0 0 0 1 0 0 0 1', 'touchpad': 'enable',
        'check': lambda x, y: y <= -g},
        {'rot': 'inverted', 'coord': '-1 0 1 0 -1 1 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: y >= g},
        {'rot': 'left', 'coord': '0 -1 1 1 0 0 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: x >= g},
        {'rot': 'right', 'coord': '0 1 0 -1 0 1 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: x <= -g},
    ]

    accel_x = bdopen('in_accel_x_raw')
    accel_y = bdopen('in_accel_y_raw')

    disable_touchpads = False

    start_rotate_loop()
