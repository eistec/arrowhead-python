#!/usr/bin/env python3

import logging
import argparse

import asyncio

import aiocoap.resource as resource
import aiocoap

from arrowhead.servicedirectory import ServiceDirectory
from arrowhead.servicedirectory import coap
from arrowhead.servicedirectory import http

loglevels = [logging.CRITICAL, logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]

def main(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument('-f', '--dbfile', type=str, metavar='FILE', default='directory_db.json',
                        help="Service directory database filename")
    parser.add_argument("-v", "--verbosity", type=int, default=4,
                        help="set logging verbosity, 1=CRITICAL, 5=DEBUG")
    parser.add_argument("--httpport", type=int, default=8080,
                        help="HTTP port, use 0 to disable")
    parser.add_argument("--http-host", default='::',
                        help="HTTP server bind address")
    parser.add_argument("--coapport", type=int, default=5683,
                        help="CoAP port, use 0 to disable")
    args = parser.parse_args()

    # logging setup
    logging.basicConfig(level=loglevels[args.verbosity-1])
    # selective log levels
    #logging.getLogger("coap-server").setLevel(logging.DEBUG)
    #logging.getLogger("arrowhead").setLevel(logging.DEBUG)

    directory = ServiceDirectory(args.dbfile)

    loop = asyncio.get_event_loop()

    if args.coapport:
        # TODO: Update this when aiocoap 0.3 is released on PyPi (loop support)
        #coap_server = coap.Server(directory=directory, loop=loop)
        coap_server = coap.Server(directory=directory)
        asyncio.async(coap_server.context)
    if args.httpport:
        http_directory = http.Server(directory=directory, loop=loop)
        http_handler = http_directory.make_handler()
        http_server = loop.create_server(http_handler, host=args.http_host,
            port=args.httpport)
        asyncio.async(http_server)

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    import sys
    main(sys.argv)
