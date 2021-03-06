import asyncio
from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import random
import os
import logging

os.environ["PYTHONASYNCIODEBUG"] = "True"
logging.basicConfig(level=logging.DEBUG)


class MyServerProtocol(WebSocketServerProtocol):
    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")
        print("Setting up comms task")
        clients[id(self)] = self

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received from client: {0} bytes".format(len(payload)))
        else:
            print("Text message received from client: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        del clients[id(self)]


def accept_client(client_reader, client_writer):
    task = asyncio.Task(handle_client(client_reader, client_writer))
    clients[task] = (client_reader, client_writer)

    def client_done(task):
        print("Finishing task: {}".format(task))
        del clients[task]

    task.add_done_callback(client_done)


@asyncio.coroutine
def handle_client(client_writer):
    while True:
        data = yield from q.get()
        client_writer(data.encode('utf-8'))


@asyncio.coroutine
def handle_clients():
    while True:
        if clients:
            data = yield from q.get()
            for id, client in clients.items():
                client.sendMessage(data.encode('utf-8'))
        else:
            yield

@asyncio.coroutine
def random_data_generator(id):
    while True:
        rnd = random.randint(0, 50) / 10
        yield from asyncio.sleep(random.randint(0, 50) / 10)
        yield from q.put("Sleeped: {}s ID {}".format(rnd, id))


loop = asyncio.get_event_loop()
clients = {}
q = asyncio.Queue()
factory = WebSocketServerFactory("ws://localhost:9000", debug=False)
factory.protocol = MyServerProtocol
my_tasks = [loop.create_task(random_data_generator(x)) for x in range(10)]
loop.create_task(handle_clients())

f = loop.create_server(factory, '0.0.0.0', 9000)
server = loop.run_until_complete(f)
loop.run_forever()
