###############################################################
#   (c) 2017 Makecents LLC
#   Created by Thomas Veale, Ryan Murphy
#   Purpose: Utility library for batching, posting, balance-
#               checking, and flask helpers, etc.
#   License: see LICENSE
###############################################################
# TODO: Imrpove dependency injection for transactions
# TODO: remove depricated code
# TODO: move sawtooth to its own file from utils -> sawtooth

import json
import cbor2
import base64
import requests
import socket
import random
import os
import string
from random import randint
from hashlib import sha512

from requests import ConnectionError
from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory

from flask import current_app

from sawtooth_sdk.protobuf.batch_pb2 import Batch
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionList

# get the app stack
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

import flask_sawtooth.exceptions as exceptions


class Sawtooth(object):
    """
    A Sawtooth utlity library as a Flask extension.
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Sets up reasonable defaults for Sawtooth lake and generates keys
        if they do not exist.
        """
        app.logger.info('Initializing Sawtooth Module')
        app.config.setdefault('SAWTOOTH_PRIV', None)
        app.config.setdefault('SAWTOOTH_PUB', None)
        app.config.setdefault('SAWTOOTH_HOST', 'localhost')
        app.config.setdefault('SAWTOOTH_PORT', '8008')
        app.config.setdefault('SAWTOOTH_FAMILY', 'intkey')
        app.config.setdefault('SAWTOOTH_SOCKET_URL',
                              'ws://{host}:{port}/subscriptions'
                              .format(host=app.config['SAWTOOTH_HOST'],
                                      port=app.config['SAWTOOTH_PORT']))
        app.config.setdefault('SAWTOOTH_BASE_URL', 'http://{host}:{port}'
                              .format(host=app.config['SAWTOOTH_HOST'],
                                      port=app.config['SAWTOOTH_PORT']))

        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    @staticmethod
    def gen_keys():
        """ Helper method that generates keys if none are provided
        for the encoder and batcher.

        :returns signer: An abstraction that handles private keys and signature gen.

        Getting public key:
        signer.get_public_key()   // optional .as_hex()

        Signing:
        signer.sign(msg)

        verification:
        singer._context.verify(signature:str, message:bytes, public_key:bytes)

        More info:
        https://sawtooth.hyperledger.org/docs/core/releases/1.0.1/_modules/sawtooth_signing/core.html

        """
        context = create_context('secp256k1')
        priv = current_app.config['SAWTOOTH_PRIV']
        private_key = priv if priv is not None else \
            context.new_random_private_key()
        signer = CryptoFactory(context).new_signer(private_key)
        return signer

    @staticmethod
    def subscribe(addr_prefixes='1cf126'):
        """ Opens a websocket connection to Sawtooth's state-delta service.
        :args addr_prefixes: A filter for certain transaction faminiles.

        :returns ws: A websocket file handle
        """
        try:
            current_app.logger.info('Subscribing to sawtooth state-delta.')
            r = requests.get(
                current_app.config['SAWTOOTH_SOCKET_URL'],
                stream=True)
            # Extract the underlying socket connection
            ws = socket.fromfd(
                r.raw.fileno(),
                socket.AF_INET,
                socket.SOCK_STREAM)
            # Send a subscribe message to state-delta
            ws.send(json.dumps({
                'action': 'subscribe',
                'address_prefixes': addr_prefixes
            }))
            return ws
        except ConnectionError as e:
            current_app.logger.fatal(e)

    @staticmethod
    def connect():
        """ Builds a reusable connection pool based on urllib3's connection pooling.

        :arg server: specifies the url of the server to build a conenction pool to.

        :returns s: A requests session pool

        """
        try:
            # current_app.logger.info('Building connection pool to sawtooth REST.')
            s = requests.Session()
            s.headers.update({'Content-Type': 'application/octet-stream'})
            # s.get(server)
            return s
        except ConnectionError as e:
            current_app.logger.fatal(e)

    @staticmethod
    def teardown(exception):
        """ Closes the websocket connection to Sawtooth's state-delta."""
        # current_app.logger.info('Gracefully tearing down resources...')
        ctx = stack.top
        if hasattr(ctx, 'sawtooth_state_delta'):
            # gracefully disconnect
            ctx.sawtooth_state_delta.send(
                json.dumps({'action': 'unsubscribe'}))
            # close the underlying TCP
            ctx.sawtooth_state_delta.close()
            current_app.logger.info('Closed open websockets.')
            # close the connection pool
        if hasattr(ctx, 'sawtooth_rest'):
            ctx.sawtooth_rest.close()
            current_app.logger.info('Closed all other connections.')

    @property
    def connection(self):
        """ Represents a reusable connection pool to sawtooth REST. """
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'sawtooth_rest'):
                # lazily load the connection pool
                ctx.sawtooth_rest = self.connect()
            return ctx.sawtooth_rest

    @property
    def signer(self):
        """ Represents a CryptoFactory used in signing batches and transactions"""
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'sawtooth_signer'):
                ctx.sawtooth_signer = self.gen_keys()
            return ctx.sawtooth_signer

    @staticmethod
    def gen_addr(mcname: str, family='intkey') -> bytes:
        """Takes in a state identifier (mobile or rng string) and returns
        the 70 byte sawtooth radix state address. See specifications in:

         https://intelledger.github.io/architecture/global_state.html

         Args:
             :arg state_store: a string representing the user's state address
             :parameter family: A string representing the family name of the txn.
         Returns:
             :returns addr: A hex-decimal string twice the length of the 70 byte address.
         """
        return sha512(family.encode('utf-8')).hexdigest()[0:6] \
            + sha512('{name}'.format(name=mcname)
                     .encode('utf-8')).hexdigest()[-64:]

    @staticmethod
    def decode_addr(state: bytes) -> dict:
        """Utility for decoding information stored at intkey like radix
        state addresses. First decodes base64 and then cbor.
        Args:
            :parameter state: A binary blob containing the encoded state
        Returns:
            :returns dict: containing the information stored at that address
        """
        return cbor2.loads(base64.b64decode(state))

    def initialize_state(self, mcname: str, promo=500, deps=None):
        """Initializes a state for a new user name. Called after
        phone verification.

        Args:
            :argument mcname: A unique string used to generate the user's stateaddress
            :parameter promo: A promotional amount of cents to give users
            :parameter deps: A transaction list of dependencies (header signatures)
        Returns:
            :returns bat: A serialized protobuf batchList
            :returns dep_id: A transaction header signature to be used as a dependency in
            future transactions.
        """
        current_app.logger.info('Initializing a state address.')
        tx, dep_id = self.txn_gen('set', mcname, promo, pub=None, deps=None)

        # tx is a transaction List so that bat_gen can iterate on it.
        # in a addition to the dependencies passed in
        bat = self.bat_gen(tx)
        return bat, dep_id

    def build_batch(self, payload: dict, deps=None):
        """Constructs a batch from two transactions represented as
        a dictionary with the sender and recipient. the first
        batch is from the party that submitted this request.
        The second is the recipient of the funds.
        TODO: make these codependent?
        Args
            :arg payload: A dict containing the request details
            payload = {
                'sender': bar
                'recipient': foo
                'value': 10
            }
            :arg deps: A list of Transaction.header_signature dependency.

        Returns:
            :returns BatchList: A serialized protobuf batch
        """
        try:
            # sender, TransactionList([s, ])
            s, _s_id = self.txn_gen('dec',
                                   payload['sender'],
                                   payload['value'],
                                   deps=deps)
            # recipient TransactionList([r, ])
            r, _r_id = self.txn_gen('inc',
                                   payload['receiver'],
                                   payload['value'],
                                   deps=deps)
        except KeyError:
            raise KeyError

        txn_list_bytes = TransactionList(
            transactions=[r.transactions[0], s.transactions[0]]
        )

        return self.bat_gen(txn_list_bytes)

    def credit(self, name: str, value: int) -> bytes:
        """Sends money to the specified address

        Args:
            :argument name: The nickname of the user or merchant
            :argument value: The value of the transaction (in cents)
        Returns:
            A serialized batch protobuf representing this transaction
        """
        raise NotImplementedError

    def debit(self, name: str, value: int) -> bytes:
        """Sends money to the specified address

        Args:
            :argument name: The nickname of the user or merchant
            :argument value: The value of the transaction (in cents)
        Returns:
            A serialized batch protobuf representing this transaction
        """
        raise NotImplementedError

    def txn_gen(self, verb: str, name: str, value: int,
                pub=None, deps=None) -> TransactionList:
        """ Generates a valid batch for testing submissions,
        optional arguments are for payment transactions.
        Args:
            :arg verb: the string 'inc', 'dec', or 'set'
            :arg name: the unique name used to identify a state address
            :arg value: the size of the transaction
            :arg pub: public key, defaults to self.signer if not provided
            :arg deps: A list of transaction header signature dependency this relies on.
        Returns:
            :var txn: a transaction list that includes the transaction porotobuf
            :var id: the transaction header signature used for dependnecies
        """

        # build payload
        payload = {
            'Verb': str(verb),
            'Name': str(name),
            'Value': int(value)
        }

        # calculate the state store
        state_store = self.gen_addr('{name}'.format(name=name))

        # encode the payload
        payload_bytes = cbor2.dumps(payload)

        # Create the header
        txn_header = TransactionHeader(
            batcher_public_key=pub if pub is not None else self.signer.get_public_key().as_hex(),
            dependencies=[] if deps is None else deps,
            family_name='intkey',
            family_version='1.0',
            inputs=[state_store],
            nonce=str(randint(0, 1000000000)),
            outputs=[state_store],
            payload_sha512=sha512(payload_bytes).hexdigest(),
            signer_public_key=pub if pub is not None else self.signer.get_public_key().as_hex())

        current_app.logger.info('txn header: {}'.format(txn_header))

        # encode the header to hex
        txn_header_bytes = txn_header.SerializeToString()

        # sign the header bytes, wif assumed.
        txn_signature_hex = self.signer.sign(txn_header_bytes)

        # build the transaction protobuf
        txn = Transaction(
            header=txn_header_bytes,
            header_signature=txn_signature_hex,
            payload=payload_bytes)

        return TransactionList(transactions=[txn]), txn.header_signature

    def bat_gen(self, txns: TransactionList) -> bytes:
        """ Generates a valid batch for testing submissions,
        optional arguments are for payment transactions.

        Args:
            :arg txns: the list of transactions to be included
        Returns:
            :arg batch_list: A serialized BatchList

        """
        Transactions = [txn.header_signature for txn in txns.transactions]

        batch_header = BatchHeader(
            signer_public_key=self.signer.get_public_key().as_hex(),
            transaction_ids=Transactions)

        # encode batch header
        batch_header_bytes = batch_header.SerializeToString()

        # sign batch header
        batch_signature_hex = self.signer.sign(batch_header_bytes)

        # build the batch
        batch = Batch(
            header=batch_header_bytes,
            header_signature=batch_signature_hex,
            transactions=[txn for txn in txns.transactions])

        batch_list = BatchList(batches=[batch])
        # return the batch and the header signatures of the transactions
        # included
        return batch_list.SerializeToString()

    def check_balance(self, name: str) -> int:
        """Retrieves the balance

        Args:
            :arg name: the user's nickname or id
        Returns:
            :returns balance: an integer representation of a user's makecents balance stored at
            state :meth:`makecents.sawtooth.Sawtooth.gen_addr`(name)
        """
        # calculate the state store
        address = self.gen_addr(name)
        try:
            # contains
            res = self.get_state(address)
            if res.ok:
                j = res.json()
                encoded_balance = j['data']
                head = j['head']
                balance = self.decode_addr(encoded_balance)
                current_app.logger.info(
                    'address {} \n head {} \n data {}'.format(
                        address, head, balance))
                return balance[name]
            else:
                current_app.logger.fatal(
                    'Failed to retrieve balance: {}'.format(
                        res.reason))
                raise exceptions.BalanceNotFound
        except (KeyError, AttributeError, exceptions.BalanceNotFound) as err:
            current_app.logger.error(err)
            raise (err)

    def get_state(self, address):
        """ Submits a get request to sawtooth REST to retrieve a state.

        Args:
            :arg address: a 70 byte state address
        Returns:
            a rolled json object or an HTTPError
        """
        url = current_app.config['SAWTOOTH_BASE_URL'] + '/state/' + address
        try:
            r = self.connection.get(url)
            current_app.logger.info(
                'Retrieved state: {}, encoding: {}'.format(
                    r.content, r.encoding))
            return r
        except requests.HTTPError as err:
            raise err

    def post_batch(self, batch_bytes):
        """ Submits a batch from users to sawtooth rest-api.
        Args:
            batch_bytes: is protobuf batch list
        Returns:
             a rolled json object or an HTTPError
        """
        url = current_app.config['SAWTOOTH_BASE_URL'] + '/batches'
        current_app.logger.info(
            'Posting barch to: {} and data {}'.format(
                url, batch_bytes))
        headers = {'Content-Type': 'application/octet-stream'}
        req = requests.Request('POST', url, headers=headers, data=batch_bytes)
        prepped = self.connection.prepare_request(req)
        try:
            r = self.connection.send(prepped)
            return r
        except (requests.HTTPError, requests.ConnectionError) as e:
            current_app.logger.error(e)
            raise e

    # TODO: refactor this into a batch getting utility
    def expand_sawtooth_link(self, batch_id, batch_id_array=None):
        """ Used to retrieve the current list of batches from sawtooth.
        Args:
            :arg batch_id: A url to be polled for information from sawtooth
            :arg batch_id_array: an array of batches to retrieve. for 15+ batches
        Returns:
            a rolled json object with the response.
        """
        if batch_id_array is None:
            url = current_app.config['SAWTOOTH_BASE_URL'] \
                + '/batch_statuses?id={}'.format(batch_id)
            req = requests.Request('GET', url)
            prepped = self.connection.prepare_request(req)
            try:
                r = self.connection.send(prepped)
                return r
            except requests.HTTPError as e:
                raise e
        else:
            # Returns an array of batch envelopes.
            # this should incease the effiecency of updating the database if we can
            # do just one request to blockchain instead of n.
            url = current_app.config['SAWTOOTH_BASE_URL'] + '/batch_statuses'
            req = requests.Request('POST', url, data=batch_id_array)
            prepped = self.connection.prepare_request(req)
            try:
                r = self.connection.send(prepped)
                return r
            except (requests.HTTPError, requests.ConnectionError) as e:
                current_app.logger.error(e)
                raise e

    @staticmethod
    def generate_word():
        return ''.join([random.choice(string.ascii_letters) for _ in range(0, 20)])

    @staticmethod
    def generate_word_list(count):
        if os.path.isfile('/usr/share/dict/words'):
            with open('/usr/share/dict/words', 'r') as fd:
                return [x.strip() for x in fd.readlines()[0:count]]
        else:
            return [Sawtooth.generate_word() for _ in range(0, count)]

    @staticmethod
    def generate_sawtooth_name():
        words = Sawtooth.generate_word_list(1000)
        return random.choice(words)
