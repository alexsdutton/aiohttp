from inspect import signature

class Signal(object):
    def __init__(self, parameters):
        self._parameters = frozenset(parameters)

    def check_callback_valid(self, callback):
        # Check that the callback can be called with the given parameter names
        signature(callback).bind(**{p: None for p in self._parameters})

class SignalCallbackException(Exception):
    pass

response_start = Signal({'request', 'response'})

