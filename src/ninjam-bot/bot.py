#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
"""
NINJAM <=> Chat gateway


Usage:
    python3.4 bot.py

"""

__author__ = 'tea <Ikkei.Shimomura at gmail dot com>'
__version__ = '0.4.0'

# TODO: JOIN/PART for gui console

import io
import os
import re
import sys
import hashlib
import logging
from cmd import Cmd
from argparse import ArgumentParser
from collections import namedtuple
from struct import Struct, pack, unpack
from socket import socket
from threading import Thread
from multiprocessing import Process, JoinableQueue as Queue
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser


Logger = logging.getLogger(__file__)


##
# NetMsg structure header
# 1 byte for message type
# 4 bytes unsigned int32 for a length of following message payload.
# n bytes data follow as the message payload. (could be zero for keep-alive)

NetMsg = Struct("<BL")


UserInfo = namedtuple(
    "UserInfo",
    "active,index,volume,pan,flags,username,channel")


class NINJAMConnection:
    def __init__(self, host, port, username, password, **config):
        sock = socket()
        sock.connect((host, int(port)))

        self._sock = sock
        self._stream = sock.makefile("rb")
        self.username = username
        self.password = password
        self.config = config
        self.users = {}

    def message_loop(self):
        read = self._stream.read
        for header in iter(lambda: read(5), b''):
            if len(header) < 5:
                if __debug__:
                    Logger.debug("NINJAM Connection lost")
                break
            msgtype, msglen = NetMsg.unpack(header)
            msgbody = read(msglen) if msglen > 0 else b''
            yield msgtype, msgbody

    def sendmsg(self, msgtype, msg):
        if __debug__:
            Logger.debug("NINJAM>{:02X} {}".format(msgtype, msg))
        self._sock.sendall(NetMsg.pack(msgtype, len(msg)) + msg)

    @staticmethod
    def _parse_user_info(data, offset=0):
        assert isinstance(data, bytes)
        view = memoryview(data)
        stream = io.BytesIO(data)

        while len(data) > offset:
            params = unpack("<BBhBB", view[offset:offset+6])
            active, index, volume, pan, flags = params
            offset += 6
            stream.seek(offset, io.SEEK_SET)

            offset = data.find(b"\x00", offset + 1)
            assert offset >= 0
            username = stream.read(offset - stream.tell())
            stream.seek(1, io.SEEK_CUR)

            offset = data.find(b"\x00", offset + 1)
            assert offset >= 0
            channel = stream.read(offset - stream.tell())
            stream.seek(1, io.SEEK_CUR)
            offset += 1

            yield UserInfo(active, index, volume, pan, flags,
                           username, channel)

    @classmethod
    def parse_user_info(cls, data):
        return list(cls._parse_user_info(data))


class IRCConnection:
    def __init__(self, host, port, nick, channel, encoding, **config):
        sock = socket()
        sock.connect((host, int(port)))

        self._sock = sock
        self._stream = sock.makefile("rb")
        self.nick = nick
        self.channel = channel
        self.encoding = encoding
        self.config = config

    def readlines(self):
        while True:
            yield self._stream.readline().decode(self.encoding, "ignore")

    def sendline(self, line):
        line = line.lstrip("\r\n").encode(self.encoding)
        if __debug__:
            Logger.debug("IRC> {}".format(line))
        self._sock.sendall(line + b"\r\n")


# XXX: separate "irc" argument, remove the dependency.
# XXX: assign ninjam.users dictionary is temporary code.
def ninjam_bot(Q, ninjam, irc):
    """
    https://github.com/wahjam/wahjam/wiki/Ninjam-Protocol
    """
    for msgtype, msgbody in ninjam.message_loop():
        if __debug__:
            Logger.debug("{:02X} {}".format(msgtype, msgbody))

        if msgtype == 0x00:  # SERVER AUTH CHALLENGE
            username = ninjam.username.encode("latin-1")
            password = ninjam.password.encode("latin-1")
            challenge, servercaps, protover = unpack("<8sLL", msgbody[:16])
            if __debug__:
                Logger.debug("{} {:08x} {:08x}".format(
                    challenge, servercaps, protover))
            if 0x0002ffff >= protover >= 0x00020000 and (
                    servercaps == 1 or servercaps == 1e01):
                # XXX: ninbot.com servercaps 1e01
                passhash = hashlib.sha1(username + b":" + password).digest()
                passhash = hashlib.sha1(passhash + challenge).digest()
                # CLIENT AUTH USER
                x = pack("<LL", servercaps, protover)
                chunk = passhash + username + b"\x00" + x
                Q.put(("NINJAM", 0x80, chunk))
                del x, chunk
            else:
                break
        elif msgtype == 0x01:  # SERVER AUTH REPLY
            # TODO: error or userlist
            if __debug__:
                Logger.debug(msgbody)
        elif msgtype == 0x02:  # SERVER CONFIG CHANGE NOTIFY
            bpm, bpi = unpack("<HH", msgbody)
            pass
        elif msgtype == 0x03:  # SERVER USERINFO CHANGE NOTIFY
            for info in ninjam.parse_user_info(msgbody):
                ninjam.users[info.username.decode("latin-1")] = 1
        elif msgtype == 0xc0:  # CHAT
            params = msgbody.split(b'\x00')
            assert len(params) == 6
            mode, sender, message, _, _, _ = params
            sender = sender.decode('latin-1')
            if mode == b"MSG":
                # NOTE: skip self message
                username = sender.split("@", 1)[0]
                message = message.decode("utf-8")
                if __debug__:
                    Logger.debug("{} {}".format(username, ninjam.username))
                if username != ninjam.username.split(":")[-1]:
                    msg = "{}> {}".format(sender, message)
                    if irc:
                        Q.put(("IRC",
                               "PRIVMSG {} :{}".format(irc.channel, msg)))
                    Q.put(("GUI",
                           "add_line",
                           "{}@NINJAM> {}".format(username, message)))
            elif mode == b"JOIN":
                ninjam.users[sender] = 1
                if irc:
                    msg = ninjam.config["join_msg"].format(
                        username=sender)
                    Q.put(("IRC", "PRIVMSG {} :{}".format(
                        irc.channel, msg)))
                    Logger.info(msg)
            elif mode == b"PART":
                del ninjam.users[sender]
                if irc:
                    msg = ninjam.config["part_msg"].format(username=sender)
                    Q.put(("IRC", "PRIVMSG {} :{}".format(
                        irc.channel, msg)))
                    Logger.info(msg)
            del params, mode, sender, message
        elif msgtype == 0xfd:  # KEEP-ALIVE
            Q.put(("NINJAM", 0xfd, b""))
        else:
            break


def irc_bot(Q, irc):
    """
    http://tools.ietf.org/html/rfc2812
    """
    sender_name = lambda x: x.lstrip(":").split("!", 1)[0]  # XXX

    for line in irc.readlines():
        if __debug__:
            Logger.debug(repr(line))
        if line.startswith(":"):
            sender, msgtype, rest = line.split(" ", 2)
            if "End of /MOTD command." in rest:  # XXX
                irc.connected = True
                Q.put(("IRC", "JOIN {}".format(irc.channel)))
            elif msgtype == "PRIVMSG":
                _, msg = rest.split(" ", 1)
                message = msg.lstrip(":").strip()
                chunk = "MSG\x00{}@IRC: {}\x00".format(
                    sender_name(sender), message)
                Q.put(("NINJAM", 0xc0, chunk.encode("utf-8")))
                Q.put(("GUI", "add_line",
                       "{}@IRC> {}".format(sender_name(sender), message)))
            elif msgtype == "JOIN" or msgtype == "PART":
                key = "{}_msg".format(msgtype.lower())
                msg = irc.config[key].format(
                    username=sender_name(sender))
                chunk = "MSG\x00{}\x00".format(msg)
                Q.put(("NINJAM", 0xc0, chunk.encode("utf-8")))
                Logger.info(msg)
                del key, msg, chunk
            else:
                pass
        else:
            msgtype, rest = line.split(" ", 1)
            if msgtype == "PING":
                Q.put(("IRC", "PONG {}".format(rest)))
            else:
                pass


def message_loop(queue, bot):
    untuple = lambda x, *xs: (x, xs)

    gui = bot.gui
    irc = bot.irc
    ninjam = bot.ninjam

    while True:
        target, rest = untuple(*queue.get())
        if __debug__:
            Logger.debug("QUEUE: {}".format(target))

        if target == "NINJAM" and ninjam:
            ninjam.sendmsg(*rest)
        elif target == "IRC" and irc:
            irc.sendline(*rest)
        elif target == "GUI" and gui:
            action, args = untuple(*rest)
            method = getattr(gui, action, None)
            if method:
                method(*args)
        queue.task_done()


def start_web_server(app, config):
    """
    XXX: limitation, This function is called in a child thread,
    so may not able to use a database which assume to be run in
    main thread.
    httpd should have it own process, but this is a sample,
    I will go on this quick way.
    """
    from wsgiref.simple_server import make_server

    assert callable(app)
    assert isinstance(config, dict)

    # NOTE: host can be blank or 127.0.0.1 for local, 0.0.0.0 for public
    # recommend setting is bind to local address, and use another httpd
    # as frontend, and mapping proxy for the port.
    httpd = make_server(config['host'], int(config['port']), app)
    httpd.serve_forever()


class AdminShell(Cmd):
    completekey = 'tab'

    def __init__(self, bot=None):
        super(AdminShell, self).__init__()
        self.bot = bot

    def do_quit(self, *args):
        return True


class AdminGui:
    # TODO: redirect stdout logging into tk's console

    def __init__(self, queue=None, shell=None, bot=None):
        self._queue = queue  # XXX: no used now
        self._shell = shell  # XXX: no used now
        self._bot = bot
        self._initialize_components()

    def _initialize_components(self):
        from tkinter import Tk, StringVar
        from tkinter.ttk import Entry
        from tkinter.scrolledtext import ScrolledText as TextArea
        from tkinter.constants import BOTH, BOTTOM

        root = self.root = Tk()
        root.title("bot.py admin console")
        line = self.line = StringVar(root)
        entry = self.entry = Entry(root, textvariable=line)
        entry.pack(side=BOTTOM, fill=BOTH)
        entry.bind('<Return>', self.on_return)
        textarea = self.textarea = TextArea()
        textarea.pack(fill=BOTH, expand=1)

        root.after(100, entry.focus)

    def on_return(self, evt):
        try:
            text = self.line.get()
            if text == "/quit":
                self.root.after(100, self.root.quit)
            elif text.startswith("/"):
                self._shell.onecmd(text.lstrip("/"))
            else:
                bot = self._bot
                bot.send_irc_chat_msg(text)
                bot.send_ninjam_chat_msg(text)
                self.add_line("{}> {}".format("bot.py", text))
        finally:
            self.line.set("")

    def add_line(self, line):
        line = "{}\n".format(line.rstrip())  # ensure line break
        self.root.after(100, lambda: self.textarea.insert('end', line))

    def mainloop(self):
        self.root.mainloop()


class AdminWeb:
    """
    @see WSGI Application
    """
    def __init__(self, bot):
        self.bot = bot

    def __call__(self, environ, start_response):
        start_response('200 Ok', [('Content-type', 'text/html')])
        path_info = environ['PATH_INFO']
        if path_info == "/list":
            yield b"<ul>"
            # XXX: too long dot chain
            for item in self.bot.ninjam.users.keys():
                yield "<li>{}</li>".format(item).encode("utf-8")
            yield b"</ul>"
        else:
            yield b"""<a href="/list">List</a>"""


class Bot:
    __slots__ = ['gui', 'irc', 'ninjam', 'queue']

    def __init__(self, irc=None, ninjam=None, gui=None, queue=None):
        self.gui = gui
        self.irc = irc
        self.ninjam = ninjam
        self.queue = queue  # XXX: no used now

    def send_ninjam_chat_msg(self, msg):
        if self.ninjam:
            chunk = "MSG\x00{}\x00".format(msg)
            self.queue.put(("NINJAM", 0xc0, chunk.encode("utf-8")))

    def send_irc_chat_msg(self, msg):
        if self.irc:
            line = "PRIVMSG {} :{}".format(self.irc.channel, msg)
            self.queue.put(("IRC", line.strip()))


def main():
    # init logging
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(LOG_FORMAT)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    Logger.setLevel(logging.DEBUG)
    Logger.addHandler(handler)

    # Init config dictionary
    config = ConfigParser()
    config.read("bot.cfg")
    ninjam_config = config['ninjam']
    irc_config = config['irc']
    httpd_config = config['httpd']
    config_enable = config['enable']

    # Init command line arguments parser
    parser = ArgumentParser()
    parser.add_argument(
        '--tk',
        action='store_true',
        help='show admin GUI console')
    parser.add_argument(
        '--httpd',
        type=int,
        default=8080,
        help='enable httpd')
    parser.add_argument(
        '--ws',
        action='store_true',
        help='enable websocket connection')
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='NINJAM Bot v{}'.format(__version__))
    args = parser.parse_args()

    # Override config by command line arguments.
    if args.tk:
        config_enable['tk'] = "1"
    if args.ws:
        config_enable['ws'] = "1"
    if args.httpd > 0:
        config_enable['httpd'] = "1"
        httpd_config['port'] = str(args.httpd)

    # XXX: being deep dependency each classes.
    queue = Queue()
    bot = Bot(queue=queue)
    shell = AdminShell(bot=bot)

    def _make_daemon(init):
        def _init_daemon(**kw):
            obj = init(**kw)
            obj.setDaemon(True)
            return obj
        return _init_daemon
    make_daemon_thread = _make_daemon(Thread)
    make_daemon_process = _make_daemon(Process)

    if int(config_enable['tk']):
        gui = bot.gui = AdminGui(queue=queue, shell=shell, bot=bot)
    else:
        gui = None

    if int(config_enable['irc']):
        nick = irc_config['nick']
        irc = bot.irc = IRCConnection(**irc_config)
        irc.sendline("NICK {}".format(nick))
        irc.sendline("USER {0} * * :{0}".format(nick))
        irc_thread = make_daemon_thread(target=irc_bot, args=(queue, irc))
        irc_thread.start()
    else:
        irc = None

    if int(config_enable['ninjam']):
        ninjam = bot.ninjam = NINJAMConnection(**ninjam_config)
        ninjam_thread = make_daemon_thread(
            target=ninjam_bot, args=(queue, ninjam, irc))
        ninjam_thread.start()
    else:
        ninjam = None

    if int(config_enable['httpd']):
        app = AdminWeb(bot)
        httpd_thread = make_daemon_thread(
            target=start_web_server, args=(app, dict(httpd_config)))
        httpd_thread.start()

    if int(config_enable['ws']):
        # TODO
        pass

    if 1:  # Worker thread should always be enable
        worker_thread = make_daemon_thread(
            target=message_loop, args=(queue, bot))
        worker_thread.start()

    if gui:
        gui.mainloop()
    else:
        shell.cmdloop()


if __name__ == "__main__":
    main()
