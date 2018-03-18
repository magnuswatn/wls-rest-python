wls-rest-python
===============

.. image:: https://travis-ci.org/magnuswatn/wls-rest-python.svg?branch=master
    :target: https://travis-ci.org/magnuswatn/wls-rest-python

.. image:: https://codecov.io/gh/magnuswatn/wls-rest-python/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/magnuswatn/wls-rest-python

.. image:: https://badge.fury.io/py/wls-rest-python.svg
    :target: https://badge.fury.io/py/wls-rest-python

This is a Python client for Weblogics RESTful Management Services.
It takes care of some of the quirks with the API, without being so closely
linked that it becomes limiting.

It creates Python objects dynamically based on the response from the server,
so that it's easy to quickly write useful and Pythonic scripts.

It's tested against 12.2.1.2, but should work fine with all 12c R2 releases.

Installation
------------

.. code-block:: bash

    $ pipenv install wls-rest-python



Example usage
-------------

Explore the API, change properties and undeploy applications:

.. code-block:: python

    >>> from wls_rest_python import WLS
    >>> 
    >>> wls = WLS('https://wls.example.com:7001', 'weblogic', 'welcome1')
    >>> 
    >>> dir(wls.edit.batchConfig)
    ['canonical', 'dynamicallyCreated', 'id', 'identity', 'name', 'notes','parent', 'schemaName',
    'self', 'tags', 'type']
    >>> 
    >>> wls.edit.servers.myServer.nativeIOEnabled
    True
    >>> wls.edit.servers.myServer.update(nativeIOEnabled=False)
    >>> wls.edit.servers.myServer.nativeIOEnabled
    False
    >>> wls.domainRuntime.deploymentManager.appDeploymentRuntimes.myApp.getState(target='myServer')
    {'return': 'STATE_ACTIVE'}
    >>> 
    >>> wls.domainRuntime.deploymentManager.appDeploymentRuntimes.myApp.undeploy()
    >>> 


Restart all managed servers asynchronous:

.. code-block:: python

    from wls_rest_python import WLS

    wls = WLS('https://wls.example.com:7001', 'weblogic', 'welcome1')

    admin_server_name = wls.edit.adminServerName

    running_jobs = []
    for server in wls.domainRuntime.serverRuntimes:
        if server.name != admin_server_name:
            running_jobs.append(server.restart(prefer_async=True))

    while running_jobs:
        for job in running_jobs:
            if job.completed:
                running_jobs.remove(job)
        time.sleep(10)


Undeploy all applications and deploy a new:

.. code-block:: python

    import json
    from wls_rest_python import WLS

    wls = WLS('https://wls.example.com:7001', 'weblogic', 'welcome1')

    for deployment in wls.edit.appDeployments:
        deployment.delete()

    deployment_model = {
        'name': 'myWebApp',
        'targets': [
            {'identity': [
                'servers',
                'myServer'
                ]
            }
        ]
    }

    deployment_info = {
        'model': (None, json.dumps(deployment_model)),
        'sourcePath': open('/u01/wars/myWebApp.war', 'rb'),
        'planPath': open('/u01/wars/myWebAppPlan.xml', 'rb')
    }
    wls.edit.appDeployments.create(files=deployment_info)
