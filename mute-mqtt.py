import sys
import paho.mqtt.client as mqtt
import subprocess


MUTE_TOGGLE_SCRIPT = """
var se = Application('System Events');
var zoom_se = se.processes.byName('zoom.us');
var meeting_menu = zoom_se.menuBars[0].menuBarItems.byName('Meeting');
var meeting_items = meeting_menu.menus[0].menuItems;

// A try/catch block is a little faster than an explicit check. A side
// effect is that the first option we try is slightly faster than the
// second. Unmuting seems a little more urgent.
var mute_item = meeting_items.byName('Mute Audio');
var unmute_item = meeting_items.byName('Unmute Audio');
try {
    unmute_item.click();
} catch (e) {
    mute_item.click();
}
"""


def osascript(script):
    # You'll need to give Terminal "Accessibility" privileges.
    res = subprocess.run(
        ['osascript', '-l', 'JavaScript', '-'],
        input=script.encode('utf8'),
        capture_output=True,
        check=True,
    )
    return res.stdout


def main(host, topic):
    client = mqtt.Client('mute')
    client.connect(host)

    def on_message(client, data, msg):
        print('toggle')
        osascript(MUTE_TOGGLE_SCRIPT)

    client.on_message = on_message
    client.subscribe(topic)

    client.loop_forever()


if __name__ == '__main__':
    main(*sys.argv[1:])
