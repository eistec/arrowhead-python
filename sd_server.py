#!/usr/bin/env python3

# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

import datetime
import logging

import asyncio

import aiocoap.resource as resource
import aiocoap

from arrowhead.core.servicediscovery.coap import ServiceResource,  PublishResource, UnpublishResource, TypeResource, ParentSite
from arrowhead.core.servicediscovery.directory import ServiceDirectory

class TimeResource(resource.ObservableResource):
    """
    Example resource that can be observed. The `notify` method keeps scheduling
    itself, and calles `update_state` to trigger sending notifications.
    """
    def __init__(self):
        super(TimeResource, self).__init__()

        self.notify()

    def notify(self):
        self.updated_state()
        asyncio.get_event_loop().call_later(6, self.notify)

    def update_observation_count(self, count):
        if count:
            # not that it's actually implemented like that here -- unconditional updating works just as well
            print("Keeping the clock nearby to trigger observations")
        else:
            print("Stowing away the clock until someone asks again")

    @asyncio.coroutine
    def render_get(self, request):
        payload = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode('ascii')
        return aiocoap.Message(code=aiocoap.CONTENT, payload=payload)

# logging setup

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

def main():
    directory = ServiceDirectory('directory_db.json')
    # Resource tree creation
    root = ParentSite()

    root.add_resource(('.well-known', 'core'), resource.WKCResource(root.get_resources_as_linkheader))

    root.add_resource(('time',), TimeResource())

    root.add_resource(('servicediscovery', 'service'), ServiceResource(directory=directory))
    root.add_resource(('servicediscovery', 'publish'), PublishResource(directory=directory))
    root.add_resource(('servicediscovery', 'unpublish'), UnpublishResource(directory=directory))
    root.add_resource(('servicediscovery', 'type'), TypeResource(directory=directory))

    asyncio.async(aiocoap.Context.create_server_context(root))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
