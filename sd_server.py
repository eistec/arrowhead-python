#!/usr/bin/env python3

# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

import logging
import argparse

import asyncio

import aiocoap.resource as resource
import aiocoap

from arrowhead.servicedirectory import ServiceDirectory
from arrowhead.servicedirectory import coap

loglevels = [logging.CRITICAL, logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]

def main(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument('-f', '--dbfile', type=str, metavar='FILE', default='directory_db.json',
                        help="Service directory database filename")
    parser.add_argument("-v", "--verbosity", type=int, default=3,
                        help="set logging verbosity, 0=CRITICAL, 5=DEBUG")
    args = parser.parse_args()

    # logging setup
    logging.basicConfig(level=loglevels[args.verbosity])
    # selective log levels
    #logging.getLogger("coap-server").setLevel(logging.DEBUG)
    #logging.getLogger("arrowhead").setLevel(logging.DEBUG)

    directory = ServiceDirectory(args.dbfile)
    # Resource tree creation
    root = coap.ParentSite()

    root.add_resource(('.well-known', 'core'), resource.WKCResource(root.get_resources_as_linkheader))

    root.add_resource(('servicediscovery', 'service'), coap.ServiceResource(directory=directory))
    root.add_resource(('servicediscovery', 'publish'), coap.PublishResource(directory=directory))
    root.add_resource(('servicediscovery', 'unpublish'), coap.UnpublishResource(directory=directory))
    root.add_resource(('servicediscovery', 'type'), coap.TypeResource(directory=directory))

    asyncio.async(aiocoap.Context.create_server_context(root))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    import sys
    main(sys.argv)
