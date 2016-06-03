"""Test input data"""

EXAMPLE_SERVICES = {
    'SingleService1': {
        'service': {
            "name": "orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.",
            "type": "_orch-s-ws-https._tcp",
            "domain": "arces.unibo.it.",
            "host": "bedework.arces.unibo.it.",
            "port": 8181,
            "properties": {
                "version": "1.0",
                "path": "/orchestration/store/"
            }
        },
        'as_json': '''
            {
                "name": "orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.",
                "type": "_orch-s-ws-https._tcp",
                "domain": "arces.unibo.it.",
                "host": "bedework.arces.unibo.it.",
                "port": 8181,
                "properties": {
                    "property": [
                        {
                            "name": "version",
                            "value": "1.0"
                        },
                        {
                            "name": "path",
                            "value": "/orchestration/store/"
                        }
                    ]
                }
            }''',
        'as_xml': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        '''
    },
    'SingleService2': {
        'service': {
            "name": "anotherprinterservice._printer-s-ws-https._tcp.srv.arces.unibo.it.",
            "type": "_printer-s-ws-https._tcp",
            "domain": "168.56.101.",
            "host": "192.168.56.101.",
            "port": 8055,
            "properties": {
                "version": "1.0",
                "path": "/printer/something"
            }
        },
        'as_json': '''
            {
                "name": "anotherprinterservice._printer-s-ws-https._tcp.srv.arces.unibo.it.",
                "type": "_printer-s-ws-https._tcp",
                "domain": "168.56.101.",
                "host": "192.168.56.101.",
                "port": 8055,
                "properties": {
                    "property": [
                        {
                            "name": "version",
                            "value": "1.0"
                        },
                        {
                            "name": "path",
                            "value": "/printer/something"
                        }
                    ]
                }
            }
        ''',
        'as_xml': '''
            <service>
                <domain>168.56.101.</domain>
                <host>192.168.56.101.</host>
                <name>anotherprinterservice._printer-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8055</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/printer/something</value>
                    </property>
                </properties>
                <type>_printer-s-ws-https._tcp</type>
            </service>
        '''
    }
}

BROKEN_SERVICES = {
    'missing name': {
        'service': {
            "type": "_orch-s-ws-https._tcp",
            "domain": "arces.unibo.it.",
            "host": "bedework.arces.unibo.it.",
            "port": 8181,
            "properties": {
                "version": "1.0",
                "path": "/orchestration/store/"
            }
        },
        'as_json': '''
            {
                "type": "_orch-s-ws-https._tcp",
                "domain": "arces.unibo.it.",
                "host": "bedework.arces.unibo.it.",
                "port": 8181,
                "properties": {
                    "property": [
                        {
                            "name": "version",
                            "value": "1.0"
                        },
                        {
                            "name": "path",
                            "value": "/orchestration/store/"
                        }
                    ]
                }
            }''',
        'as_xml': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        '''
    },
}

BROKEN_XML = {
    'XML syntax error': '''
            <service>
                <domain>arces.unibo.it.</domain
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML duplicate tags': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <domain>unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML nested tags': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name></host>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML nested props': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML nested props2': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <value><name>path</name>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML duplicate props': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                    <property>
                        <name>version</name>
                        <value>1.1</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML missing prop value': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML missing prop name': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML extra tags': '''
            <service>
                <foo>hej</foo>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
    'XML extra props': '''
            <service>
                <foo>hej</foo>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <nmae>version</nmae>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        ''',
}
