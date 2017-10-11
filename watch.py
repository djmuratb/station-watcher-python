#!/usr/bin/env python3

"""
A handy-dandy script that watches radio servers and turns changes into URI webhooks.

Sample usage:
watch.py shoutcast2 http://shoutcast.url/np.json http://azuracast.url/api

ShoutCast 2 desired URI:
http://localhost:8000/statistics?json=1

IceCast 2 desired URI:
http://admin:password@localhost:8000/admin/stats
"""

import sys, logging, time, requests
from requests.models import Response

from adapters import ShoutcastAdapter, IcecastAdapter

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
        logging.error('Not enough parameters! Usage: %s adapters watch_uri report_uri' % __file__)
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
                triggerEvent(report_uri, response)
            else:
                try:
                    is_changed = adapter.compareResponses(previous_result, response)
                    if (is_changed):
                        triggerEvent(report_uri, response)
                except Exception as e:
                    logging.error('Error processing response: %s' % e)
                    time.sleep(3)

            previous_result = response
        else:
            logging.error('Request url "%s" returned status code %d!' % (watch_uri, response.status_code))

        time.sleep(2)
        continue

def triggerEvent(report_uri: str, response: Response):
    logging.info('Webhook POST triggered.')
    webhook_response = requests.post(report_uri, data=response.text)

    if (webhook_response.status_code != 200):
        logging.error('Webhook returned response code %d. Verify API authentication key.' % webhook_response.status_code)
        time.sleep(15)
    return

if __name__ == '__main__':
    # First arg is script name, skip it
    main(sys.argv[1:])