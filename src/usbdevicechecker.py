#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2023 Toyohiko Komatsu (dragonkomat)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -*- coding: utf-8 -*-

import argparse
import re
import signal
import subprocess
import sys
import os
from datetime import datetime, timedelta
import logging
import time
#import pdb

#[475025.659793] usb 1-1.3: device descriptor read/64, error -110
RE_DMESG_TRIGGER = re.compile(r'^\[.*?\] usb 1-([0-9.]+): .*? error (-[0-9]+)$')
USBDEV='usb1'
INTERVAL_AFTER_MATCH=timedelta(seconds=60)

log:'logging.Logger' = None

def signal_handler(signum, frame):

    log.error(f'Signal handler called with signal {signum}.')
    log.error('Terminate...')
    sys.exit(1)

def reset():
    subprocess.run('systemctl stop dump1090-fa', shell=True)
    subprocess.run(f'echo {USBDEV} > /sys/bus/usb/drivers/usb/unbind', shell=True)
    time.sleep(1)
    subprocess.run(f'echo {USBDEV} > /sys/bus/usb/drivers/usb/bind', shell=True)
    subprocess.run('systemctl start dump1090-fa', shell=True)

def main():

    lastmatchtime = datetime.now() - INTERVAL_AFTER_MATCH

    # メインループ
    while True:

        log.info('dmesg process starting...')

        try:
            
            # dmesgコマンドの実行
            with subprocess.Popen(
                    ['stdbuf','-oL','dmesg','-w','--noescape','-P']
                    ,stdout=subprocess.PIPE
                    ,stderr=subprocess.DEVNULL
                    ,bufsize=0
                    ,text=True ) as dmesg:

                log.info('dmesg process started. Wait for receiving logs...')

                # dmesgの出力を読み込む
                for line in dmesg.stdout:

                    # エラーメッセージの処理
                    r = re.match(RE_DMESG_TRIGGER, line)
                    if r is not None:
                        currenttime = datetime.now()
                        if (currenttime - lastmatchtime) >= INTERVAL_AFTER_MATCH:
                            log.info('usb error detected. Resetting...')
                            reset()
                            log.info('reset completed.')
                            lastmatchtime = currenttime
                        continue

        except Exception as e:
            log.exception(e)
            log.error('dmesg process occurred exception! Terminate...')
            sys.exit(3)

        # dmesgが終了してしまった場合は5秒待ってから再度実行
        log.warning('dmesg process terminated. Retry after 5 seconds...')
        time.sleep(5)

if __name__ == '__main__':

    # stdout/stderrを行バッファモードにする
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

    # シグナルハンドラの登録
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # コマンドパラメーターの解析
    parser = argparse.ArgumentParser()
    parser.add_argument('-l',action='store',dest='log_level',default=logging.INFO)
    args = parser.parse_args()

    # ログの準備
    log = logging.getLogger('log')
    log_handler = logging.StreamHandler()   # sys.stderr
    log_formatter = logging.Formatter('%(levelname)s: %(message)s')
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)
    log.setLevel(args.log_level)

    main()
