import subprocess
import sys
import paho.mqtt.client as mqtt


def main(device, host):
    proc = subprocess.Popen(
        ['gatttool', '-b', device, '--char-read', '-a', '0x000c', '--listen'],
        stdout=subprocess.PIPE,
    )

    client = mqtt.Client('itag')
    client.connect(host)
    client.loop_start()

    topic = 'itag/{}/button'.format(device)

    try:
        for line in proc.stdout:
            print(line)
            if b'Notification' in line:
                print(topic)
                client.publish(topic)
    finally:
        client.loop_stop()


if __name__ == '__main__':
    main(*sys.argv[1:])
