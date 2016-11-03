.. image:: https://img.shields.io/travis/wickedasp/gateway/master.svg?style=flat-square
    :target: https://travis-ci.org/wickedasp/gateway

.. image:: https://img.shields.io/pypi/l/wasp-gateway.svg?style=flat-square
    :target: https://github.com/wickedasp/gateway/blob/master/LICENSE

.. image:: https://img.shields.io/pypi/v/wasp-gateway.svg?style=flat-square
    :target: https://pypi.python.org/pypi/wasp-gateway

.. image:: https://img.shields.io/pypi/status/wasp-gateway.svg?style=flat-square
    :target: https://pypi.python.org/pypi/wasp-gateway

.. image:: https://img.shields.io/pypi/pyversions/wasp-gateway.svg?style=flat-square
    :target: https://pypi.python.org/pypi/wasp-gateway

WASP Gateway
============

A gateway is used as a single entry point into a microservice based system, abstracting away the fact that there may be an infinite number of services in the system.

WASP is built to be a cohesive ecosystem, but you are free to write back-end applications in any framework that speaks the DispatchStrategy you choose.

Dispatch Strategies
-------------------

Dispatcher strategies define how the gateway transforms the REST calls for the backend systems. Effectively the gateway acts as a translator.

We support two common strategies for dispatching:

* HTTP Rest: Effectively the gateway is a proxy to dynamic services
    * Fastest, but requires some sort of "service discovery", which adds complexity to systems.
* Service BUS: The gateway buffers all requests and places them onto a service BUS, awaiting responses and sending them back via HTTP
    * Reduced coupling, backend systems will be more "reactive" and don't need to be web-services at all.

HTTP Rest
~~~~~~~~~

In this strategy, the gateway acts as a proxy. Quite literally, the data is streamed to and from the target. This does depend on the usage of more components - specifically some sort of *service discovery* mechanism (Consul, Eureka, etc.).

This should be the *fastest strategy* as no data is buffered in either direction, instead it is simply streamed through as data is available on the socket.

Service Resolvers
_________________

A service resolver translates the request into a target url, the resolver can use anything from the request to identify the target system.

WASP takes the opinion that URL path resolves the service name and uses the remainder of the path to request a path on the remote server.

``/foo/bar/baz`` -> ``service: foo, remote path: /bar/baz``

Supported ServiceResolvers:

* ``DictResolver``: This is only really suitable for testing, as it is not dynamically updated as services come in and out of service.
* ``EurekaResolver``: This uses Netflix's Eureka server - TODO This will be an external package on pypi
* ``...``

Service BUS
~~~~~~~~~~~

The gateway is a translator in both directions, it loads the request data and translates it into messages for your service bus. Once a result comes back from the bus, it is loaded again and dumped to the waiting client.

Supported BUSAdapters:

* ``RabbitMQ`` TODO This will be an external package on pypi

The service bus does not need to resolve any services, instead it simply places topics on an exchange (or similar construct) and awaits responses. This effectively depends on two things:

1. A pre-defined naming strategy is agreed upon
    - Similar to the HTTP way, the target exchange is resolved from something about the request
    - Our opinionated way uses the first part of the HTTP Path as the exchange.
    - Similar to HTTP, messages have a "path" construct (for RabbitMQ this is the *topic*)
2. A queue is bound to the target exchange with the provided routing strategy (topic)
    - Our opinionated way uses the rest of the path as the routing key, with dots as the ``/`` and the query string becomes a header param ``X-WASP-QS``

Service BUS Routing
___________________

Routing translates all the HTTP Rest components into RabbitMQ Components:

.. code-block::

    METHOD <path><query_string>
    HEADERS

    Request Body

These are translated as:

* ``X-WASP-METHOD`` - an added Header: Http Request Method
* ``X-WASP-QS`` - an added header: Http Path Query String
* Rabbit Exchange: First path segment in the HTTP Request
* Rabbit Routing Key: Rest of the path, with full stops replacing slashes
* Rabbit Body: HTTP Request body, if any included. Otherwise empty

Example routing:

``GET /foo/bar/baz?page=1&size=20``:

* Exchange: ``foo``
* Routing Key: ``bar.baz``
* Header: ``X-WASP-QS: page=1&size=20``
* Header: ``X-WASP-METHOD: GET``

Note that with exchanges, any number of queues can be bound and they will all get the message. You need to ensure that only one queue is used for the actual request processing and all workers that can respond listen to that queue. Any other listeners, of course, are free to use the data received (metrics, logging, etc.) - but shouldn't respond to the response queue. 

Limitations
-----------

The gateway is built to be as fast as possible (well, eventually anyway :), and focused 100% on routing HTTP requests into a backend system.

As a result, there are intentionally omitted features at the moment:

* No SSE support
* No Web Socket support
