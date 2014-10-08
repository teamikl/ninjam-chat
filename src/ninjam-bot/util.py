

import json


def ws_parse_msg(payload):
    return json.loads(payload)


def ws_pack_msg(msg, encoding='utf-8'):
    assert isinstance(msg, dict)
    return json.dumps(msg).encode(encoding)


def ws_build_msg(msgtype, username, text="", *, pack=ws_pack_msg):
    # NOTE: flag for avoid echo back ws message.
    assert msgtype in {'join', 'part', 'chat'}
    msg = {'type': msgtype, 'user': username, 'flag': 1}
    if text:
        msg['text'] = text
    return pack(msg)


def queue_loop(queue):
    for task in iter(queue.get, None):
        yield task
        queue.task_done()
    else:
        queue.task_done()


# XXX: this was for 2.x
untuple = lambda x, *xs: (x, xs)


import functools
import unicodedata
normalize = functools.partial(unicodedata.normalize, 'NFKC')
