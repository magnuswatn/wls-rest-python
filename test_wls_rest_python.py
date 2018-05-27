try:
    from json.decoder import JSONDecodeError
except ImportError:
    # python2
    JSONDecodeError = ValueError
try:
    from unittest.mock import MagicMock
except ImportError:
    # python2
    from mock import MagicMock

import pytest
import requests_mock

import wls_rest_python

def test_wls_init():
    collection = {
        'version': '17.12.3.1',
        'isLatest': True,
        'lifecycle': 'active',
        'links': [
            {'rel': 'edit', 'href': 'https://edit-link'},
            {'rel': 'domainRuntime', 'href': 'https://domainruntime-link'},
        ],
    }
    with requests_mock.mock() as r:
        r.get(
            'https://wls.example.com:7001/management/weblogic/latest', json=collection
        )
        wls = wls_rest_python.WLS(
            'https://wls.example.com:7001', 'weblogic', 'Welcome1'
        )
    assert wls.isLatest is True
    assert wls.lifecycle == 'active'
    assert wls.version == '17.12.3.1'
    assert wls.timeout == wls_rest_python.DEFAULT_TIMEOUT
    assert wls.edit._url == 'https://edit-link'
    assert wls.session.verify is True
    assert wls.session.auth == ('weblogic', 'Welcome1')
    assert 'X-Requested-By' in wls.session.headers


def test_wls_init_nondefault_version():
    collection = {
        'version': '17.12.3.1',
        'isLatest': False,
        'lifecycle': 'deprecated',
        'links': [
            {'rel': 'edit', 'href': 'https://edit-link'},
            {'rel': 'domainRuntime', 'href': 'https://domainruntime-link'},
        ],
    }
    with requests_mock.mock() as r:
        r.get(
            'https://wls.example.com:7001/management/weblogic/17.12.3.1',
            json=collection,
        )
        wls = wls_rest_python.WLS(
            'https://wls.example.com:7001', 'weblogic', 'Welcome1', version='17.12.3.1'
        )
    assert wls.isLatest is False
    assert wls.lifecycle == 'deprecated'
    assert wls.version == '17.12.3.1'


def test_wls_init_noverify():
    collection = {
        'version': '17.12.3.1',
        'isLatest': True,
        'lifecycle': 'active',
        'links': [
            {'rel': 'edit', 'href': 'https://edit-link'},
            {'rel': 'domainRuntime', 'href': 'https://domainruntime-link'},
        ],
    }
    with requests_mock.mock() as r:
        r.get(
            'https://wls.example.com:7001/management/weblogic/latest', json=collection
        )
        wls = wls_rest_python.WLS(
            'https://wls.example.com:7001', 'weblogic', 'Welcome1', verify=False
        )
    assert wls.session.verify == False

def test_wls_init_nondefault_timeout():
    collection = {
        'version': '17.12.3.1',
        'isLatest': True,
        'lifecycle': 'active',
        'links': [
            {'rel': 'edit', 'href': 'https://edit-link'},
            {'rel': 'domainRuntime', 'href': 'https://domainruntime-link'},
        ],
    }
    with requests_mock.mock() as r:
        r.get(
            'https://wls.example.com:7001/management/weblogic/latest', json=collection
        )
        wls = wls_rest_python.WLS(
            'https://wls.example.com:7001', 'weblogic', 'Welcome1', timeout=832
        )
    assert wls.timeout == 832

def test_wls_get():
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    fake_wls.timeout = 372
    fake_wls.session = MagicMock()
    fake_wls.session.get = MagicMock()
    wls_rest_python.WLS.get(fake_wls, 'https://url', weird_requests_option='hei')
    fake_wls.session.get.assert_called_once_with('https://url', timeout=372,
                                                 weird_requests_option='hei')


def test_wls_post():
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    fake_wls.timeout = 372
    fake_wls.session = MagicMock()
    fake_wls.session.post = MagicMock()
    wls_rest_python.WLS.post(fake_wls, 'https://url', weird_requests_option='hei')
    fake_wls.session.post.assert_called_once_with('https://url', headers=None,
                                                  timeout=372,
                                                  weird_requests_option='hei')


def test_wls_delete():
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    fake_wls.timeout = 372
    fake_wls.session = MagicMock()
    fake_wls.session.delete = MagicMock()
    wls_rest_python.WLS.delete(fake_wls, 'https://url', weird_requests_option='hei')
    fake_wls.session.delete.assert_called_once_with('https://url', headers=None,
                                                    timeout=372,
                                                    weird_requests_option='hei')


def test_wls_handle_response_from_get():
    # it is important that we get the raw json back from GET
    # as otherwise it wil get messy (recursion)
    collection = {
        'name': 'naaame',
        'links': [
            {'rel': 'self', 'href': 'https://self-link'},
        ],
    }
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    response = MagicMock()
    response.ok = True
    # 'get'.upper() to check == and not is
    response.request.method = 'get'.upper()
    response.json = MagicMock(return_value=collection)
    returned = wls_rest_python.WLS._handle_response(fake_wls, response)
    assert returned == collection
    assert not isinstance(returned, wls_rest_python.WLSObject)
    fake_wls._handle_error.assert_not_called()


def test_wls_handle_response_empty():
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    response = MagicMock()
    response.ok = True
    response.json = MagicMock(return_value={})
    assert wls_rest_python.WLS._handle_response(fake_wls, response) is None
    fake_wls._handle_error.assert_not_called()


def test_wls_handle_response_job():
    job = {
        'links': [
            {'rel': 'job', 'href': 'https://joblink'},
        ],
        'name': 'Very important job',
        'state': 'STATE_IN_PROGRESS',
        'progress': 'yes',
        'completed': False,
    }
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    response = MagicMock()
    response.ok = True
    response.json = MagicMock(return_value=job)
    decoded_response = wls_rest_python.WLS._handle_response(fake_wls, response)
    assert decoded_response._name == 'Very important job'
    assert decoded_response._url == 'https://joblink'
    fake_wls._handle_error.assert_not_called()


def test_wls_handle_response_object():
    collection = {
        'items': [
            {
                'links': [{'rel': 'self', 'href': 'https://item-link'}],
                'attr1': True,
                'attr2': 2,
                'attr3': 3,
                'name': 'item_1',
            }
        ],
        'name': 'Random object',
        'property': 'yesyes',
        'links': [
            {'rel': 'action', 'title': 'superAction', 'href': 'https://action-link'},
            {'rel': 'underCollection', 'href': 'https://undercollection-link'},
            {'rel': 'self', 'href': 'https://self-link'},
        ],
    }
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    response = MagicMock()
    response.ok = True
    response.json = MagicMock(return_value=collection)
    decoded_response = wls_rest_python.WLS._handle_response(fake_wls, response)
    assert decoded_response._name == 'Random object'
    assert decoded_response._url == 'https://self-link'
    fake_wls._handle_error.assert_not_called()


def test_wls_handle_response_no_self_link():
    what = {
        'what': True,
        'is': False,
        'this': 'true story',
        'links': [
            {'rel': 'action', 'title': 'superAction', 'href': 'https://action-link'},
            {'rel': 'underCollection', 'href': 'https://undercollection-link'},
        ],
    }
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    response = MagicMock()
    response.ok = True
    response.json = MagicMock(return_value=what)
    decoded_response = wls_rest_python.WLS._handle_response(fake_wls, response)
    assert decoded_response == what
    fake_wls._handle_error.assert_not_called()

def test_wls_handle_response_unknown():
    what = {
        'what': True,
        'is': False,
        'this': 'true story'
    }
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    response = MagicMock()
    response.ok = True
    response.json = MagicMock(return_value=what)
    decoded_response = wls_rest_python.WLS._handle_response(fake_wls, response)
    assert decoded_response == what
    fake_wls._handle_error.assert_not_called()


def test_wls_handle_response_with_error():
    fake_wls = MagicMock(spec=wls_rest_python.WLS)
    fake_wls._handle_error = MagicMock()
    fake_wls._handle_error.side_effect = wls_rest_python.WLSException
    response = MagicMock()
    response.ok = False
    with pytest.raises(wls_rest_python.WLSException):
        wls_rest_python.WLS._handle_response(fake_wls, response)
    fake_wls._handle_error.assert_called_once_with(response)


def test_wls_handle_error_400():
    response = MagicMock()
    response.status_code = 400
    response.json = MagicMock(return_value={'detail': 'insert detail here'})
    with pytest.raises(wls_rest_python.BadRequestException, match='insert detail here'):
        wls_rest_python.WLS._handle_error(response)


def test_wls_handle_error_401():
    response = MagicMock()
    response.status_code = 401
    response.json = MagicMock()
    response.json.side_effect = JSONDecodeError('No json here', '"', 1)
    with pytest.raises(wls_rest_python.UnauthorizedException):
        wls_rest_python.WLS._handle_error(response)


def test_wls_handle_error_403():
    response = MagicMock()
    response.status_code = 403
    response.json = MagicMock(return_value={'detail': 'insert detail here'})
    with pytest.raises(wls_rest_python.ForbiddenException, match='insert detail here'):
        wls_rest_python.WLS._handle_error(response)


def test_wls_handle_error_404():
    response = MagicMock()
    response.status_code = 404
    response.json = MagicMock(return_value={'detail': 'insert detail here'})
    with pytest.raises(wls_rest_python.NotFoundException, match='insert detail here'):
        wls_rest_python.WLS._handle_error(response)


def test_wls_handle_error_405():
    response = MagicMock()
    response.status_code = 405
    response.json = MagicMock(return_value={'detail': 'insert detail here'})
    with pytest.raises(
        wls_rest_python.MethodNotAllowedException, match='insert detail here'
    ):
        wls_rest_python.WLS._handle_error(response)


def test_wls_handle_error_406():
    response = MagicMock()
    response.status_code = 406
    response.json = MagicMock(return_value={'detail': 'insert detail here'})
    with pytest.raises(
        wls_rest_python.NotAcceptableException, match='insert detail here'
    ):
        wls_rest_python.WLS._handle_error(response)


def test_wls_handle_error_500_json():
    response = MagicMock()
    response.status_code = 500
    response.json = MagicMock(return_value={'detail': 'insert detail here'})
    with pytest.raises(
        wls_rest_python.ServerErrorException, match='insert detail here'
    ):
        wls_rest_python.WLS._handle_error(response)


def test_wls_handle_error_500_html():
    response = MagicMock()
    response.status_code = 500
    response.text = 'text here'
    response.json = MagicMock()
    response.json.side_effect = JSONDecodeError('No json here', '"', 1)
    with pytest.raises(wls_rest_python.ServerErrorException, match='text here'):
        wls_rest_python.WLS._handle_error(response)


def test_wls_handle_error_503():
    response = MagicMock()
    response.status_code = 503
    response.json = MagicMock(return_value={'detail': 'insert detail here'})
    with pytest.raises(
        wls_rest_python.ServiceUnavailableException, match='insert detail here'
    ):
        wls_rest_python.WLS._handle_error(response)

def test_wls_handle_unknown_error():
    response = MagicMock()
    response.status_code = 507
    response.json = MagicMock(return_value={'detail': 'whaat'})
    with pytest.raises(
        wls_rest_python.WLSException, match='An unknown error occured. Got status code: 507'
    ):
        wls_rest_python.WLS._handle_error(response)

def test_wls_object_dir():
    collection = {
        'items': [
            {
                'links': [{'rel': 'self', 'href': 'https://self-link'}],
                'attr1': True,
                'attr2': 2,
                'attr3': 3,
                'name': 'item_1',
            }
        ],
        'name': 'navn',
        'property': 'yesyes',
        'links': [
            {'rel': 'action', 'title': 'superAction', 'href': 'https://action-link'},
            {'rel': 'underCollection', 'href': 'https://undercollection-link'},
        ],
    }
    fake_wls = MagicMock()
    fake_wls.get = MagicMock(return_value=collection)
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    for attr in ['property', 'item_1', 'superAction']:
        assert attr in dir(wls_obj)


def test_wls_object_getattr():
    collection = {
        'items': [
            {
                'links': [{'rel': 'self', 'href': 'https://self-link'}],
                'attr1': True,
                'attr2': 2,
                'attr3': 3,
                'name': 'item_1',
            }
        ],
        'name': 'navn',
        'property': 'yesyes',
        'links': [
            {'rel': 'action', 'title': 'superAction', 'href': 'https://action-link'},
            {'rel': 'underCollection', 'href': 'https://undercollection-link'},
        ],
    }
    fake_wls = MagicMock()
    fake_wls.get = MagicMock(return_value=collection)
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    assert wls_obj.property == collection['property']
    assert wls_obj.superAction._url == 'https://action-link'
    assert wls_obj.underCollection._url == 'https://undercollection-link'
    assert isinstance(wls_obj.item_1, wls_rest_python.WLSObject)
    with pytest.raises(AttributeError):
        wls_obj.what

def test_wls_object_getitem():
    collection = {
        'items': [
            {
                'links': [{'rel': 'self', 'href': 'https://self-link'}],
                'attr1': True,
                'attr2': 2,
                'attr3': 3,
                'name': 'item_1',
            }
        ],
        'name': 'navn',
        'property': 'yesyes',
        'links': [
            {'rel': 'action', 'title': 'superAction', 'href': 'https://action-link'},
            {'rel': 'underCollection', 'href': 'https://undercollection-link'},
        ],
    }
    fake_wls = MagicMock()
    fake_wls.get = MagicMock(return_value=collection)
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    assert wls_obj['property'] == collection['property']
    assert wls_obj['superAction']._url == 'https://action-link'
    assert wls_obj['underCollection']._url == 'https://undercollection-link'
    assert isinstance(wls_obj.item_1, wls_rest_python.WLSObject)
    with pytest.raises(KeyError):
        wls_obj['what']

def test_wls_object_iter():
    collection = {
        'items': [
            {
                'links': [{'rel': 'self', 'href': 'https://self-link'}],
                'attr1': True,
                'attr2': 2,
                'attr3': 3,
                'name': 'item 1',
            },
            {
                'links': [{'rel': 'self', 'href': 'https://self-link2'}],
                'attr1': True,
                'attr2': 2,
                'attr3': 3,
                'name': 'item 2',
            },
            {
                'links': [{'rel': 'self', 'href': 'https://self-link3'}],
                'attr1': True,
                'attr2': 2,
                'attr3': 3,
                'name': 'item 3',
            },
        ]
    }
    fake_wls = MagicMock()
    fake_wls.get = MagicMock(return_value=collection)
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    counter = 0
    for item in wls_obj:
        counter += 1
        coll = [x for x in collection['items'] if x['name'] == item._name][0]
        assert item._url == coll['links'][0]['href']
    assert counter == 3


def test_wls_object_non_iter():
    collection = {
        'links': [{'rel': 'self', 'href': 'https://self-link'}],
        'attr1': True,
        'attr2': 2,
        'attr3': 3,
        'name': 'item 1',
    }
    fake_wls = MagicMock()
    fake_wls.get = MagicMock(return_value=collection)
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    with pytest.raises(TypeError):
        for item in wls_obj:
            pass


def test_wls_object_empty_items():
    # If there is an empty item array in the response,
    # it means it is iterable, only withouth objects
    # this should not throw an Exception
    collection = {
        'links': [{'rel': 'self', 'href': 'https://self-link'}],
        'attr1': True,
        'attr2': 2,
        'attr3': 3,
        'name': 'item 1',
        'items': [],
    }
    fake_wls = MagicMock()
    fake_wls.get = MagicMock(return_value=collection)
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    counter = 0
    for item in wls_obj:
        counter += 1
    assert counter == 0


def test_wls_object_delete():
    fake_wls = MagicMock()
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    wls_obj.delete(hei='sann')
    fake_wls.delete.assert_called_once_with('https://url', False, hei='sann')
    wls_obj.delete(prefer_async=True)
    fake_wls.delete.assert_called_with('https://url', True)


def test_wls_object_create():
    fake_wls = MagicMock()
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    wls_obj.create(hei='sann')
    fake_wls.post.assert_called_once_with('https://url', False, hei='sann')
    wls_obj.create(prefer_async=True, important='true')
    fake_wls.post.assert_called_with('https://url', True, important='true')


def test_wls_object_update():
    fake_wls = MagicMock()
    wls_obj = wls_rest_python.WLSObject('name', 'https://url', fake_wls)
    wls_obj.update(hei='sann')
    fake_wls.post.assert_called_once_with('https://url', False, json={'hei': 'sann'})
    wls_obj.update(prefer_async=True, ssl=True)
    fake_wls.post.assert_called_with('https://url', True, json={'ssl': True})


def test_wls_item():
    items = ['item1', 'item2']
    wls_item = wls_rest_python.WLSItems(items)
    assert wls_item.items == items
    assert wls_item.counter == 0
    wls_item.__next__()
    assert wls_item.counter == 1
    # python2
    wls_item.next()
    assert wls_item.counter == 2
    with pytest.raises(StopIteration):
        wls_item.__next__()


def test_wls_action_with_data():
    fake_wls = MagicMock()
    wls_action = wls_rest_python.WLSAction('name', 'https://url', fake_wls)
    action_answer = wls_action(a='b')
    fake_wls.post.assert_called_once_with('https://url', False, json={'a': 'b'})
    assert isinstance(action_answer, MagicMock)


def test_wls_action_no_data():
    fake_wls = MagicMock()
    wls_action = wls_rest_python.WLSAction('name', 'https://url', fake_wls)
    action_answer = wls_action()
    fake_wls.post.assert_called_once_with('https://url', False, json={})
    assert isinstance(action_answer, MagicMock)


def test_wls_action_async():
    fake_wls = MagicMock()
    wls_action = wls_rest_python.WLSAction('name', 'https://url', fake_wls)
    action_answer = wls_action(prefer_async=True)
    fake_wls.post.assert_called_once_with('https://url', True, json={})
    assert isinstance(action_answer, MagicMock)
