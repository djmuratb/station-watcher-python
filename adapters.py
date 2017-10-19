import logging
from requests.models import Response
from xml.dom import minidom

class AbstractAdapter:
    def compareResponses(self, old_response: Response, new_response: Response) -> bool:
        old_comp = self._getComparable(old_response)
        new_comp = self._getComparable(new_response)

        logging.debug('Old response: %s' % old_comp)
        logging.debug('New response: %s' % new_comp)

        return (old_comp != new_comp)

    def _getComparable(self, response: Response):
        return []

class ShoutcastAdapter(AbstractAdapter):
    def _getComparable(self, response: Response):
        json = response.json()
        comparable = []

        for stream in json['streams']:
            comparable.append({
                'title': stream['songtitle'],
                'listeners': int(stream['currentlisteners'])
            })
        return comparable

class IcecastAdapter(AbstractAdapter):
    def _getComparable(self, response: Response):
        xml = minidom.parseString(response.text)
        comparable = []

        streams = xml.getElementsByTagName('source')
        for stream in streams:
            comparable.append({
                'title': self._getText(stream.getElementsByTagName('artist')) + " - " + \
                         self._getText(stream.getElementsByTagName('title')),
                'listeners': int(self._getText(stream.getElementsByTagName('listeners')))
            })

        return comparable

    def _getText(self, elements):
        rc = []

        if (elements):
            for node in elements[0].childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)

        return ''.join(rc)