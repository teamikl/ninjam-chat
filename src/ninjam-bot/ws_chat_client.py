
"""
"""

import json
import logging
from autobahn.asyncio.websocket import (
    WebSocketClientProtocol,
    WebSocketClientFactory,
    )

logger = logging.getLogger(__name__)


# TODO: How to send to WSChatServer via Queue ?


class WSChatClientProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        logger.info('Server connected: {}'.format(response.peer))

    def onOpen(self):
        logger.info('WebSocket connection open.')
        self.sendMessage(json.dumps({'type': 'join', 'user': 'BOT'}).encode('utf-8'))

    def onMessage(self, payload, isBinary):
        if __debug__:
            logger.debug("onMessage {} {} bytes".format("BINARY" if isBinary else "TEXT", len(payload)))

        if isBinary:
            logger.info('Binary message received: {} bytes'.format(len(payload)))
        else:
            logger.info('Text message received: {}'.format(payload.decode('utf-8')))

    def onClose(self, wasClean, code, reason):
        logger.info('WebSocket connection closed: {}'.format(reason))


DEFAULT_WS_PORT = 6789

def worker(queue, config):
    port = config.get('port', DEFAULT_WS_PORT)

    if 0:
        # debug asyncio
        logging.basicConfig(level=logging.DEBUG)
    else:
        formatter = logging.Formatter('%(asctime)s %(name)s [%(levelname)s] %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    logger.info("Start main")

    import asyncio
    factory = WebSocketClientFactory('ws://localhost:{}'.format(port))
    factory.protocol = WSChatClientProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, 'localhost', port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
