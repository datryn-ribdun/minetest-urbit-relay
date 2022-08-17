#!/usr/bin/env python3
import sys
from aiohttp import web
import aiohttp
import quinnat
import asyncio
import json
import time
import configparser
import re
from multiprocessing import Process

config = configparser.ConfigParser()

config.read("relay.conf")


class Queue:
    def __init__(self):
        self.queue = []

    def add(self, item):
        self.queue.append(item)

    def get(self):
        if len(self.queue) >= 1:
            item = self.queue[0]
            del self.queue[0]
            return item
        else:
            return None

    def get_all_and_clear(self):
        items = self.queue
        self.queue = []
        return items

    def isEmpty(self):
        return len(self.queue) == 0


outgoing_msgs = Queue()

msg = {"author": "dong", "content": "whats up bro"}
outgoing_msgs.add(msg)

SHIP_ADDRESS = config["BOT"]["address_port"]
SHIP_NAME = config["BOT"]["ship"]
SHIP_CODE = config["BOT"]["code"]


def getUrbitClient():
    q = quinnat.Quinnat(SHIP_ADDRESS, SHIP_NAME, SHIP_CODE)
    q.connect()
    return q


group_host = config["RELAY"]["group_host"]
channel_id = config["RELAY"]["channel_id"]

connected = False

port = int(config["RELAY"]["port"])


class FauxUrbitListener:
    @property
    def urbit_client(self):
        return self._urbit_client

    @urbit_client.setter
    def urbit_client(self, value):
        self._urbit_client = value

    def run(self):
        print("hit run over urbit")

        def urbit_action(message, _):
            print("got chat")
            if group_host == message.host_ship:
                if message.resource_name == channel_id:
                    msg = {
                        "author": message.author,
                        "content": message.full_text.replace("\n", "/"),
                    }
                    print("added msg")
                    print(msg)
                    outgoing_msgs.add(msg)

        # self.urbit_client.listen(urbit_action)


def urbit_runner():
    listener = FauxUrbitListener()
    listener.urbit_client = getUrbitClient()
    listener.run()


# def server_runner():
class Server:
    global outgoing_msgs

    @property
    def urbit_client(self):
        return self._urbit_client

    @urbit_client.setter
    def urbit_client(self, value):
        self._urbit_client = value

    def run(self):
        last_request = 0

        def check_timeout():
            return time.time() - last_request <= 1

        async def handle_get_post(request):
            global last_request
            last_request = time.time()
            text = await request.text
            try:
                data = json.loads(text)
                if data["type"] == "URBIT-RELAY-MESSAGE":
                    self.urbit_client.post_message(
                        group_host, channel_id, {"text": data["content"][0:2000]}
                    )
                    # maybe do some parsing to get @p's working, or to avoid chars that could break things
                    # msg = discord.utils.escape_mentions(data['content'])[0:2000]
                    # r = re.compile(r'\x1b(T|F|E|\(T@[^\)]*\))')
                    # msg = r.sub('', msg)
                    return web.Response(
                        text="Acknowledged"
                    )  # urbit.send should NOT block extensively on the Lua side
                if data["type"] == "URBIT-REQUEST-DATA":
                    if not outgoing_msgs.isEmpty():
                        print("we have some outgoing msg to serv")

                    response = json.dumps(
                        {"messages": []}  # outgoing_msgs.get_all_and_clear(),
                    )
                    return web.Response(text=response)
            except:
                pass
            return web.Response(text=None)

        async def runServer():
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "localhost", port)
            await site.start()

            print(f"======= Serving on http://127.0.0.1:{port}/ ======")
            # q.listen(urbit_action)

            # pause here for very long time by serving HTTP requests and
            # waiting for keyboard interruption
            await asyncio.sleep(100 * 3600)

        app = web.Application()
        app.add_routes([web.get("/", handle_get_post), web.post("/", handle_get_post)])
        # print("=" * 37 + "\nStarting relay. Press Ctrl-C to exit.\n" + "=" * 37)
        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(runServer())
        except KeyboardInterrupt:
            pass
        loop.close()


def server_runner():
    listener = Server()
    listener.urbit_client = getUrbitClient()
    listener.run()


urbit_process = Process(target=urbit_runner, args=())
urbit_process.start()
server_process = Process(target=server_runner, args=())
server_process.start()

urbit_process.join()
server_process.join()
