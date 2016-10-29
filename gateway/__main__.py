import asyncio
import contextlib
from signal import SIGINT, SIGTERM, signal

import multiprocessing

import time
import uvloop

from gateway.http import DictResolver
from gateway.http.dispatcher import HttpDispatcher
from gateway.protocol import GatewayProtocol
# from gateway.bus.rabbit import RabbitDispatcher


def serve(reuse_port=False):
    asyncio.get_event_loop().close()
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def proto_factory():
        resolver = DictResolver(foo='http://localhost:8081')
        http_dispatcher = HttpDispatcher(resolver)
        # rabbit_dispatcher = RabbitDispatcher()
        return GatewayProtocol(loop, dispatcher=http_dispatcher)

    srv_coro = loop.create_server(proto_factory, '0.0.0.0', 8080,
                                  reuse_port=reuse_port)
    srv = loop.run_until_complete(srv_coro)
    print('Listening on: ', srv.sockets[0].getsockname())
    loop.add_signal_handler(SIGINT, loop.stop)
    loop.add_signal_handler(SIGTERM, loop.stop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.close()


def serve_many(workers=1):
    # thank you sanic
    workers = min(workers, multiprocessing.cpu_count())
    event = multiprocessing.Event()
    signal(SIGINT, lambda *_: event.set())
    signal(SIGTERM, lambda *_: event.set())

    processes = []
    kwargs = dict(reuse_port=True)
    for _ in range(workers):
        # noinspection PyArgumentList
        process = multiprocessing.Process(target=serve, kwargs=kwargs,
                                          daemon=True)
        process.start()
        print('Started subprocess:', process.name, process.pid)
        processes.append(process)

    with contextlib.suppress(Exception):
        while not event.is_set():
            time.sleep(0.5)

    [process.terminate() for process in processes]
    [process.join() for process in processes]


if __name__ == '__main__':
    # serve_many(4)
    serve()
