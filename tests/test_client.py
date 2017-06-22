import unittest
import logging
import httpretty
from requests.sessions import Session
from requests.adapters import HTTPAdapter
from behest.client import HTTPClient
from behest.adapters import \
    HookableHTTPAdapter, VerboseLoggingHook, CafeLoggingHook
from contextlib import contextmanager


class TestFixture(unittest.TestCase):

    @contextmanager
    def assertDoesNotRaise(self, msg=None, exception=Exception):
        try:
            yield
        except exception:
            self.fail("Unexpected Exception: Assertion Failed")


class HTTPClient_Tests(TestFixture):

    def test_init_with_no_arguments_works(self):
        with self.assertDoesNotRaise():
            HTTPClient()

    def test_init_kwarg_default_HTTPAdapter_is_HookableHTTPAdapter(self):
        httpc = HTTPClient()
        self.assertIsInstance(httpc._http_adapter, HookableHTTPAdapter)

    def test_init_kwarg_default_logging_hook_is_VerboseLoggingHook(self):
        httpc = HTTPClient()
        self.assertIsInstance(httpc._http_adapter._loghook, VerboseLoggingHook)

    def test_init_accepts_user_defined_HTTPAdapter(self):
        adapter = HTTPAdapter()
        httpc = HTTPClient(http_adapter=adapter)
        self.assertIsInstance(httpc._http_adapter, HTTPAdapter)

    def test_init_accepts_user_defined_LoggingHook(self):
        hook = CafeLoggingHook(logging.getLogger())
        httpc = HTTPClient(logging_hook=hook)
        self.assertIsInstance(httpc._http_adapter._loghook, CafeLoggingHook)

    def test_persistent_session_instantiation(self):
        httpc = HTTPClient(persistent_session=True)
        self.assertIsInstance(httpc._session, Session)

    def test_persistent_session_mounted_hooks(self):
        httpc = HTTPClient(persistent_session=True)
        for adapter_mount_point in httpc._session.adapters.keys():
            self.assertIsInstance(
                httpc._session.adapters[adapter_mount_point],
                HookableHTTPAdapter)


class _HTTP_RequestTestsMixin(object):

    def assertExpectedResponseBodyRecieved(self, response):
        if response.text != self.testbody:
            msg = (
                "Malformed response body:\nexpected: "
                "{e}\nrecieved:{r}".format(
                    e=self.testbody, r=response.content))
            self.fail(msg)

    @httpretty.activate
    def _request_test(self, verb):
        httpretty.register_uri(
            getattr(httpretty, verb), self.testurl, body=self.testbody)
        self.assertExpectedResponseBodyRecieved(
            self.httpc.request(verb, self.testurl))

    def test_GET(self):
        self._request_test('GET')

    def test_POST(self):
        self._request_test('POST')

    def test_PUT(self):
        self._request_test('PUT')

    def test_DELETE(self):
        self._request_test('DELETE')

    def test_OPTIONS(self):
        self._request_test('OPTIONS')

    def test_PATCH(self):
        self._request_test('PATCH')

    @httpretty.activate
    def test_HEAD(self):
        httpretty.register_uri(
            httpretty.HEAD, self.testurl, headers={"HEADER": "VALUE"})
        r = self.httpc.request('HEAD', self.testurl)
        headers = r.headers.get('headers')
        self.assertEqual(headers, "{'HEADER': 'VALUE'}")

    # @httpretty.activate
    # def test_COPY(self):
    #     httpretty.register_uri('COPY', self.testurl)
    #     r = self.httpc.request('COPY', self.testurl)


class _HTTP_RequestAliasesTestsMixin(object):

    def assertExpectedResponseBodyRecieved(self, response):
        if response.text != self.testbody:
            self.fail("request received incorrect response body")

    @httpretty.activate
    def _request_test(self, verb):
        method = getattr(self.httpc, '_{}'.format(verb.lower()))
        httpretty.register_uri(
            getattr(httpretty, verb), self.testurl, body=self.testbody)
        self.assertExpectedResponseBodyRecieved(
            method(self.testurl))

    def test_alias_GET(self):
        self._request_test('GET')

    def test_alias_POST(self):
        self._request_test('POST')

    def test_alias_PUT(self):
        self._request_test('PUT')

    def test_alias_DELETE(self):
        self._request_test('DELETE')

    def test_alias_OPTIONS(self):
        self._request_test('OPTIONS')

    def test_alias_PATCH(self):
        self._request_test('PATCH')

    @httpretty.activate
    def test_alias_HEAD(self):
        httpretty.register_uri(
            httpretty.HEAD, self.testurl, headers={"HEADER": "VALUE"})
        r = self.httpc.request('HEAD', self.testurl)
        headers = r.headers.get('headers')
        self.assertEqual(headers, "{'HEADER': 'VALUE'}")

    # @httpretty.activate
    # def test_alias_COPY(self):
    #     httpretty.register_uri('COPY', self.testurl)
    #     r = self.httpc.request('COPY', self.testurl)


class HTTPClient_NonPersistentRequestTests_http(
        _HTTP_RequestAliasesTestsMixin, unittest.TestCase):
    testurl = "http://test.test/"
    testbody = "BODY"

    def setUp(self):
        self.httpc = HTTPClient()


class HTTPClient_RequestAliasTests(
        _HTTP_RequestTestsMixin, unittest.TestCase):
    testurl = "http://test.test/"
    testbody = "BODY"

    def setUp(self):
        self.httpc = HTTPClient()


class HTTPClient_NonPersistentRequestTests_https(
        _HTTP_RequestTestsMixin, unittest.TestCase):
    testurl = "https://test.test/"
    testbody = "BODY"

    def setUp(self):
        self.httpc = HTTPClient()


class HTTPClient_PersistentRequestTests_http(
        _HTTP_RequestTestsMixin, unittest.TestCase):
    testurl = "http://test.test/"
    testbody = "BODY"

    def setUp(self):
        self.httpc = HTTPClient(persistent_session=True)
        # self.session_id = id(self.httpc._session)
        # TODO Figure out a way to grab the session id() from inside the
        # request method to guarantee that we're using the persistent
        # session.  This may be overkill.


class HTTPClient_PersistentRequestTests_https(
        _HTTP_RequestTestsMixin, unittest.TestCase):
    testurl = "https://test.test/"
    testbody = "BODY"

    def setUp(self):
        self.httpc = HTTPClient(persistent_session=True)


"""
TODO
test persistent session (make sure it's using the stored session)
test instantiation of all defined
test logging with all defined hooks
test http vs https requests with and without hook
test request and response hook methods and all hooks that use those methods
test all the log_request and log_response methods in all logging hooks
test _safe_decode
test all the verb-methods in HTTPClient
"""
