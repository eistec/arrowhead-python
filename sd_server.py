#!/usr/bin/env python3

import logging
import argparse

import asyncio
import ipaddress

from arrowhead.servicedirectory import ServiceDirectory
from arrowhead.servicedirectory import coap
from arrowhead.servicedirectory import http

loglevels = [logging.CRITICAL, logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]

def main(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument('-f', '--dbfile', type=str, metavar='FILE', default='directory_db',
                        help="Service directory database filename")
    parser.add_argument("-v", "--verbosity", type=int, default=4,
                        help="set logging verbosity, 1=CRITICAL, 5=DEBUG")
    parser.add_argument("--coap-port", type=int, default=5683,
                        help="CoAP port, use 0 to disable")
    parser.add_argument("--coap-bind", default='::',
                        help="CoAP server bind address")
    parser.add_argument("--http-port", type=int, default=8080,
                        help="HTTP port, use 0 to disable")
    parser.add_argument("--http-bind", default='::',
                        help="HTTP server bind address")
    args = parser.parse_args()

    # logging setup
    logging.basicConfig(level=loglevels[args.verbosity-1])
    # selective log levels
    #logging.getLogger("coap-server").setLevel(logging.DEBUG)
    #logging.getLogger("arrowhead").setLevel(logging.DEBUG)

    directory = ServiceDirectory(args.dbfile)

    loop = asyncio.get_event_loop()

    if args.coap_port:
        # aiocoap only supports IPv6 sockets, use ::ffff:123.45.67.89 for
        # listening on IPv4 addresses
        coap_addr = ipaddress.ip_address(args.coap_bind)
        if isinstance(coap_addr, ipaddress.IPv4Address):
            coap_bind = '::ffff:' + str(coap_addr)
        else:
            coap_bind = str(coap_addr)
        # TODO: Update this when aiocoap 0.3 is released on PyPi (loop support)
        #coap_server = coap.Server(directory=directory, loop=loop)
        coap_server = coap.Server(directory=directory, bind=(coap_bind, args.coap_port))
        asyncio.async(coap_server.context)
    if args.http_port:
        http_directory = http.Server(directory=directory, loop=loop)
        http_handler = http_directory.make_handler()
        http_server = loop.create_server(http_handler, host=args.http_bind,
            port=args.http_port)
        asyncio.async(http_server)

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    import sys
    main(sys.argv)
