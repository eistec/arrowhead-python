Service Oriented Architecture
*****************************

... using the Arrowhead Framework Core services.

*For an introduction to the Arrowhead Framework, see http://www.arrowhead.eu*

A Python library for interacting with Arrowhead services, including a CoAP+HTTP
service registry server with IPv6 support.

Development
===========

This code is released as open source, the main development repository is hosted
on GitHub at https://github.com/eistec/arrowhead-python

For guidelines on contributing to the project, see `CONTRIBUTING <https://github.com/eistec/arrowhead-python/blob/master/CONTRIBUTING.rst>`_

Licensing
=========

Released under the Arrowhead Framework Licensing terms, which is a dual license
Eclipse Public License and Apache License v2.0. For more details, see the
`LICENSE.txt
<https://github.com/eistec/arrowhead-python/blob/master/LICENSE.txt>`_ file in
this repository.

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
