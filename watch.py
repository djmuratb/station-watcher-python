#!/usr/bin/env python3

#
# A handy-dandy script that watches radio servers and turns changes into URI webhooks.
# Sample usage:
# watch.py shoutcast2 http://shoutcast.url/np.json http://azuracast.url/api
#
# ShoutCast 2 desired URI:
# http://localhost:8000/statistics?json=1
#
# IceCast 2 desired URI:
# http://admin:password@localhost:8000/admin/stats
#

import sys, logging, time, requests
from xml.dom import minidom

class AbstractAdapter:
    def compare_responses(self, old_response, new_response):
        return

class ShoutcastAdapter(AbstractAdapter):
    def compare_responses(self, old_response, new_response):
        old_json = old_response.json()
        new_json = new_response.json()

        for i in range(len(old_json['streams'])):
            old_stream = old_json['streams'][i]
            new_stream = new_json['streams'][i]

            if (old_stream['songtitle'] != new_stream['songtitle']):
                logging.info('Song changed from "%s" to "%s"' % (old_stream['songtitle'], new_stream['songtitle']))
                return 'new_song'
            elif (old_stream['currentlisteners'] != new_stream['currentlisteners']):
                logging.info('Listeners changed from %d to %d' % (old_stream['currentlisteners'], new_stream['currentlisteners']))
                return 'new_listeners'

        return

class IcecastAdapter(AbstractAdapter):

    def compare_responses(self, old_response, new_response):
        old_xml = minidom.parseString(old_response.text)
        new_xml = minidom.parseString(new_response.text)

        old_streams = old_xml.getElementsByTagName('source')
        new_streams = new_xml.getElementsByTagName('source')

        for i in range(len(old_streams)):
            old_stream = old_streams[i]
            new_stream = new_streams[i]

            old_song = self.get_text(old_stream.getElementsByTagName('artist')[0].childNodes) + " - " +\
                       self.get_text(old_stream.getElementsByTagName('title')[0].childNodes)

            new_song = self.get_text(new_stream.getElementsByTagName('artist')[0].childNodes) + " - " +\
                       self.get_text(new_stream.getElementsByTagName('title')[0].childNodes)

            if (old_song != new_song):
                logging.info('Song changed from "%s" to "%s"' % (old_song, new_song))
                return 'new_song'

            old_listeners = int(self.get_text(old_stream.getElementsByTagName('listeners')[0].childNodes))
            new_listeners = int(self.get_text(new_stream.getElementsByTagName('listeners')[0].childNodes))

            if (old_listeners != new_listeners):
                logging.info('Listeners changed from %d to %d' % (old_listeners, new_listeners))
                return 'new_listeners'
        return

    def get_text(self, nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)

def trigger_event(report_uri, event_name, response):
    logging.info('New event triggered: %s' % event_name)
    webhook_response = requests.post(report_uri, data=response.text)

    if (webhook_response.status_code != 200):
        logging.error('Webhook returned response code %d. Verify API authentication key.' % webhook_response.status_code)
        time.sleep(15)
    return

def main(args):
    # Set up logging
    root = logging.getLogger()
    root.name = 'station-watcher'
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Enforce parameters
    if (args.__len__() != 3):
        logging.error('Not enough parameters! Usage: %s adapter watch_uri report_uri' % __file__)
        exit(1)

    adapter_name, watch_uri, report_uri = args

    # A list of all known adapters
    adapters = {
        'shoutcast2': ShoutcastAdapter,
        'icecast': IcecastAdapter
    }

    if (adapter_name not in adapters):
        logging.error('Adapter "%s" not found.' % adapter_name)
        exit(1)

    adapter = adapters[adapter_name]()
    previous_result = None

    while True:
        response = requests.get(watch_uri)

        if (response.status_code == 200):
            if (previous_result is None):
                trigger_event(report_uri, 'new_song', response)
            else:
                try:
                    event = adapter.compare_responses(previous_result, response)
                except IndexError:
                    logging.error('Adapter %s returned IndexError (malformed data?)' % adapter_name)
                    time.sleep(10)
                    continue

                if (event is not None):
                    trigger_event(report_uri, event, response)

            previous_result = response
        else:
            logging.error('Request url "%s" returned status code %d!' % (watch_uri, response.status_code))

        time.sleep(2)
        continue

if __name__ == '__main__':
    # First arg is script name, skip it
    main(sys.argv[1:])