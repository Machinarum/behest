import json
import types

try:
    # Python 3
    from types import SimpleNamespace as _Namespace
except ImportError:
    # Python 2.x fallback
    from argparse import Namespace as _Namespace


class Namespace(_Namespace):
    def __getitem__(self, item):
        return self.__dict__[item]


def automodel(response):
    """
    Injects a function into the Response object that gets returned by requests.
    The fuunction, automodel, deserializes the response content, if available,
    to json, but uses a SimpleNamespace object (Namespace in python 2.X)
    instead of dicts, allowing dotted access to the data structure.

    The parsing is performed once and cached for future automodel calls on
    the response object.
    """
    def _automodel(self):
        if hasattr(self, '__automodel__'):
            return self.__automodel__

        def obj_hook(d):
            """
            Filters out breaking key-names before passing data into Namespace
            TODO:  Make this more generic in the future, it'd be nice if users
            could define their own filter/renaming functions to facilitate
            complex mappings of strings to dot-addressable-object-names.
            """
            try:
                if 'self' in d.keys():
                    d['self_'] = d['self']
                    del d['self']
            except:
                pass
            return Namespace(**d)

        model = json.loads(self.content, object_hook=obj_hook)
        setattr(self, '__automodel__', model)
        return model

    response.automodel = types.MethodType(_automodel, response)
