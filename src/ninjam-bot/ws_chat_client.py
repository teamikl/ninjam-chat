
"""
"""

import logging
from threading import Thread

from autobahn.asyncio.websocket import (
    WebSocketClientProtocol,
    WebSocketClientFactory,
    )

from util import ws_build_msg, queue_loop

logger = logging.getLogger(__name__)


class WSChatClientProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        logger.info('Server connected: {}'.format(response.peer))

    def onOpen(self):
        logger.info('WebSocket connection open.')
        self.factory.client = self
        self.factory.send_queue.put(ws_build_msg('join', 'BOT'))

    def onMessage(self, payload, isBinary):
        if __debug__:
            logger.debug("onMessage {} {} bytes".format("BINARY" if isBinary else "TEXT", len(payload)))

        if isBinary:
            if __debug__:
                logger.info('Binary message received: {} bytes'.format(len(payload)))
        else:
            encoding = self.factory.encoding
            if __debug__:
                logger.info('Text message received: {}'.format(payload.decode(encoding)))
                logger.debug("WS: {}".format(payload))
            if self.factory.queue:
                self.factory.queue.put(("<WS", payload.decode(encoding)))

    def onClose(self, wasClean, code, reason):
        self.factory.client = None
        self.factory.send_queue.put(ws_build_msg('part', 'BOT'))
        logger.info('WebSocket connection closed: {}'.format(reason))


# NOTE: use bot.cfg to override this settings.
# here stay for default failback settings.
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 6789
DEFAULT_ENCODING = 'utf-8'

def worker(queue, send_queue, config):
    host = config.get('host', DEFAULT_HOST)
    port = config.get('port', DEFAULT_PORT)
    encoding = config.get('encoding', DEFAULT_ENCODING)

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
    factory = WebSocketClientFactory('ws://{}:{}'.format(host, port))
    factory.client = None
    factory.protocol = WSChatClientProtocol
    factory.queue = queue
    factory.encoding = encoding
    factory.send_queue = send_queue

    def ws_send_worker(queue, factory):
        for payload in queue_loop(queue):
            if __debug__:
                logger.debug("payload-length: {}".format(len(payload)))
            if factory.client:
                factory.client.sendMessage(payload)
    thread = Thread(target=ws_send_worker, args=(send_queue, factory), daemon=True)
    thread.start()

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, host, port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
