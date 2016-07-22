#!/usr/bin/env python
"""Example how to query an Arrowhead Service Directory"""

import logging
import argparse
import sys
import asyncio

# for pretty-printing the results
from pprint import pprint

def print_results(browser):
    pprint(browser.services, indent=4, width=160)

loglevels = [logging.CRITICAL, logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]

from soa import ServiceDirectoryBrowser

@asyncio.coroutine
def main(argv=None):
    """Program main entry point"""
    parser = argparse.ArgumentParser(argv)
    parser.add_argument("-v", "--verbosity", type=int, default=4,
                        help="set logging verbosity, 1=CRITICAL, 5=DEBUG")
    parser.add_argument('url', nargs='?', default='coap://[::1]/servicediscovery/service',
                        help="URL to service directory")
    args = parser.parse_args()

    # logging setup
    logging.basicConfig(level=loglevels[args.verbosity-1])

    sdb = ServiceDirectoryBrowser(uri=args.url, notify=print_results)
    yield from sdb.start_observe()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main(sys.argv))
