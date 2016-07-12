Arrowhead Core Services
***********************

For an introduction to the Arrowhead Framework, see http://www.arrowhead.eu

A Python library for interacting with Arrowhead services, including a CoAP+HTTP
service registry server with IPv6 support.

Quick start
===========

 1. clone the repository
 2. (optional) set up your ``virtualenv``
 3. run ``python setup.py develop``

After installing the dependencies above, to start the server:

    ./sd_server.py

Use ``./sd_server.py --help`` for help

External dependencies
=====================

 - aiocoap - https://github.com/chrysn/aiocoap
 - aiohttp - https://github.com/KeepSafe/aiohttp
 - link_header - https://bitbucket.org/asplake/link_header
 - blitzdb - https://github.com/adewes/blitzdb
