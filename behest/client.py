import logging
import requests
from requests.packages import urllib3
from behest.adapters import HookableHTTPAdapter, VerboseLoggingHook

logging.getLogger("requests").setLevel(logging.WARNING)
urllib3.disable_warnings()


class HTTPClient(BaseClass):

    def __init__(self, *args, **kwargs):

        # The base class sets up a "classproperty" that instantiates the
        # _log object
        super(HTTPClient, self).__init__()

        # TODO: Separate the HTTPAdapter instantiation from the client so that
        # users can pass-in/choose/plugin/configure whatever behavior with
        # their own adapter.
        # Maybe make this a default.  tl;dr: maybe it shouldn't be the
        # HTTPClient's responisbility to instantiate the hooks for the adapter.
        logging_hook = kwargs.pop(
            'logging_hook', VerboseLoggingHook(self._log))
        self._http_adapter = kwargs.pop(
            'http_adapter', HookableHTTPAdapter(logging_hook=logging_hook))

        # Note: I'm not sure what a good sane default here would be.
        # I defaulted to not having a persistent session to emulate how the
        # client worked before.
        self._session = None
        if kwargs.pop('persistent_session', False):
            self._session = requests.sessions.Session()
            self._session.mount('https://', self._http_adapter)
            self._session.mount('http://', self._http_adapter)

    def request(self, method, url, **kwargs):
        """A copy of the request method in requsts.api that mounts a custom
        pluggable HTTPAdapter to the session (either ephemeral or persistent)

        Takes the same parameters as requests.api.request()
        """

        if self._session:
            return self._session.request(method=method, url=url, **kwargs)

        with requests.sessions.Session() as session:
            session.mount('https://', self._http_adapter)
            session.mount('http://', self._http_adapter)
            r = session.request(method=method, url=url, **kwargs)

            # Requests lets the session modify the response after
            # build_response gets called, so the response hook has to either
            # tie into request's deprecated response hook system, or go here.

            self._http_adapter.response_hook(r)
            return r

    # The verbs methods are here to duplicate requests.api interface
    def _put(self, url, **kwargs):
        """ HTTP PUT request """
        return self.request('PUT', url, **kwargs)

    def _copy(self, url, **kwargs):
        """ HTTP COPY request """
        return self.request('COPY', url, **kwargs)

    def _post(self, url, data=None, **kwargs):
        """ HTTP POST request """
        return self.request('POST', url, data=data, **kwargs)

    def _get(self, url, **kwargs):
        """ HTTP GET request """
        return self.request('GET', url, **kwargs)

    def _head(self, url, **kwargs):
        """ HTTP HEAD request """
        return self.request('HEAD', url, **kwargs)

    def _delete(self, url, **kwargs):
        """ HTTP DELETE request """
        return self.request('DELETE', url, **kwargs)

    def _options(self, url, **kwargs):
        """ HTTP OPTIONS request """
        return self.request('OPTIONS', url, **kwargs)

    def _patch(self, url, **kwargs):
        """ HTTP PATCH request """
        return self.request('PATCH', url, **kwargs)
