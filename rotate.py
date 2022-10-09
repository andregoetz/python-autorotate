#!/usr/bin/env python
from time import sleep
from os import path as op
import sys
from subprocess import call, check_output
from glob import glob
import re


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


def init_reversed_sink():
    sinks = check_output(['pactl', 'list', 'sinks']).decode()

    if not re.search(check_remapped_re, sinks):
        call(['pactl', 'load-module', 'module-remap-sink', 'sink_name=reverse-stereo', 'master=0', 'channels=2', 'master_channel_map=front-right,front-left', 'channel_map=front-left,front-right'])
        sinks = check_output(['pactl', 'list', 'sinks']).decode()

    sink_ids = re.findall(index_re, sinks)
    return sink_ids


def switch_sink(new_state, current_state, sink_ids):
    s = STATES[new_state]
    cur_s = STATES[new_state if current_state is None else current_state]

    if s['reversed'] and not cur_s['reversed']:
        target_sink = sink_ids[1]
    elif cur_s['reversed'] and not s['reversed']:
        target_sink = sink_ids[0]
    else:
        return

    call(['pactl', 'set-default-sink', target_sink])


def start_rotate_loop():
    current_state = None

    while True:
        x = read_accel(accel_x)
        y = read_accel(accel_y)
        for i in range(4):
            if i != current_state and STATES[i]['check'](x, y):
                rotate(i)
                switch_sink(i, current_state, sink_ids)
                current_state = i
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
        'check': lambda x, y: y <= -g, 'reversed': False},
        {'rot': 'inverted', 'coord': '-1 0 1 0 -1 1 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: y >= g, 'reversed': True},
        {'rot': 'left', 'coord': '0 -1 1 1 0 0 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: x >= g, 'reversed': False},
        {'rot': 'right', 'coord': '0 1 0 -1 0 1 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: x <= -g, 'reversed': False},
    ]

    accel_x = bdopen('in_accel_x_raw')
    accel_y = bdopen('in_accel_y_raw')

    index_re = re.compile('Name: (.+)')
    check_remapped_re = re.compile('Name: reverse-stereo')

    sink_ids = init_reversed_sink()

    disable_touchpads = False

    start_rotate_loop()
