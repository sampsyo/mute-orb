import subprocess
import sys
import paho.mqtt.client as mqtt


def notify(device, client):
    proc = subprocess.Popen(
        ['gatttool', '-b', device, '--char-read', '-a', '0x000c', '--listen'],
        stdout=subprocess.PIPE,
    )

    button_topic = 'itag/{}/button'.format(device)
    connect_topic = 'itag/{}/connect'.format(device)

    for line in proc.stdout:
        if b'Characteristic' in line:
            print(connect_topic)
            client.publish(connect_topic)
        elif b'Notification' in line:
            print(button_topic)
            client.publish(button_topic)


def main(device, host):
    client = mqtt.Client('itag')
    client.connect(host)
    client.loop_start()

    try:
        notify(device, client)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()


if __name__ == '__main__':
    main(*sys.argv[1:])
