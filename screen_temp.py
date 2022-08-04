#!/bin/python3

"""
Copyright 2022 SpookedByRoaches

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from ast import Raise
from datetime import datetime, timedelta
from PIL import Image
from pystray import MenuItem as Item, Icon, Menu
from os import path as path, _exit as osExit
from subprocess import check_output, STDOUT
from configparser import ConfigParser
from sys import argv
from threading import Thread
from time import sleep


config_loc = "YOUR LOCATION"

my_loc = path.dirname(__file__)
file_splitter = "/"

POISON = 6969


class Temp_Pair:
    def __init__(self, time_begin, time_end, temp_begin, temp_end, name):
        hours = self.__convert_to_hours([time_begin, time_end])
        self.start_time = hours[0]
        self.end_time = hours[1]
        self.start_temp = int(temp_begin)
        self.end_temp = int(temp_end)
        self.name = name
        if (self.end_time < self.start_time):
            self.end_time += timedelta(days=1)
            self.did_rollover = True
        else:
            self.did_rollover = False

    def __convert_to_hours(self, in_list):
        out_times = []
        for in_value in in_list:
            in_t = datetime.strptime(in_value, "%H:%M")
            out_times.append(in_t - in_t.replace(hour=0,
                             minute=0, second=0, microsecond=0))
        return out_times

    def calc_redshift_temp(self, cur_time):
        if(not self.is_within_period(cur_time)):
            return POISON
        t_since_midnight = (
            cur_time - cur_time.replace(hour=0, minute=0, second=0, microsecond=0))
        t_since_midnight = self.__rollover_cur_t(t_since_midnight)
        time_diff_sec = (self.end_time - self.start_time).total_seconds()
        time_since_begin_sec = (
            t_since_midnight - self.start_time).total_seconds()
        temp_diff = self.end_temp - self.start_temp
        out_temp = ((time_since_begin_sec/time_diff_sec)
                    * temp_diff) + self.start_temp
        return out_temp

    def __rollover_cur_t(self, cur_time):
        if (not self.did_rollover):
            return cur_time
        unrolled_end_t = self.end_time - timedelta(days=1)
        if (cur_time <= unrolled_end_t):
            return cur_time + timedelta(days=1)
        else:
            return cur_time

    def is_within_period(self, cur_time):
        t_since_midnight = (
            cur_time - cur_time.replace(hour=0, minute=0, second=0, microsecond=0))
        if (self.did_rollover):
            end_time_after_midnight = self.end_time - timedelta(days=1)
            if ((t_since_midnight < self.start_time) and (t_since_midnight > end_time_after_midnight)):
                return False
            else:
                return True
        else:
            if ((t_since_midnight < self.start_time) or (t_since_midnight > self.end_time)):
                return False
            else:
                return True


def logic_test(m_pair, n_pair):
    for i in range(0, 24):
        for j in range(0, 56, 5):
            cur_t_str = "{hours:02d}{minutes:02d}".format(hours=i, minutes=j)
            cur_t = datetime.strptime(cur_t_str, "%H%M")
            if(n_pair.is_within_period(cur_t)):
                cur_temp = n_pair.calc_redshift_temp(cur_t)
                print("Time = {cur_t_str} | Temp = {cur_temp}".format(
                    cur_t_str=cur_t_str, cur_temp=cur_temp))
            elif(m_pair.is_within_period(cur_t)):
                cur_temp = m_pair.calc_redshift_temp(cur_t)
                print("Time = {cur_t_str} | Temp = {cur_temp}".format(
                    cur_t_str=cur_t_str, cur_temp=cur_temp))
            else:
                print("{cur_t_str} No change".format(cur_t_str=cur_t_str))


def testing():
    cur_time = datetime.now()
    pairs = get_pairs_list(config_loc)
    minute_diffs = 1
    for i in range(int(24*60/minute_diffs)):
        cur_time += timedelta(minutes=minute_diffs)
        str_time = cur_time.strftime("%H:%M")

        applicable_pair = get_applicable_pair(pairs, cur_time)
        if (applicable_pair == None):
            before = get_closest_before(pairs, cur_time)
            if (before != ''):
                cur_temp = before.end_temp
            else:
                cur_temp = "cuck"
            print("Temp = {cur_temp} | Time = {cur_t}".format(
                cur_temp=cur_temp, cur_t=str_time))
            continue
        cur_temp = applicable_pair.calc_redshift_temp(cur_time)
        print("Temp = {cur_temp} | Time = {cur_t}".format(
            cur_temp=cur_temp, cur_t=str_time))


def smooth_transition(start, end):
    cur_temp = start
    def msleep(x): return sleep(x/1000.0)
    delta = end - start
    for i in range(int(abs(delta))):
        check_output(
            "DISPLAY=:0;redshift -O  {cur_temp} -P".format(cur_temp=cur_temp), shell=True)
        cur_temp += delta / abs(delta)
        msleep(10)


def immediate_change(cur_temp):
    check_output(
        "DISPLAY=:0;redshift -O  {cur_temp} -P".format(cur_temp=cur_temp), shell=True)


def get_pairs_list(config_fname):
    config = ConfigParser()
    config.read(config_fname)
    pairs = []
    for user_pair in config.sections():
        start_temp = int(config[user_pair]["start_temp"])
        end_temp = int(config[user_pair]["end_temp"])
        start_time = config[user_pair]["start_time"]
        end_time = config[user_pair]["end_time"]
        pairs.append(Temp_Pair(start_time, end_time,
                     start_temp, end_temp, user_pair))
    return pairs


def user_smooth_trans():
    if (len(argv) != 4):
        print("Incorrect number of arguments")
        return
    try:
        start = int(argv[2])
    except ValueError:
        print("Start temp is invalid: {}".format(argv[2]))
        exit()
    try:
        end = int(argv[3])
    except ValueError:
        print("End temp is invalid: {}".format(argv[3]))
        exit()
    if (start > 6500 or start < 1000 or end > 6500 or end < 1000):
        print("Temperature should not be less than 1000 or more than 6500")
        exit()
    smooth_transition(start, end)


def do_other_stuff():
    if (argv[1] == "-t"):
        testing()
    elif (argv[1] == "-h"):
        print("Alls you can do at the moment is run the actual script without any arguments or test using: -t")
    elif (argv[1] == "-st"):
        user_smooth_trans()
    elif (argv[1] == "-q"):
        print_cur_temp()
    else:
        print("Unsupported argument only can to testing: -t or debugging")


def get_applicable_pair(pairs, cur_time):
    applicable_pair = None
    for pair in pairs:
        if (pair.is_within_period(cur_time)):
            applicable_pair = pair
            break
    return applicable_pair


def get_closest_after(pairs, cur_time):
    best_pair = ""
    best_delta = timedelta(days=1)
    zero_time = timedelta()
    cur_time = cur_time - \
        cur_time.replace(hour=0, minute=0, second=0, microsecond=0)
    for pair in pairs:
        this_delta = pair.start_time - cur_time

        # this_delta -= datetime(1900, 1, 1)
        if (this_delta < best_delta and this_delta > zero_time):
            best_delta = this_delta
            best_pair = pair
    return best_pair


def is_too_early(pairs, cur_time):
    zero_time = timedelta()
    for pair in pairs:
        this_delta = cur_time - pair.end_time

        if (this_delta >= zero_time):
            return False
    return True


def get_closest_before(pairs, cur_time):
    best_pair = ""
    best_delta = timedelta(days=1)
    zero_time = timedelta()
    cur_time = cur_time - \
        cur_time.replace(hour=0, minute=0, second=0, microsecond=0)
    if (is_too_early(pairs, cur_time)):
        cur_time += timedelta(days=1)
    for pair in pairs:
        end_time = pair.end_time
        this_delta = cur_time - end_time
        if (this_delta < best_delta and this_delta >= zero_time):
            best_delta = this_delta
            best_pair = pair
    if (best_pair == ""):
        raise ValueError(
            "get_closest_before: Failed to get the closest time period before now")
    return best_pair


def test_between():
    minute_diffs = 60
    cur_time = datetime.now()
    pairs = get_pairs_list(config_loc)
    for i in range(int(24*60/minute_diffs)):
        cur_time += timedelta(minutes=minute_diffs)
        str_time = cur_time.strftime("%H:%M")

        applicable_pair = get_applicable_pair(pairs, cur_time)
        if (applicable_pair != None):
            print("Transitioning into the {}".format(applicable_pair.name))
            continue
        closest_before = get_closest_before(pairs, cur_time)
        closest_after = get_closest_after(pairs, cur_time)
        print("The closest pair before {time} is {pair} with a temp of {temp}".format(
            time=str_time, pair=closest_before.name, temp=str(closest_before.end_temp)))


def exit_program(icon, item):
    osExit(0)

def get_screen_status():
    return check_output("xset q", stderr=STDOUT, shell=True).decode("utf-8")

def is_screen_on():
    return "Monitor" in get_screen_status()

def handle_tray():
    image_loc = my_loc + file_splitter + "res" + file_splitter + "sunset.png"
    image = Image.open(image_loc)
    print(image_loc)
    menu = Menu(
        Item('Quit', exit_program)
    )
    icon = Icon("Screen Temp", image, "Screen Temp", menu)
    icon.run()


def print_cur_temp():
    pairs = get_pairs_list(config_loc)
    cur_time = datetime.now()
    before = get_closest_before(pairs, cur_time)
    applicable_pair = get_applicable_pair(pairs, cur_time)
    if (applicable_pair == None):
        before = get_closest_before(pairs, cur_time)
        cur_temp = before.end_temp
    else:
        cur_temp = applicable_pair.calc_redshift_temp(cur_time)
    print("The current temperature should be {}".format(cur_temp))


if __name__ == "__main__":
    if (len(argv) != 1):
        do_other_stuff()
        exit()
    pairs = get_pairs_list(config_loc)
    th = Thread(target=handle_tray)
    th.start()
    cur_temp = 0
    prev_temp = 0
    was_monitor_on = True
    while True:
        is_monitor_on = is_screen_on()
        monitor_turned_on = is_monitor_on and (not was_monitor_on)
        cur_time = datetime.now()
        str_time = cur_time.strftime("%H:%M")
        five_ago = cur_time - timedelta(minutes=5)
        str_ago = five_ago.strftime("%H:%M")
        applicable_pair = get_applicable_pair(pairs, cur_time)
        if (is_monitor_on):    
            if (applicable_pair == None):
                before = get_closest_before(pairs, cur_time)
                if (before != ''):
                    cur_temp = before.end_temp
                    if ((cur_temp != prev_temp) or monitor_turned_on):
                        immediate_change(cur_temp)
            else:
                cur_temp = applicable_pair.calc_redshift_temp(cur_time)
                if ((cur_temp != prev_temp) or monitor_turned_on):
                    immediate_change(cur_temp)
        # print("Temp = {cur_temp} | Time = {cur_t}".format(cur_temp=cur_temp, cur_t = str_time))
        sleep(1.0)
        prev_temp = cur_temp
        was_monitor_on = is_monitor_on
