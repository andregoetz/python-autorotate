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


def read_accel(fp):
    fp.seek(0)
    return float(fp.read()) * scale


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


def switch_sink(new_state, cur_state):
    new_s = STATES[new_state]
    cur_s = STATES[cur_state]

    if new_s['sink'] != cur_s['sink']:
        target_sink = sink_ids[new_s['sink']]
        call(['pactl', 'set-default-sink', target_sink])


def find_xdevices():
    devices = check_output(['xinput', '--list', '--name-only']).decode().splitlines()

    touchscreen_names = ['touchscreen', 'wacom']
    touchscreens = [i for i in devices if any(j in i.lower() for j in touchscreen_names)]

    touchpad_names = ['touchpad', 'trackpoint']
    touchpads = [i for i in devices if any(j in i.lower() for j in touchpad_names)]

    return touchscreens, touchpads


def init_reversed_sink():
    reverse_sink = 'reverse-stereo'
    sinks = check_output(['pactl', 'list', 'sinks']).decode()
    sinks = re.findall(re.compile('Name: (.+)'), sinks)

    if reverse_sink not in sinks:
        call(['pactl', 'load-module', 'module-remap-sink', f'sink_name={reverse_sink}', 'master=0', 'channels=2', 'master_channel_map=front-right,front-left', 'channel_map=front-left,front-right'])

    default_sink = check_output(['pactl', 'get-default-sink']).decode().strip()
    if default_sink == reverse_sink:
        default_sink = next(filter(lambda s: s != reverse_sink, sinks))

    return {'default': default_sink, 'reversed': reverse_sink}


def start_rotation_loop():
    current_state = 1 # ensures sink/rotation to be default/normal on first run

    while True:
        x = read_accel(accel_x)
        y = read_accel(accel_y)
        for i in range(4):
            if i != current_state and STATES[i]['check'](x, y):
                rotate(i)
                switch_sink(i, current_state)
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
        'check': lambda x, y: y <= -g, 'sink': 'default'},
        {'rot': 'inverted', 'coord': '-1 0 1 0 -1 1 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: y >= g, 'sink': 'reversed'},
        {'rot': 'left', 'coord': '0 -1 1 1 0 0 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: x >= g, 'sink': 'default'},
        {'rot': 'right', 'coord': '0 1 0 -1 0 1 0 0 1', 'touchpad': 'disable',
        'check': lambda x, y: x <= -g, 'sink': 'default'},
    ]

    accel_x = bdopen('in_accel_x_raw')
    accel_y = bdopen('in_accel_y_raw')

    sink_ids = init_reversed_sink()

    disable_touchpads = False

    start_rotation_loop()
