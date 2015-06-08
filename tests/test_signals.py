import asyncio
import unittest
from unittest import mock
from aiohttp.multidict import CIMultiDict
from aiohttp.signals import Signal, response_start
from aiohttp.web import Application
from aiohttp.web import Request, StreamResponse, Response
from aiohttp.protocol import HttpVersion, HttpVersion11, HttpVersion10
from aiohttp.protocol import RawRequestMessage

class TestSignals(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()

    def make_request(self, method, path, headers=CIMultiDict()):
        message = RawRequestMessage(method, path, HttpVersion11, headers,
                                    False, False)
        return self.request_from_message(message)

    def request_from_message(self, message):
        self.app = mock.Mock()
        self.payload = mock.Mock()
        self.transport = mock.Mock()
        self.reader = mock.Mock()
        self.writer = mock.Mock()
        req = Request(self.app, message, self.payload,
                      self.transport, self.reader, self.writer)
        return req

    def test_callback_valid(self):
        signal = Signal({'foo', 'bar'})

        # All these are suitable
        good_callbacks = [
            (lambda foo, bar: None),
            (lambda *, foo, bar: None),
            (lambda foo, bar, **kwargs: None),
            (lambda foo, bar, baz=None: None),
            (lambda baz=None, *, foo, bar: None),
            (lambda foo=None, bar=None: None),
            (lambda foo, bar=None, *, baz=None: None),
            (lambda **kwargs: None),
        ]
        for callback in good_callbacks:
            signal.check_callback_valid(callback)

    def test_callback_invalid(self):
        signal = Signal({'foo', 'bar'})

        # All these are unsuitable
        bad_callbacks = [
            (lambda foo: None),
            (lambda foo, bar, baz: None),
        ]
        for callback in bad_callbacks:
            with self.assertRaises(TypeError):
                signal.check_callback_valid(callback)

    def test_add_signal_handler(self):
        signal = Signal({'foo', 'bar'})
        callback = lambda foo, bar: None
        app = Application(loop=self.loop)
        app.add_signal_handler(signal, callback)

    def test_add_signal_handler_not_a_signal(self):
        signal = object()
        callback = lambda foo, bar: None
        app = Application(loop=self.loop)
        with self.assertRaises(TypeError):
            app.add_signal_handler(signal, callback)

    def test_add_signal_handler_not_a_callable(self):
        signal = Signal({'foo', 'bar'})
        callback = True
        app = Application(loop=self.loop)
        with self.assertRaises(TypeError):
            app.add_signal_handler(signal, callback)

    def test_signal_dispatch(self):
        signal = Signal({'foo', 'bar'})
        kwargs = {'foo': 1, 'bar': 2}

        callback_mock = mock.Mock()
        callback = lambda **kwargs: callback_mock(**kwargs)

        app = Application(loop=self.loop)
        app.add_signal_handler(signal, callback)

        self.loop.run_until_complete(app.dispatch_signal(signal, kwargs))
        callback_mock.assert_called_once_with(**kwargs)

    def test_response_start(self):
        callback_mock = mock.Mock()
        callback = lambda **kwargs: callback_mock(**kwargs)

        app = Application(loop=self.loop)
        app.add_signal_handler(response_start, callback)

        request = self.make_request('GET', '/')
        response = Response(body=b'')
        self.loop.run_until_complete(response.start(request))

        callback_mock.assert_called_once_with(request=request,
                                              response=response)

