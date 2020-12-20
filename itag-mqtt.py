import subprocess
import sys
import paho.mqtt.client as mqtt
from threading import Thread
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def notify(device, host):
    """Listen for notifications from a device and publish corresponding
    MQTT messages to the broker host.
    """
    # Connect to MQTT broker.
    client = mqtt.Client('itag')
    client.enable_logger(logger)
    client.connect(host)
    client.loop_start()

    proc = subprocess.Popen(
        ['gatttool', '-b', device, '--char-read', '-a', '0x000c', '--listen'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    button_topic = 'itag/{}/button'.format(device)
    connect_topic = 'itag/{}/connect'.format(device)

    try:
        for line in proc.stdout:
            if b'Characteristic' in line:
                print(connect_topic)
                client.publish(connect_topic)
            elif b'Notification' in line:
                print(button_topic)
                client.publish(button_topic)
            elif b'error:' in line:
                print('***', line)
            else:
                print('???', line)
    finally:
        client.loop_stop()


def discover(name='iTAG'):
    """Use hcitool to scan for a device by name and return its MAC
    address.
    """
    proc = subprocess.Popen(
        ['script', '-q', '-c', 'hcitool lescan', '/dev/null'],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=1,
        text=True,
    )

    for line in proc.stdout:
        addr, found_name = line.strip().split(None, 1)
        if name in found_name:
            proc.kill()
            return addr


def main(host, *addrs):
    if addrs:
        # Monitor all the devices specified.
        threads = [Thread(target=notify, args=(addr, host)) for addr in addrs]
        for thread in threads:
            thread.start()
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            pass
    else:
        # Look for a single device and monitor it.
        addr = discover()
        print('discovered', addr)
        try:
            notify(addr, host)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main(*sys.argv[1:])
