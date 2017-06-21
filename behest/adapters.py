import logging
import six
import requests
from behest.plugins import automodel


class HTTPAdapterLoggingHookInterface(object):

    def __init__(self, log, level=logging.DEBUG):
        self.log = log
        self.level = level

    def log_request(self, req):
        raise NotImplementedError

    def log_response(self, resp):
        raise NotImplementedError

    @staticmethod
    def _safe_decode(text, incoming='utf-8', errors='replace'):
        """Decodes incoming text/bytes string using `incoming`
           if they're not already unicode.

        :param incoming: Text's current encoding
        :param errors: Errors handling policy. See here for valid
            values http://docs.python.org/2/library/codecs.html
        :returns: text or a unicode `incoming` encoded
                    representation of it.
        """
        if isinstance(text, six.text_type):
            return text

        return text.decode(incoming, errors)


class NullLoggingHook(HTTPAdapterLoggingHookInterface):

    def __init__(self, *args, **kwargs):
        pass

    def log_request(self, req):
        pass

    def log_response(self, resp):
        pass


class VerboseLoggingHook(HTTPAdapterLoggingHookInterface):

    def log_request(self, req):
        try:
            logline = "REQUEST: {method} {url} headers:{headers}".format(
                method=req.method,
                url=req.url,
                headers=req.headers)
            self.log.log(self.level, self._safe_decode(logline))
        except Exception:
            self.log.exception("REQUEST: An exception occured during logging")

    def log_response(self, resp):
        try:
            logline = (
                "RESPONSE: {status_code} {reason} elapsed:{elapsed}s "
                "headers:{headers}".format(
                    status_code=resp.status_code,
                    reason=resp.reason,
                    elapsed=resp.elapsed.total_seconds(),
                    headers=resp.headers))
            self.log.log(self.level, self._safe_decode(logline))
        except Exception:
            self.log.exception("RESPONSE: An exception occured during logging")


class CafeLoggingHook(HTTPAdapterLoggingHookInterface):

    # def _parse_request_params(self, req):
    #     # Unused
    #     params = None
    #     path_url = None
    #     if hasattr(req, 'path_url'):
    #         try:
    #             params = {
    #                 k:v for k,v in [
    #                     t.split('=') for t in
    #                     req.path_url.lstrip('/?').split('&')]}
    #             req_url = r.request.url.rsplit(req.path_url)[0]
    #         except:
    #             self.log.error(req.path_url)
    #             self.log.exception(
    #                 "An exception occured durring logging while attepting "
    #                 "to parse request parameters")
    #     return params, req_url

    def log_request(self, req):
        request_header = '\n{0}\nREQUEST SENT\n{0}\n'.format('-' * 12)
        logline = ''.join([
            request_header,
            'request method..: {0}\n'.format(req.method),
            'request full url: {0}\n'.format(req.url),
            'request headers.: {0}\n'.format(req.headers),
            'request body....: {0}\n'.format(req.body)])
        try:
            self.log.log(self.level, self._safe_decode(logline))
        except Exception:
            # Ignore all exceptions that happen in logging, then log them
            self.log.log(self.level, request_header)
            self.log.exception("An exception occured during logging")

    def log_response(self, resp):
        response_header = '\n{0}\nRESPONSE RECEIVED\n{0}\n'.format('-' * 17)
        logline = ''.join([
            response_header,
            'response status..: {0} {1}\n'.format(resp, resp.reason),
            'response time....: {0}s\n'.format(resp.elapsed.total_seconds()),
            'response headers.: {0}\n'.format(resp.headers),
            'response body....: {0}\n'.format(resp.content),
            '-' * 79])
        try:
            self.log.log(self.level, self._safe_decode(logline))
        except Exception:
            # Ignore all exceptions that happen in logging, then log them
            self.log.log(self.level, response_header)
            self.log.exception("An exception occured during logging")


class HookableHTTPAdapter(requests.adapters.HTTPAdapter):

    def __init__(self, *args, **kwargs):
        # Defaults to requests lib standard logging
        self._loghook = kwargs.pop('logging_hook', NullLoggingHook())

        # TODO: use a plugin autoloading metaclass pattern to load all the
        #       hooks. Make the loghooks use the same system
        self._response_hooks = []
        self._response_hooks.append(
            automodel.automodel
        )

        super(HookableHTTPAdapter, self).__init__(*args, **kwargs)

    def request_hook(self, request, **kwargs):
        """
        Provides access to the request object immediately before being sent.

        This method should return None
        """
        self._loghook.log_request(request)

    def response_hook(self, response):
        """
        Provides access to the request and response objects immediately before
        returning to the caller.

        This method should return None
        """
        self._loghook.log_response(response)
        for hook in self._response_hooks:
            hook(response)

    def add_headers(self, request, **kwargs):
        """
        This is the last method called in the transport adapter
        before the request is actually sent.  In the base class, it's
        unimplemented.
        I'm using it as an entry point to access or modify the request so that
        I don't have to monkeypatch anything.

        If you need to use it for its intended purpose, it should modify the
        request object directy and return None.
        """
        super(HookableHTTPAdapter, self).add_headers(request, **kwargs)
        self.request_hook(request, **kwargs)
