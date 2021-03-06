import subprocess
import sys
import paho.mqtt.client as mqtt
from threading import Thread
import json

DISCOVERY_PREFIX = 'homeassistant'


def _publish(client, topic, payload=None):
    """Publish an MQTT message, and also log it.
    """
    if payload:
        print('{}: {}'.format(topic, payload))
    else:
        print(topic)
    client.publish(topic, payload)


def notify(device, host, announce=False):
    """Listen for notifications from a device and publish corresponding
    MQTT messages to the broker host. If `announce`, then also announce
    the device for Home Assistant discovery.
    """
    # Connect to MQTT broker.
    client = mqtt.Client('itag/{}'.format(device))
    client.connect(host)
    client.loop_start()

    button_topic = 'itag/{}/button'.format(device)
    connect_topic = 'itag/{}/connect'.format(device)
    error_topic = 'itag/{}/error'.format(device)

    # Announce the device for automatic discovery.
    if announce:
        announce_device(client, device, button_topic)

    try:
        while True:
            proc = gatt_listen(device)
            for line in proc.stdout:
                if b'Characteristic' in line:
                    _publish(client, connect_topic)
                elif b'Notification' in line:
                    _publish(client, button_topic)
                elif b'error:' in line:
                    _, msg = line.split(b'error:', 1)
                    msg_txt = msg.strip().decode('utf8', 'ignore')
                    _publish(client, error_topic, msg_txt)
                    proc.kill()
                    break  # Reconnect.
                else:
                    print('???', line)
    finally:
        client.loop_stop()


def gatt_listen(device):
    """Open a `gatttool` subprocess to listen for events from a device.
    """
    return subprocess.Popen(
        ['gatttool', '-b', device, '--char-read', '-a', '0x000c', '--listen'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def announce_device(client, device, button_topic):
    """Announce a newly connected device for Home Assistant discovery.
    """
    name = device.replace(':', '').lower()
    announce_topic = '{}/device_automation/{}/config'.format(
        DISCOVERY_PREFIX,
        name,
    )
    client.publish(announce_topic, json.dumps({
        "automation_type": "trigger",
        "topic": button_topic,
        "type": "button_short_press",
        "subtype": "button_1",
        "device": {
            "name": name,
            "model": "iTag",
            "identifiers": [device],
        },
    }))


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


def main(host, *addrs, discovery=False):
    if addrs:
        # Monitor all the devices specified.
        threads = [Thread(target=notify, args=(addr, host, discovery))
                   for addr in addrs]
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
            notify(addr, host, discovery)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    args = sys.argv[1:]
    if '-d' in args:
        discovery = True
        args.remove('-d')
    main(*args, discovery=discovery)
