###############################################################
#   (c) 2017 Makecents LLC
#   Created by Thomas Veale
#   Purpose: API tests for monolith
#   TODO: Mock Sawtooth
#   License: see LICENSE
###############################################################


import json
import time
import unittest
import mock
import cbor2
import time
import hmac
import random
import functools
import urllib

from base64 import b64decode, b64encode
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
from hashlib import sha512, sha384

from makecents import create_app, db, sawtooth as stl
from makecents.sawtooth.sawtooth import Sawtooth

TEST_SAWTOOTH_HOST = 'localhost'
TEST_SAWTOOTH_PORT = '8008'
TEST_STATE_NAME = 'foo'
TEST_SAWTOOTH_URL = 'http://localhost:8008'
TEST_SAWTOOTH_STATE_DELTA = 'ws:localhost:8080/subscriptions'
TEST_STATE = 'f7fbba1ff39bc5b188615273484021dfb16fd8284cf684ccf0fc795be3aa2fc1e6c181'

POST_BAD_BATCH_RESP = {
    "error": {
        "code": 35,
        "message": "The protobuf BatchList you submitted was malformed and could not be read.",
        "title": "Protobuf Not Decodable"
    }
}

POST_GOOD_BATCH_RESP = {
    "link": "http://localhost:8080/batch_status?id=c776aee796e3edd98bb5bdd308eba191ff9b306bed6da599d8dd673f7026fd091abc1211f9e616284d8af2a114c62bd64654bb0732021d08e31500ade6ad9757"
}

BAD_CHAIN_SETTINGS = {
    "error": {
        "code": 15,
        "message": "The validator has no genesis block, and is not yet ready to be queried. Try your request again later.",
        "title": "Validator Not Ready"
    }
}

GOOD_STATE_RESP = {
    'address': '',
    'head': '',
    'balance': b'oWNmb29jYmFy'

}

# TODO: fill this in
BAD_STATE_RESP = {
    'error': {
        'code': '',
        'message': '',
        'title': ''
    }

}


class TestSawtooth(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')

        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()  # just in case
        db.create_all()
        self.client = self.app.test_client()
        self.cache_data = {}
        pass

    def tearDown(self):
        db.drop_all()
        self.ctx.pop()

    def test_key_gen(self):
        """Tests that key length and type is correct. Could create and verify a signature."""

        # Test that it creates valid signatures
        sig = stl.signer.sign(b'foo')
        # self, signature, message, public_key
        b = stl.signer._context.verify(
            sig, b'foo', stl.signer.get_public_key())
        self.assertEquals(b, True)

    def test_subscribe(self):
        pass

    def test_connect(self):
        """Tests the connection pool to the server"""
        url = TEST_SAWTOOTH_URL + '/batches'
        res = stl.connection.get(url)
        self.assertEquals(res.ok, True)

    def test_websocket(self):
        pass

    def test_gen_address(self):
        """Ensures we are building the address correctly"""
        addr = stl.gen_addr('foo', 'intkey')
        self.assertEquals(
            '1cf1266e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7', addr)

    def test_create_user(self):
        """ Create a state, posts it, checks the initilization."""

        # build a batch
        bat, dep_id = stl.initialize_state('asdf')

        # post the batch
        res = stl.post_batch(bat)

        # check the state at the address
        addr = stl.gen_addr('asdf', 'intkey')
        state_res = stl.get_state(addr)
        self.assertEquals(state_res.ok, True)

        bal = stl.check_balance('asdf')
        self.assertEquals(bal, 500)

    def test_decode_address(self):
        # go one way, mimic how its stored on chain
        state_dict = {'asdf': 500}
        recovered_dict = stl.decode_addr(b'oWRhc2RmGQH0')
        self.assertEquals(state_dict, recovered_dict)

    def test_transaction_generation(self):
        pass

    def test_batch_generation(self):
        pass

    def test_build_batch(self):
        pass

    def test_credit(self):
        pass

    def test_debit(self):
        pass

    # @mock.patch('sawtooth.connect.get')
    # @mock.patch('sawtooth.connect.send')
    # def test_check_balance(self, mock_stl_conn_get, mock_stl_conn_send):
    #     """Mocks the balance checking."""
    #     mock_stl_conn_get.side_effect = mocked_stl_get
    #     mock_stl_conn_send.side_effect = mocked_stl_send
    #
    #     # generate a state adddress
    #     addr = stl.gen_addr('foo', family='bar')
    #     s = stl.connect(server=TEST_SAWTOOTH_URL)
    #     res = stl.check_balance('foo')
    #     self.assertEquals(res.status_code, 201)
    #     pass

    def test_post_batch(self):
        pass

    def test_expand_sawtooth_link(self):
        pass

# class MockResponse:
#     def __init__(self, json_data, status_code, headers):
#         self.json_data = json_data
#         self.status_code = status_code
#         self.headers = headers
#
#     def json(self):
#         """ Return the raw JSON blob"""
#         return self.json_data
#
# def mocked_sawtooth_subscription(*args, **kwargs):
#     """ Mocks the websocket interface for sawtooth state delta subscription
#     via websocket."""
#     if args[0] == '{}'.format(TEST_SAWTOOTH_STATE_DELTA):
#         pass
#
#     # return the
#     return MockResponse(None, 404, None)
#
# def mocked_sawtooth_get(*args, **kwargs):
#     """ Mocks a get to a URL of sawtooth REST api."""
#     if args[0] == 'http://localhost:8080/state/{}'.format(Sawtooth.gen_addr("asdf")):
#         return {"data": base64.b64encode(cbor2.dumps({"asdf": "500"}))}
#     elif args[0] == 'http://someothe`rurl.com/anothertest.json':
#         return MockResponse({"key2": "value2"}, 200)
#
#     return MockResponse(None, 404)


# def mocked_stl_get(*args, **kwargs):
#     class MockResponse:
#         """ Defines a response object"""
#         def __init__(self, data, status_code, headers):
#             self.data = data
#             self.status_code = status_code
#             self.headers = headers
#
#         def json(self):
#             """ Return the raw JSON blob"""
#             return self.data
#
#         def headers(self):
#             return self.headers
#
#         def status_code(self):
#             return self.status_code
#
#     if args[0] == 'http://{}:{}/batches/'.format(TEST_SAWTOOTH_HOST, TEST_SAWTOOTH_PORT):
#         return MockResponse(data=BAD_CHAIN_SETTINGS, status_code=500, headers=None)
#     if args[0] == 'http://{}:{}/state/{}'.format(TEST_SAWTOOTH_HOST, TEST_SAWTOOTH_PORT, TEST_STATE):
#         return MockResponse(data=GOOD_STATE_RESP, status_code=200, headers=None)
#     if args[0] == 'http://{}:{}/state/{}'.format(TEST_SAWTOOTH_HOST, TEST_SAWTOOTH_PORT, 'asdf'):
#         return MockResponse(data=BAD_STATE_RESP, status_code=200, headers=None)
#     return MockResponse(None, 404, {"content-type": "application/json"})
#
# def mocked_stl_send(*args, **kwargs):
#     """Mocks a post to a URL of sawtooth REST api"""
#     class MockResponse:
#         """ Defines a response object"""
#         def __init__(self, data, status_code, headers):
#             self.data = data
#             self.status_code = status_code
#             self.headers = headers
#
#         def json(self):
#             """ Return the raw JSON blob"""
#             return self.data
#
#         def headers(self):
#             return self.headers
#
#         def status_code(self):
#             return self.status_code
#
#     #
#     if args[0] == 'http://{}:{}/batches/'.format(TEST_SAWTOOTH_HOST, TEST_SAWTOOTH_PORT):
#         if isinstance(args[1], bytes):
#             #return MockResponse({'link': 'http://localhost:8080/batches?{}'.format(Sawtooth.gen_addr("foo")), 'data': [{'status': 'PENDING'}]}, 200)
#             return MockResponse(data=POST_GOOD_BATCH_RESP, status_code=201, headers=None)
#         else:
#             return MockResponse(data=POST_BAD_BATCH_RESP, status_code=400, headers=None)
#     # elif args[0] == 'http://someotherurl.com/anothertest.json':
#     #     return MockResponse({"key2": "value2"}, 200)
#     return MockResponse(None, 404, {"content-type": "application/json"})
#
#
#
#
# class Sawtooth(unittest.TestCase):
#
#     def setUp(self):
#         pass
#
#     def tearDown(self):
#         pass
#
#     def test_key_gen(self):
#         """Tests that key length and type is correct. Could create and verify a signature."""
#
#         #generate some keys
#         p, s = stl.gen_keys()
#         self.assertEquals(len(p), 384)
#         self.assertEquals(len(s), 256)
#         self.assertEquals(type(s), bytes)
#
#         # Test that it creates valid signatures
#         sig = signer.sign(b'foo', s, privkey_format=bytes)
#         b = signer.verify(b'foo', sig)
#         self.assertEquals(b, True)
#
#     def test_subscribe(self):
#         pass
#
#     def test_connect(self):
#         """Tests the connection pool to the server"""
#         s = stl.connect(server=TEST_SAWTOOTH_URL)
#         self.assertEquals('asdf', s)
#         pass
#
#     def test_teardown(self):
#         pass
#
#     def test_websocket(self):
#         pass
#
#     def test_encoder(self):
#
#         pass
#
#     def test_batcher(self):
#         pass
#
#     def test_gen_address(self):
#         """Ensures we are building the address correctly"""
#         addr = stl.gen_addr('foo', 'intkey')
#         self.assertEquals('1cf1266e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7', addr)
#
#     def test_decode_address(self):
#         # go one way, mimic how its stored on chain
#         state_dict = {'foo': 'bar'}
#         state = b64encode(cbor2.dumps(state_dict))
#
#         # recover what was stored there
#         state_str = cbor2.loads(b64decode(state))
#         recovered = json.loads(state)
#         self.assertEquals(state_dict, recovered)
#         pass
#
#     def test_transaction_generation(self):
#         pass
#
#     def test_batch_generation(self):
#         pass
#
#     def test_initilize_state_address(self):
#         pass
#
#     def test_build_batch(self):
#         pass
#
#     def test_credit(self):
#         pass
#
#     def test_debit(self):
#         pass
#
#
#     def test_get_state(self):
#         pass
#
#     @mock.patch('sawtooth.connect.get')
#     @mock.patch('sawtooth.connect.send')
#     def test_check_balance(self, mock_stl_conn_get, mock_stl_conn_send):
#         """Mocks the balance checking."""
#         mock_stl_conn_get.side_effect = mocked_stl_get
#         mock_stl_conn_send.side_effect = mocked_stl_send
#
#         # generate a state adddress
#         addr = stl.gen_addr('foo', family='bar')
#         s = stl.connect(server=TEST_SAWTOOTH_URL)
#         res = stl.check_balance('foo')
#         self.assertEquals(res.status_code, 201)
#         pass
#
#     def test_post_batch(self):
#         pass
#
#     def test_expand_sawtooth_link(self):
#         pass
