#!/usr/bin/env python3

# Sample usage: watch.py shoutcast2 http://shoutcast.url/np.json http://azuracast.url/api

import sys, logging, time, requests

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
        return

def trigger_event(report_uri, event_name, response):
    logging.info('New event triggered: %s' % event_name)
    return

def main(args):
    # Set up logging
    root = logging.getLogger()
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
        'shoutcast2': ShoutcastAdapter
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
                event = adapter.compare_responses(previous_result, response)
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