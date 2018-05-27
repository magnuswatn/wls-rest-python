"""
A Python client for the Weblogic Server REST API.

https://github.com/magnuswatn/wls-rest-python
"""
import logging
import requests

__version__ = '0.1.2'

logger = logging.getLogger(__name__)

# This is quite high, as the WLS server will, by default,
# do operations that take "approximately 5 minutes" synchronous.
DEFAULT_TIMEOUT = 305

class WLSException(Exception):
    """Superclass for exceptions thrown by this module"""
    pass


class BadRequestException(WLSException):
    """
    A REST method returns 400 (BAD REQUEST) if the request failed because
    something is wrong in the specified request, for example, invalid argument values.
    """
    pass


class UnauthorizedException(WLSException):
    """
    A REST method returns 401 (UNAUTHORIZED) if the user does not have permission
    to perform the operation. 401 is also returned if the user supplied incorrect
    credentials (for example, a bad password).
    """
    pass


class ForbiddenException(WLSException):
    """
    A REST method returns 403 (FORBIDDEN) if the user is not in the ADMIN,
    OPERATOR, DEPLOYER or MONITOR role.
    """
    pass


class NotFoundException(WLSException):
    """
    A REST method returns 404 (NOT FOUND) if the requested URL does not refer to an
    existing entity.
    """
    pass


class MethodNotAllowedException(WLSException):
    """
    A REST method returns 405 (METHOD NOT ALLOWED) if the resource exists but
    does not support the HTTP method, for example, if the user tries to create a server by
    using a resource in the domain configuration tree (only the edit tree allows
    configuration editing).
    """
    pass


class NotAcceptableException(WLSException):
    """
    The resource identified by this request is not capable of generating a representation
    corresponding to one of the media types in the Accept header of the request. For
    example, the client's Accept header asks for XML but the resource can only return
    JSON.
    """
    pass


class ServerErrorException(WLSException):
    """
    A REST method returns 500 (INTERNAL SERVER ERROR) if an error occurred that
    is not caused by something wrong in the request. Since the REST layer generally
    treats exceptions thrown by the MBeans as BAD REQUEST, 500 is generally used for
    reporting unexpected exceptions that occur in the REST layer. These responses do not
    include the text of the error or a stack trace, however, generally they are logged in the
    server log.
    """
    pass


class ServiceUnavailableException(WLSException):
    """
    The server is currently unable to handle the request due to temporary overloading or
    maintenance of the server. The WLS REST web application is not currently running.
    """
    pass


class WLS(object):
    """
    Represents a WLS REST server

    :param string host: protocol://hostname:port of the server.
    :param string username: Username used to authenticate against the server
    :param string password: Password used to authenticate against the server
    :param string version: Version of the rest interface to use. Defaults to "latest"
    :param bool verify_ssl: Whether to verify certificates on SSL connections.
    """

    def __init__(self, host, username, password, version='latest', verify=True,
                 timeout=DEFAULT_TIMEOUT):
        self.session = requests.Session()
        self.session.verify = verify
        self.session.auth = (username, password)
        user_agent = 'wls-rest-python {} ({})'.format(
            __version__, self.session.headers['User-Agent']
        )
        self.session.headers.update(
            {'Accept': 'application/json', 'User-Agent': user_agent, 'X-Requested-By': user_agent}
        )
        self.timeout = timeout
        self.base_url = '{}/management/weblogic/{}'.format(host, version)
        collection = self.get(self.base_url)
        self.version = collection['version']
        self.isLatest = collection['isLatest']
        self.lifecycle = collection['lifecycle']
        for link in collection['links']:
            link_obj = WLSObject(link['rel'], link['href'], self)
            setattr(self, link['rel'], link_obj)

    def get(self, url, **kwargs):
        """
        Does a GET request to the specified URL.

        Returns the decoded JSON.
        """
        response = self.session.get(url, timeout=self.timeout, **kwargs)
        return self._handle_response(response)

    def post(self, url, prefer_async=False, **kwargs):
        """
        Does a POST request to the specified URL.

        If the response is a job or an collection, it will return an
        WLSObject. Otherwise it will return the decoded JSON
        """
        headers = {'Prefer': 'respond-async'} if prefer_async else None
        response = self.session.post(url, headers=headers, timeout=self.timeout, **kwargs)
        return self._handle_response(response)

    def delete(self, url, prefer_async=False, **kwargs):
        """
        Does a DELETE request to the specified URL.

        If the response is a job or an collection, it will return an
        WLSObject. Otherwise it will return the decoded JSON
        """
        headers = {'Prefer': 'respond-async'} if prefer_async else None
        response = self.session.delete(url, headers=headers, timeout=self.timeout, **kwargs)
        return self._handle_response(response)

    def _handle_response(self, response):
        logger.debug(
            'Sent %s request to %s, with headers:\n%s\n\nand body:\n%s',
            response.request.method,
            response.request.url,
            '\n'.join(["{0}: {1}".format(k, v) for k, v in response.request.headers.items()]),
            response.request.body,
        )
        logger.debug(
            'Recieved response:\nHTTP %s\n%s\n\n%s',
            response.status_code,
            '\n'.join(["{0}: {1}".format(k, v) for k, v in response.headers.items()]),
            response.content.decode(),
        )

        if not response.ok:
            self._handle_error(response)

        # GET is used by the WLSObject to retrieve the collection
        # so it must return only the decoded JSON, not an WLSobject
        if response.request.method == 'GET':
            return response.json()

        response_json = response.json()
        if not response_json:
            return None

        try:
            link = next((x['href'] for x in response_json['links'] if x['rel'] in ('self', 'job')))
            name = response_json['name']
        except (KeyError, StopIteration):
            # Not a job, and not a collection.
            # Don't know what it is, so just return the decoded json
            return response_json

        return WLSObject(name, link, self)

    @staticmethod
    def _handle_error(response):
        if response.status_code == 400:
            raise BadRequestException(response.json()['detail'])

        if response.status_code == 401:
            # does not return json
            raise UnauthorizedException()

        if response.status_code == 403:
            raise ForbiddenException(response.json()['detail'])

        if response.status_code == 404:
            raise NotFoundException(response.json()['detail'])

        if response.status_code == 405:
            raise MethodNotAllowedException(response.json()['detail'])

        if response.status_code == 406:
            raise NotAcceptableException(response.json()['detail'])

        if response.status_code == 500:
            # may not return json...
            try:
                raise ServerErrorException(response.json()['detail'])
            except ValueError:
                pass
            raise ServerErrorException(response.text)

        if response.status_code == 503:
            raise ServiceUnavailableException(response.json()['detail'])

        raise WLSException(
            'An unknown error occured. Got status code: {}'.format(response.status_code)
        )


class WLSObject(object):
    """
    Represents all the different WLS objects.

    The attributes will differ based on the
    collection used to instantiate it
    """

    def __init__(self, name, url, wls):
        self._name = name
        self._url = url
        self._wls = wls

    def __dir__(self):
        attrs = []
        collection = self._wls.get(self._url)
        for key in collection:
            item = collection[key]
            if key == 'links':
                for link in item:
                    if link['rel'] == 'action':
                        name = link['title']
                    else:
                        name = link['rel']
                    attrs.append(name)
            elif key == 'items':
                for itm in item:
                    attrs.append(itm['name'])
            else:
                attrs.append(key)
        return attrs

    def __getattr__(self, attr):
        """
        Retrieves the properties dynamically from the collection

        We store actions and links for re-use, since they are expected not to change
        """
        collection = self._wls.get(self._url)
        for key in collection:
            item = collection[key]
            if key == 'links':
                for link in item:
                    if link['rel'] == 'action':
                        name = link['title']
                        if name == attr:
                            obj = WLSAction(name, link['href'], self._wls)
                            setattr(self, name, obj)
                            return obj

                    else:
                        name = link['rel']
                        if name == attr:
                            obj = WLSObject(name, link['href'], self._wls)
                            setattr(self, name, obj)
                            return obj

            elif key == 'items':
                for itm in item:
                    if itm['name'] == attr:
                        self_link = next((x['href'] for x in itm['links'] if x['rel'] == 'self'))
                        return WLSObject(itm['name'], self_link, self._wls)

            else:
                if key == attr:
                    return item

        raise AttributeError('\'{}\' object has no attribute \'{}\''.format(self._name, attr))

    def __getitem__(self, key):
        # this is here for items with weird names
        # e.g. webapps with version number (myWebapp#1.2.3)
        try:
            return self.__getattr__(key)
        except AttributeError:
            pass
        raise KeyError(key)

    def __iter__(self):
        collection = self._wls.get(self._url)
        is_iterable = False
        iter_items = []
        for key in collection:
            item = collection[key]
            if key == 'items':
                is_iterable = True
                for itm in item:
                    self_link = next((x['href'] for x in itm['links'] if x['rel'] == 'self'))
                    iter_items.append(WLSObject(itm['name'], self_link, self._wls))
        if is_iterable:
            return WLSItems(iter_items)

        raise TypeError('\'{}\' object is not iterable'.format(self._name))

    def delete(self, prefer_async=False, **kwargs):
        """
        Deletes the resource. Will result in an DELETE request to the self url

        The kwargs are sendt through to requests
        """
        return self._wls.delete(self._url, prefer_async, **kwargs)

    def create(self, prefer_async=False, **kwargs):
        """
        Creates a resource. Will result in an POST request to the self url

        The kwargs are sendt through to requests
        """
        return self._wls.post(self._url, prefer_async, **kwargs)

    def update(self, prefer_async=False, **kwargs):
        """
        Updates an property of the resource.

        The kwargs will be sent as json
        """
        return self._wls.post(self._url, prefer_async, json=kwargs)


class WLSItems(object):
    """
    Items from an object.

    Used as an iterator
    """

    def __init__(self, items):
        self.items = items
        self.counter = 0

    def __next__(self):
        try:
            item = self.items[self.counter]
        except IndexError:
            raise StopIteration

        self.counter += 1
        return item

    def next(self):
        # python 2
        return self.__next__()


class WLSAction(object):
    """
    An action from a collection.

    Identified by a link with rel=action.
    """

    def __init__(self, name, url, wls):
        self._url = url
        self._name = name
        self._wls = wls

    def __call__(self, prefer_async=False, **kwargs):
        return self._wls.post(self._url, prefer_async,
                              json=kwargs if kwargs else {})
