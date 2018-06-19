import unittest
import riemann
from .. import helpers
from ...tx import tx
from ... import utils


# On chain legacy tx p2sh -> p2pkh tx
# https://blockchain.info/rawtx/0739d0c7b7b7ff5f991e8e3f72a6f5eb56563880df982c4ab813cd71bc7a6a03?format=hex

class TestByteData(unittest.TestCase):

    def setUp(self):
        pass

    def test_iter(self):
        bd = tx.ByteData()
        bd._bytes.extend(b'\x00\x00')
        i = iter(bd)
        next(i)
        next(i)
        self.assertRaises(StopIteration, i.__next__)

    def test_iadd_error(self):
        bd = tx.ByteData()
        with self.assertRaises(TypeError) as context:
            bd += 'alphabet'

        self.assertIn('unsupported operand type(s) for +=: '
                      'ByteData and str', str(context.exception))

    def test_setattr_error(self):
        bd = tx.ByteData()
        bd._make_immutable()
        with self.assertRaises(TypeError) as context:
            bd.a = 'aaaaa'

        self.assertIn('cannot be written to.', str(context.exception))

    def test_repr(self):
        bd = tx.ByteData()
        bd._bytes.extend(b'\xff')

        self.assertEqual(bd.__repr__(), "ByteData: bytearray(b'\\xff')")

    def test_find(self):
        bd = tx.ByteData()
        bd._bytes.extend(b'\xff\xdd\x88')

        self.assertEqual(bd.find(b'\xff'), 0)
        self.assertEqual(bd.find(b'\xdd'), 1)
        self.assertEqual(bd.find(b'\x88'), 2)
        self.assertEqual(bd.find(b'\x00'), -1)

        bd2 = tx.ByteData()
        bd2._bytes.extend(b'\xaa')

        self.assertEqual(bd.find(bd2), -1)

    def test_hex(self):
        t = b'\xff\xdd\x88'
        bd = tx.ByteData()
        bd._bytes.extend(t)

        self.assertEqual(bd.hex(), t.hex())

    def test_ne_error(self):
        with self.assertRaises(TypeError) as context:
            bd = tx.ByteData()
            bd == 'hello world'

        self.assertIn(
            'Equality not supported for ByteData and ',
            str(context.exception))


class TestVarInt(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        riemann.select_network('bitcoin_main')

    def test_one_byte(self):
        res = tx.VarInt(0xfb)
        self.assertEqual(res, b'\xfb')
        self.assertIsInstance(res, tx.VarInt)

    def test_one_byte_boundary(self):
        res = tx.VarInt(0xff)
        self.assertEqual(res, b'\xfd' + b'\xff')
        self.assertIsInstance(res, tx.VarInt)

    def test_two_bytes(self):
        res = tx.VarInt(0xffff)
        self.assertEqual(res, b'\xfd' + (b'\xff' * 2))
        self.assertIsInstance(res, tx.VarInt)

    def test_four_bytes(self):
        res = tx.VarInt(0xffffffff)
        self.assertEqual(res, b'\xfe' + (b'\xff' * 4))
        self.assertIsInstance(res, tx.VarInt)

    def test_eight_bytes(self):
        res = tx.VarInt(0xffffffffffffffff)
        self.assertEqual(res, b'\xff' + (b'\xff' * 8))
        self.assertIsInstance(res, tx.VarInt)

        res = tx.VarInt(0x0123456789abcdef)
        self.assertEqual(res, b'\xff' + b'\xef\xcd\xab\x89\x67\x45\x23\x01')

        res = tx.VarInt(0x234000000000)  # 6 bytes to test padding
        self.assertEqual(res, b'\xff' + b'\x00\x00\x00\x00\x40\x23\x00\x00')

    def test_negative(self):
        with self.assertRaises(ValueError) as context:
            tx.VarInt(-5)

        self.assertIn('VarInt cannot be less than 0.',
                      str(context.exception))

    def test_too_high(self):
        with self.assertRaises(ValueError) as context:
            tx.VarInt(2 ** 64 + 1)

        self.assertIn('VarInt cannot be greater than (2 ** 64) - 1.',
                      str(context.exception))

    def test_copy(self):
        res = tx.VarInt(0xffffffffffffffff)
        copy = res.copy()
        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)

    def test_from_bytes(self):

        # This test is kinda a joke
        self.assertEqual(tx.VarInt.from_bytes(b'\xfd\x91#'), b'\xfd\x91#')
        self.assertEqual(tx.VarInt.from_bytes(b'\x00'), b'\x00')
        self.assertEqual(tx.VarInt.from_bytes(b'\xff' * 9), b'\xff' * 9)

        with self.assertRaises(ValueError) as context:
            tx.VarInt.from_bytes(b'\xfe')
        self.assertIn(
            'Malformed VarInt. Got: fe',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.VarInt.from_bytes(b'\xfe\x00\x00\x00')
        self.assertIn(
            'Malformed VarInt. Got: fe',
            str(context.exception))

    def test_zcash_compact_enforcement(self):
        riemann.select_network('zcash_main')

        with self.assertRaises(ValueError) as context:
            tx.VarInt.from_bytes(b'\xfd\x00\x00')

        self.assertIn(
            'VarInt must be compact. Got:',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.VarInt.from_bytes(b'\xfe\x00\x00\x00\x00')

        self.assertIn(
            'VarInt must be compact. Got:',
            str(context.exception))


class TestOutpoint(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_outpoint(self):
        outpoint_index = helpers.P2PKH1['ser']['ins'][0]['index']
        outpoint_tx_id = helpers.P2PKH1['ser']['ins'][0]['hash']

        outpoint = tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertEqual(outpoint.tx_id, outpoint_tx_id)
        self.assertEqual(outpoint.index, outpoint_index)
        self.assertEqual(outpoint, outpoint_tx_id + outpoint_index)

    def test_create_outpoint_short_tx_id(self):
        outpoint_index = helpers.P2PKH1['ser']['ins'][0]['index']
        outpoint_tx_id = bytearray(b'\xff')

        with self.assertRaises(ValueError) as context:
            tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertIn('Expected byte-like object with length 32. ',
                      str(context.exception))

    def test_create_outpoint_str_tx_id(self):
        outpoint_index = helpers.P2PKH1['ser']['ins'][0]['index']
        outpoint_tx_id = 'Hello world'

        with self.assertRaises(ValueError) as context:
            tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_create_outpoint_long_index(self):
        outpoint_index = utils.i2le_padded(0, 5)
        outpoint_tx_id = helpers.P2PKH1['ser']['ins'][0]['hash']

        with self.assertRaises(ValueError) as context:
            tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertIn('Expected byte-like object with length 4. ',
                      str(context.exception))

    def test_create_outpoint_no_index(self):
        outpoint_index = None
        outpoint_tx_id = helpers.P2PKH1['ser']['ins'][0]['hash']

        with self.assertRaises(ValueError) as context:
            tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_copy(self):
        outpoint_index = helpers.P2PKH1['ser']['ins'][0]['index']
        outpoint_tx_id = helpers.P2PKH1['ser']['ins'][0]['hash']

        res = tx.Outpoint(outpoint_tx_id, outpoint_index)
        copy = res.copy()
        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)

    def test_from_bytes(self):
        outpoint = tx.Outpoint.from_bytes(
            helpers.P2PKH1['ser']['ins'][0]['outpoint'])
        self.assertEqual(outpoint, helpers.P2PKH1['ser']['ins'][0]['outpoint'])
        self.assertEqual(
            outpoint.tx_id,
            helpers.P2PKH1['ser']['ins'][0]['hash'])
        self.assertEqual(
            outpoint.index,
            helpers.P2PKH1['ser']['ins'][0]['index'])


class TestTxIn(unittest.TestCase):

    def setUp(self):
        outpoint_index = helpers.P2PKH1['ser']['ins'][0]['index']
        outpoint_tx_id = helpers.P2PKH1['ser']['ins'][0]['hash']

        self.stack_script = helpers.P2PKH1['ser']['ins'][0]['stack_script']
        self.redeem_script = helpers.P2PKH1['ser']['ins'][0]['redeem_script']
        self.sequence = helpers.P2PKH1['ser']['ins'][0]['sequence']
        self.outpoint = tx.Outpoint(outpoint_tx_id, outpoint_index)

    def test_create_input(self):
        tx_in = tx.TxIn(self.outpoint, self.stack_script,
                        self.redeem_script, self.sequence)

        self.assertEqual(tx_in.outpoint, self.outpoint)
        self.assertEqual(tx_in.stack_script, self.stack_script)
        self.assertEqual(tx_in.redeem_script, self.redeem_script)
        self.assertEqual(tx_in.sequence, self.sequence)
        self.assertEqual(tx_in, helpers.P2PKH1['ser']['tx']['in'])

    def test_copy(self):
        tx_in = tx.TxIn(self.outpoint, self.stack_script,
                        self.redeem_script, self.sequence)

        tx_in_copy = tx_in.copy()

        self.assertEqual(tx_in, tx_in_copy)  # They should be equal
        self.assertIsNot(tx_in, tx_in_copy)  # But not the same object

    def test_long_script_sig(self):
        with self.assertRaises(ValueError) as context:
            tx.TxIn(self.outpoint, b'\x00' * 1000,
                    b'\x00' * 1000, self.sequence)

        self.assertIn(
            'Input script_sig is too long. Expected <= 1650 bytes. '
            'Got 2000 bytes.',
            str(context.exception))

    def test_from_bytes_pkh(self):
        tx_in = tx.TxIn.from_bytes(helpers.P2PKH1['ser']['tx']['in'])
        self.assertEqual(tx_in, helpers.P2PKH1['ser']['tx']['in'])
        self.assertEqual(
            tx_in.outpoint,
            helpers.P2PKH1['ser']['ins'][0]['outpoint'])
        self.assertEqual(
            tx_in.sequence,
            helpers.P2PKH1['ser']['ins'][0]['sequence'])
        self.assertEqual(
            tx_in.stack_script,
            helpers.P2PKH1['ser']['ins'][0]['stack_script'])
        self.assertEqual(
            tx_in.redeem_script,
            helpers.P2PKH1['ser']['ins'][0]['redeem_script'])

    def test_from_bytes_sh(self):
        tx_in = tx.TxIn.from_bytes(helpers.P2SH['ser']['ins'][0]['input'])
        self.assertEqual(tx_in, helpers.P2SH['ser']['ins'][0]['input'])
        self.assertEqual(
            tx_in.outpoint,
            helpers.P2SH['ser']['ins'][0]['outpoint'])
        self.assertEqual(
            tx_in.sequence,
            helpers.P2SH['ser']['ins'][0]['sequence'])
        self.assertEqual(
            tx_in.stack_script,
            helpers.P2SH['ser']['ins'][0]['stack_script'])
        self.assertEqual(
            tx_in.redeem_script,
            helpers.P2SH['ser']['ins'][0]['redeem_script'])

    def test_from_bytes_wsh(self):
        tx_in = tx.TxIn.from_bytes(helpers.P2WSH['ser']['ins'][0]['input'])
        self.assertEqual(tx_in, helpers.P2WSH['ser']['ins'][0]['input'])
        self.assertEqual(
            tx_in.outpoint,
            helpers.P2WSH['ser']['ins'][0]['outpoint'])
        self.assertEqual(
            tx_in.sequence,
            utils.i2be(helpers.P2WSH['human']['ins'][0]['sequence']))
        self.assertEqual(tx_in.stack_script, b'')
        self.assertEqual(tx_in.redeem_script, b'')


class TestTxOut(unittest.TestCase):

    def setUp(self):
        self.value = helpers.P2PKH1['ser']['outs'][0]['value']
        self.output_script = helpers.P2PKH1['ser']['outs'][0]['pk_script']

    def test_create_output(self):
        tx_out = tx.TxOut(self.value, self.output_script)
        self.assertEqual(tx_out, helpers.P2PKH1['ser']['outs'][0]['out'])

    def test_copy(self):
        tx_out = tx.TxOut(self.value, self.output_script)
        tx_out_copy = tx_out.copy()

        self.assertEqual(tx_out, tx_out_copy)  # They should be equal
        self.assertIsNot(tx_out, tx_out_copy)  # But not the same object

    def test_dust_limit_error(self):
        with self.assertRaises(ValueError) as context:
            tx.TxOut(utils.i2le_padded(5, 8), self.output_script)

        self.assertIn(
            'Transaction value below dust limit. '
            'Expected more than 546 sat. Got: 5 sat.',
            str(context.exception))

    def test_from_bytes(self):
        output = helpers.P2PKH1['ser']['outs'][0]['value'] + \
            b'\x19' + helpers.P2PKH1['ser']['outs'][0]['pk_script']
        tx_out = tx.TxOut.from_bytes(output)
        self.assertEqual(
            tx_out.value,
            helpers.P2PKH1['ser']['outs'][0]['value'])
        self.assertEqual(
            tx_out.output_script,
            helpers.P2PKH1['ser']['outs'][0]['pk_script'])

    def test_from_bytes_long(self):
        with self.assertRaises(NotImplementedError) as context:
            tx.TxOut.from_bytes(b'\xff' * 10)
        self.assertIn(
            'No support for abnormally long pk_scripts.',
            str(context.exception))


class TestWitnessStackItem(unittest.TestCase):

    def setUp(self):
        self.stack_item_bytes = \
            helpers.P2WSH['ser']['witnesses'][0]['wit_stack_items'][1]

    def test_create_stack_item(self):
        w = tx.WitnessStackItem(self.stack_item_bytes)
        self.assertEqual(w.item, self.stack_item_bytes)
        self.assertEqual(w.item_len, len(self.stack_item_bytes))
        self.assertEqual(
            w,
            bytes([len(self.stack_item_bytes)]) + self.stack_item_bytes)

    def test_from_bytes(self):
        w = tx.WitnessStackItem.from_bytes(
            bytes([len(self.stack_item_bytes)]) + self.stack_item_bytes)
        self.assertEqual(w.item, self.stack_item_bytes)
        self.assertEqual(w.item_len, len(self.stack_item_bytes))
        self.assertEqual(
            w,
            bytes([len(self.stack_item_bytes)]) + self.stack_item_bytes)

    def test_item_too_long(self):
        with self.assertRaises(ValueError) as context:
            tx.WitnessStackItem(b'\xff' * 521)
        self.assertIn(
            'Item is too large. Expected <=520 bytes. ',
            str(context.exception))

    def test_null_item_from_bytes(self):
        w = tx.WitnessStackItem.from_bytes(b'\x00')
        self.assertEqual(w, b'\x00')


class TestInputWitness(unittest.TestCase):

    def setUp(self):
        self.stack = [tx.WitnessStackItem(b)
                      for b in
                      helpers.P2WSH['ser']['witnesses'][0]['wit_stack_items']]

    def test_create_witness(self):
        iw = tx.InputWitness(self.stack)
        self.assertEqual(len(iw.stack), len(self.stack))
        for item, expected in zip(iw.stack, self.stack):
            self.assertEqual(item, expected)

        bad_stack = [None, 1]
        with self.assertRaises(ValueError) as context:
            tx.InputWitness(bad_stack)

        self.assertIn('Invalid witness stack item. Expected bytes. Got None',
                      str(context.exception))

    def test_from_bytes(self):
        iw = tx.InputWitness.from_bytes(helpers.P2WSH['ser']['tx']['witness'])
        self.assertEqual(len(iw.stack), len(self.stack))
        for item, expected in zip([s.item for s in iw.stack],
                                  [s.item for s in self.stack]):
            self.assertEqual(item, expected)


class TestTx(unittest.TestCase):

    def setUp(self):
        self.outpoint_index = helpers.P2PKH1['ser']['ins'][0]['index']
        self.outpoint_tx_id = helpers.P2PKH1['ser']['ins'][0]['hash']

        self.stack_script = helpers.P2PKH1['ser']['ins'][0]['stack_script']
        self.redeem_script = helpers.P2PKH1['ser']['ins'][0]['redeem_script']
        self.sequence = helpers.P2PKH1['ser']['ins'][0]['sequence']
        self.outpoint = tx.Outpoint(self.outpoint_tx_id, self.outpoint_index)

        self.tx_in = tx.TxIn(self.outpoint, self.stack_script,
                             self.redeem_script, self.sequence)

        self.value_0 = helpers.P2PKH1['ser']['outs'][0]['value']
        self.output_script_0 = \
            helpers.P2PKH1['ser']['outs'][0]['pk_script']
        self.value_1 = helpers.P2PKH1['ser']['outs'][1]['value']
        self.output_script_1 = \
            helpers.P2PKH1['ser']['outs'][1]['pk_script']

        self.tx_out_0 = tx.TxOut(self.value_0, self.output_script_0)
        self.tx_out_1 = tx.TxOut(self.value_1, self.output_script_1)

        self.version = helpers.P2PKH1['ser']['version']
        self.none_flag = None
        self.tx_ins = [self.tx_in]
        self.tx_outs = [self.tx_out_0, self.tx_out_1]
        self.none_witnesses = None
        self.lock_time = helpers.P2PKH1['ser']['locktime']

        self.segwit_flag = b'\x00\x01'
        self.stack = [tx.WitnessStackItem(b)
                      for b in
                      helpers.P2WSH['ser']['witnesses'][0]['wit_stack_items']]
        self.tx_witnesses = [tx.InputWitness(self.stack)]

    def tearDown(self):
        riemann.select_network('bitcoin_main')

    # Convenience monotest
    # Sorta broken.
    def test_everything_witness(self):
        version = bytearray([0] * 4)
        flag = b'\x00\x01'
        outpoint_index = utils.i2le_padded(0, 4)
        outpoint_tx_id = bytearray(bytearray.fromhex(
            '10399b3f20cbdd4b5ac3f823afdba28b'
            '9f70e21437a59b312a1b62c42c5cd101'))[::-1]
        outpoint = tx.Outpoint(outpoint_tx_id, outpoint_index)

        sequence = utils.i2le_padded(0, 4)

        script = bytearray(bytearray.fromhex('473044022000e02ea97289a35181a9bfabd324f12439410db11c4e94978cdade6a665bf1840220458b87c34d8bb5e4d70d01041c7c2d714ea8bfaca2c2d2b1f9e5749c3ee17e3d012102ed0851f0b4c4458f80e0310e57d20e12a84642b8e097fe82be229edbd7dbd53920f6665740b1f950eb58d646b1fae9be28cef842da5e51dc78459ad2b092e7fd6e514c5163a914bb408296de2420403aa79eb61426bb588a08691f8876a91431b31321831520e346b069feebe6e9cf3dd7239c670400925e5ab17576a9140d22433293fe9652ea00d21c5061697aef5ddb296888ac'))  # noqa: E501

        tx_in = tx.TxIn(outpoint, script, bytearray(), sequence)
        tx_ins = [tx_in]

        tx_outs = [
            tx.TxOut(
                value=bytearray(utils.i2le_padded(2000, 8)),
                output_script=bytearray(bytearray.fromhex('76a914f2539f42058da784a9d54615ad074436cf3eb85188ac')))  # noqa: E501
        ]
        none_witnesses = [
            tx.InputWitness(
                [
                    tx.WitnessStackItem(bytearray([0x88] * 18)),
                    tx.WitnessStackItem(bytearray([0x99] * 18))
                ]
            )
        ]
        lock_time = bytearray([0xff] * 4)

        tx.Tx(version, flag, tx_ins, tx_outs, none_witnesses, lock_time)

        # TODO: needs assertions

    # Convenience monotest
    def test_everything(self):
        version = utils.i2le_padded(1, 4)
        outpoint_index = utils.i2le_padded(0, 4)
        outpoint_tx_id = bytearray(bytearray.fromhex(
            '10399b3f20cbdd4b5ac3f823afdba28b'
            '9f70e21437a59b312a1b62c42c5cd101'))[::-1]
        outpoint = tx.Outpoint(outpoint_tx_id, outpoint_index)

        sequence = utils.i2le_padded(0, 4)

        script = bytearray(bytearray.fromhex('473044022000e02ea97289a35181a9bfabd324f12439410db11c4e94978cdade6a665bf1840220458b87c34d8bb5e4d70d01041c7c2d714ea8bfaca2c2d2b1f9e5749c3ee17e3d012102ed0851f0b4c4458f80e0310e57d20e12a84642b8e097fe82be229edbd7dbd53920f6665740b1f950eb58d646b1fae9be28cef842da5e51dc78459ad2b092e7fd6e514c5163a914bb408296de2420403aa79eb61426bb588a08691f8876a91431b31321831520e346b069feebe6e9cf3dd7239c670400925e5ab17576a9140d22433293fe9652ea00d21c5061697aef5ddb296888ac'))  # noqa: E501

        tx_in = tx.TxIn(outpoint, script, bytearray(), sequence)
        tx_ins = [tx_in]

        tx_outs = [
            tx.TxOut(
                value=bytearray(utils.i2le_padded(2000, 8)),
                output_script=bytearray(bytearray.fromhex('76a914f2539f42058da784a9d54615ad074436cf3eb85188ac')))  # noqa: E501
        ]

        lock_time = utils.i2le_padded(0, 4)

        res = tx.Tx(version, None, tx_ins, tx_outs, None, lock_time)

        self.assertEqual(res, helpers.RAW_P2SH_TO_P2PKH)

    # TODO: Break up this monstrosity (further)
    def test_tx_witness(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        self.assertEqual(t, helpers.P2PKH1['ser']['tx']['signed'])

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, b'\x00\x00', self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertIn(
            'Invald segwit flag. Expected None or ',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, self.segwit_flag, self.tx_ins, self.tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Got segwit flag but no witnesses.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, b'\x00\x01', self.tx_ins, self.tx_outs,
                  [], self.lock_time)
        self.assertIn(
            'Got segwit flag but no witnesses.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, None, self.tx_ins, self.tx_outs,
                  self.tx_witnesses, self.lock_time)
        self.assertIn(
            'Got witnesses but no segwit flag.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            stack = self.stack + [self.stack[0]]
            witness = tx.InputWitness(stack)
            tx.Tx(self.version, self.segwit_flag, self.tx_ins, self.tx_outs,
                  witness, self.lock_time)
        self.assertIn(
            'Witness and TxIn lists must be same length. ',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, self.segwit_flag, self.tx_ins, self.tx_outs,
                  [1 for _ in self.tx_witnesses], self.lock_time)
        self.assertIn(
            'Invalid InputWitness. Expected instance of InputWitness.',
            str(context.exception))

    def test_tx_inandout(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        self.assertEqual(t, helpers.P2PKH1['ser']['tx']['signed'])

        with self.assertRaises(ValueError) as context:
            tx_ins = [self.tx_ins[0] for _ in range(257)]
            tx.Tx(self.version, self.none_flag, tx_ins, self.tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Too many inputs or outputs. Stop that.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_outs = [self.tx_outs[0] for _ in range(257)]
            tx.Tx(self.version, self.none_flag, self.tx_ins, tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Too many inputs or outputs. Stop that.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_ins = []
            tx.Tx(self.version, self.none_flag, tx_ins, self.tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Too few inputs or outputs. Stop that.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_ins = [1]
            tx.Tx(self.version, self.none_flag, tx_ins, self.tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Invalid TxIn. Expected instance of TxIn. Got int',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_outs = [1]
            tx.Tx(self.version, self.none_flag, self.tx_ins, tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Invalid TxOut. Expected instance of TxOut. Got int',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_in = self.tx_ins[0].copy(stack_script=b'\x00' * 1616,
                                        redeem_script=None)
            tx_ins = [tx_in for _ in range(255)]
            tx_outs = [self.tx_outs[0] for _ in range(255)]
            tx.Tx(self.version, self.none_flag, tx_ins, tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Tx is too large. Expect less than 100kB. Got: ',
            str(context.exception))

    def test_tx_inout_mutation(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        with self.assertRaises(TypeError, msg='That\'s immutable, honey'):
            t.tx_ins = t.tx_ins + (1,)

        with self.assertRaises(TypeError, msg='That\'s immutable, honey'):
            t.tx_outs = t.tx_outs + (1,)

    def test_tx_id(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        self.assertEqual(t.tx_id, helpers.P2PKH1['ser']['tx']['hash'])
        self.assertEqual(t.tx_id_le, helpers.P2PKH1['ser']['tx']['hash_le'])

    def test_from_bytes_pkh(self):
        t = tx.Tx.from_bytes(helpers.P2PKH1['ser']['tx']['signed'])
        self.assertEqual(t.version, helpers.P2PKH1['ser']['version'])
        self.assertEqual(t.tx_ins[0], helpers.P2PKH1['ser']['tx']['in'])
        self.assertEqual(t.tx_outs[0], helpers.P2PKH1['ser']['outs'][0]['out'])
        self.assertEqual(t.tx_outs[1], helpers.P2PKH1['ser']['outs'][1]['out'])
        self.assertEqual(t.lock_time, helpers.P2PKH1['ser']['locktime'])
        self.assertEqual(t, helpers.P2PKH1['ser']['tx']['signed'])

    def test_from_bytes_sh(self):
        t = tx.Tx.from_bytes(helpers.P2SH['ser']['tx']['signed'])
        self.assertEqual(t.version, helpers.P2SH['ser']['version'])
        self.assertEqual(
            t.tx_ins[0],
            helpers.P2SH['ser']['ins'][0]['input'])
        self.assertEqual(
            t.tx_outs[0],
            helpers.P2SH['ser']['outs'][0]['output'])
        self.assertEqual(
            t.tx_outs[1],
            helpers.P2SH['ser']['outs'][1]['output'])
        self.assertEqual(t.lock_time, helpers.P2SH['ser']['locktime'])
        self.assertEqual(t, helpers.P2SH['ser']['tx']['signed'])

    def test_from_bytes_wsh(self):
        t = tx.Tx.from_bytes(helpers.P2WSH['ser']['tx']['signed'])
        self.assertEqual(t.version, helpers.P2WSH['ser']['version'])
        self.assertEqual(t.tx_ins[0], helpers.P2WSH['ser']['ins'][0]['input'])
        self.assertEqual(
            t.tx_outs[0],
            helpers.P2WSH['ser']['outs'][0]['output'])
        self.assertEqual(
            t.tx_outs[1],
            helpers.P2WSH['ser']['outs'][1]['output'])
        self.assertEqual(
            t.tx_outs[2],
            helpers.P2WSH['ser']['outs'][2]['output'])
        self.assertEqual(
            t.tx_outs[3],
            helpers.P2WSH['ser']['outs'][3]['output'])
        self.assertEqual(
            t.tx_witnesses[0],
            helpers.P2WSH['ser']['tx']['witness'])
        self.assertEqual(t.lock_time, helpers.P2SH['ser']['locktime'])
        self.assertEqual(t, helpers.P2WSH['ser']['tx']['signed'])

    def test_calculate_fee(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        self.assertEqual(t.calculate_fee([10 ** 8]), 57534406)

    def test_sighash_none(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        with self.assertRaises(NotImplementedError) as context:
            t.sighash_none()

        self.assertIn('SIGHASH_NONE is a bad idea.', str(context.exception))

    def test_copy(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        t_copy = t.copy()

        self.assertEqual(t, t_copy)
        self.assertIsNot(t, t_copy)

    def test_is_witness(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        self.assertFalse(t.is_witness())

        t = tx.Tx.from_bytes(helpers.P2WSH['ser']['tx']['signed'])

        self.assertTrue(t.is_witness())

    def test_sighash_all(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        self.assertEqual(
            t.sighash_all(0, helpers.P2PKH1['ser']['ins'][0]['pk_script']),
            helpers.P2PKH1['ser']['sighash']['all'])

    def test_sighash_all_anyone_can_pay(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertEqual(
            t.sighash_all(
                0,
                helpers.P2PKH1['ser']['ins'][0]['pk_script'],
                anyone_can_pay=True),
            helpers.P2PKH1['ser']['sighash']['all_anyonecanpay'])

    def test_sighash_single(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertEqual(
            t.sighash_single(
                0,
                helpers.P2PKH1['ser']['ins'][0]['pk_script']),
            helpers.P2PKH1['ser']['sighash']['single'])

    def test_sighash_single_anyone_can_pay(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertEqual(
            t.sighash_single(
                0,
                helpers.P2PKH1['ser']['ins'][0]['pk_script'],
                anyone_can_pay=True),
            helpers.P2PKH1['ser']['sighash']['single_anyonecanpay'])

    def test_sighash_single_bug(self):
        with self.assertRaises(NotImplementedError) as context:
            t = tx.Tx(self.version, self.none_flag, self.tx_ins * 3,
                      self.tx_outs, self.none_witnesses, self.lock_time)
            t.sighash_single(2, helpers.P2PKH1['ser']['ins'][0]['pk_script'])

        self.assertIn(
            'I refuse to implement the SIGHASH_SINGLE bug.',
            str(context.exception))

    def test_sighash_forkid_single(self):
        riemann.select_network('bitcoin_cash_main')
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        sighash = t.sighash_single(
            index=0,
            script=helpers.P2PKH1['ser']['ins'][0]['pk_script'],
            prevout_value=helpers.P2PKH1['ser']['ins'][0]['value'])

        self.assertEqual(
            sighash,
            helpers.SIGHASH_FORKID['single'])

    def test_sighash_forkid_single_anyone_can_pay(self):
        riemann.select_network('bitcoin_cash_main')
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        sighash = t.sighash_single(
            index=0,
            script=helpers.P2PKH1['ser']['ins'][0]['pk_script'],
            prevout_value=helpers.P2PKH1['ser']['ins'][0]['value'],
            anyone_can_pay=True)

        self.assertEqual(
            sighash,
            helpers.SIGHASH_FORKID['single_anyone_can_pay'])

    def test_sighash_forkid_all(self):
        riemann.select_network('bitcoin_cash_main')
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        sighash = t.sighash_all(
            index=0,
            script=helpers.P2PKH1['ser']['ins'][0]['pk_script'],
            prevout_value=helpers.P2PKH1['ser']['ins'][0]['value'])

        self.assertEqual(
            sighash,
            helpers.SIGHASH_FORKID['all'])

    def test_sighash_forkid_all_anyone_can_pay(self):
        riemann.select_network('bitcoin_cash_main')
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        sighash = t.sighash_all(
            index=0,
            script=helpers.P2PKH1['ser']['ins'][0]['pk_script'],
            prevout_value=helpers.P2PKH1['ser']['ins'][0]['value'],
            anyone_can_pay=True)

        self.assertEqual(
            sighash,
            helpers.SIGHASH_FORKID['all_anyone_can_pay'])

    def test_hash_outputs(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins,
                  self.tx_outs, self.none_witnesses, self.lock_time)
        output = t._hash_outputs(index=0, sighash_type=tx.SIGHASH_SINGLE)
        expected = utils.hash256(self.tx_outs[0].to_bytes())
        self.assertEqual(output, expected)

        with self.assertRaises(NotImplementedError) as context:
            t = tx.Tx(self.version, self.none_flag, self.tx_ins,
                      self.tx_outs, self.none_witnesses, self.lock_time)
            t._hash_outputs(index=3, sighash_type=tx.SIGHASH_SINGLE)

        self.assertIn(
            'I refuse to implement the SIGHASH_SINGLE bug.',
            str(context.exception))

    def test_script_code(self):
        self.stack_script = helpers.P2SH['ser']['ins'][0]['stack_script']
        self.redeem_script = helpers.P2SH['ser']['ins'][0]['redeem_script']
        self.sequence = helpers.P2SH['ser']['ins'][0]['sequence']
        self.outpoint = helpers.P2SH['ser']['ins'][0]['outpoint']

        self.tx_in = tx.TxIn(self.outpoint, self.stack_script,
                             self.redeem_script, self.sequence)
        self.tx_ins = [self.tx_in]

        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        bob = t.script_code(index=0)
        self.assertEqual(bob, self.redeem_script)

    def test_adjusted_script_code(self):
        self.stack_script = helpers.P2SH['ser']['ins'][0]['stack_script']
        self.redeem_script = helpers.P2SH['ser']['ins'][0]['redeem_script']
        self.sequence = helpers.P2SH['ser']['ins'][0]['sequence']
        self.outpoint = helpers.P2SH['ser']['ins'][0]['outpoint']

        self.tx_in = tx.TxIn(self.outpoint, self.stack_script,
                             self.redeem_script, self.sequence)
        self.tx_ins = [self.tx_in]

        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        add_script = helpers.P2SH['ser']['ins'][0]['redeem_script']
        adj_script_code = t._adjusted_script_code(index=0, script=add_script)
        expected_code = tx.ByteData()
        expected_code += tx.VarInt(len(self.redeem_script))
        expected_code += self.redeem_script

        self.assertEqual(adj_script_code, expected_code)


class DecredTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        riemann.select_network('decred_main')

    def tearDown(self):
        riemann.select_network('bitcoin_main')


class TestDecredByteData(DecredTestCase):

    def test_init_error(self):
        riemann.select_network('bitcoin_main')
        with self.assertRaises(ValueError) as context:
            tx.DecredByteData()

        self.assertIn('Decred classes not supported by network bitcoin_main. '
                      'How did you get here?',
                      str(context.exception))


class TestDecredOutpoint(DecredTestCase):

    def test_create_outpoint(self):
        outpoint_index = helpers.DCR['ser']['ins'][0]['index']
        outpoint_tx_id = helpers.DCR['ser']['ins'][0]['hash']
        outpoint_tree = helpers.DCR['ser']['ins'][0]['tree']

        outpoint = tx.DecredOutpoint(
            outpoint_tx_id, outpoint_index, outpoint_tree)

        self.assertEqual(outpoint, helpers.DCR['ser']['ins'][0]['outpoint'])

    def test_copy(self):
        outpoint_index = helpers.DCR['ser']['ins'][0]['index']
        outpoint_tx_id = helpers.DCR['ser']['ins'][0]['hash']
        outpoint_tree = helpers.DCR['ser']['ins'][0]['tree']

        res = tx.DecredOutpoint(
            outpoint_tx_id, outpoint_index, outpoint_tree)

        copy = res.copy()
        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)

    def test_create_outpoint_short_tx_id(self):
        outpoint_index = helpers.DCR['ser']['ins'][0]['index']
        outpoint_tx_id = bytearray(b'\xff')
        outpoint_tree = helpers.DCR['ser']['ins'][0]['tree']

        with self.assertRaises(ValueError) as context:
            tx.DecredOutpoint(
                outpoint_tx_id, outpoint_index, outpoint_tree)

        self.assertIn('Expected byte-like object with length 32. ',
                      str(context.exception))

    def test_create_outpoint_string_tx_id(self):
        outpoint_index = helpers.DCR['ser']['ins'][0]['index']
        outpoint_tx_id = 'Hello World'
        outpoint_tree = helpers.DCR['ser']['ins'][0]['tree']

        with self.assertRaises(ValueError) as context:
            tx.DecredOutpoint(
                outpoint_tx_id, outpoint_index, outpoint_tree)

        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_create_outpoint_long_tx_id(self):
        outpoint_index = helpers.DCR['ser']['ins'][0]['index']
        outpoint_tx_id = b'00' * 37
        outpoint_tree = helpers.DCR['ser']['ins'][0]['tree']

        with self.assertRaises(ValueError) as context:
            tx.DecredOutpoint(
                outpoint_tx_id, outpoint_index, outpoint_tree)

        self.assertIn('Expected byte-like object with length 32. ',
                      str(context.exception))

    def test_create_outpoint_short_index(self):
        outpoint_index = b'\x00'
        outpoint_tx_id = helpers.DCR['ser']['ins'][0]['hash']
        outpoint_tree = helpers.DCR['ser']['ins'][0]['tree']

        with self.assertRaises(ValueError) as context:
            tx.DecredOutpoint(
                outpoint_tx_id, outpoint_index, outpoint_tree)

        self.assertIn('Expected byte-like object with length 4. ',
                      str(context.exception))

    def test_create_outpoint_string_tree(self):
        outpoint_index = helpers.DCR['ser']['ins'][0]['index']
        outpoint_tx_id = helpers.DCR['ser']['ins'][0]['hash']
        outpoint_tree = 'Hello World'

        with self.assertRaises(ValueError) as context:
            tx.DecredOutpoint(
                outpoint_tx_id, outpoint_index, outpoint_tree)

        self.assertIn('Expected byte-like object. ',
                      str(context.exception))


class TestDecredTxIn(DecredTestCase):

    def setUp(self):
        super().setUp()
        outpoint_index = helpers.DCR['ser']['ins'][0]['index']
        outpoint_tx_id = helpers.DCR['ser']['ins'][0]['hash']
        outpoint_tree = helpers.DCR['ser']['ins'][0]['tree']

        self.sequence = helpers.DCR['ser']['ins'][0]['sequence']

        self.outpoint = tx.DecredOutpoint(
            outpoint_tx_id, outpoint_index, outpoint_tree)

    def test_init(self):
        tx_in = tx.DecredTxIn(self.outpoint, self.sequence)

        self.assertEqual(tx_in, helpers.DCR['ser']['tx']['in_unsigned'])

    def test_init_bad_outpoint(self):
        with self.assertRaises(ValueError) as context:
            tx.DecredTxIn('Hello World', self.sequence)
        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_init_bad_sequnce(self):
        with self.assertRaises(ValueError) as context:
            tx.DecredTxIn(self.outpoint, 'Hello World')
        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_copy(self):
        res = tx.DecredTxIn(self.outpoint, self.sequence)
        copy = res.copy()
        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)


class TestDecredTxOut(DecredTestCase):

    def setUp(self):
        super().setUp()
        self.value = helpers.DCR['ser']['outs'][0]['value']
        self.version = helpers.DCR['ser']['outs'][0]['version']
        self.output_script = helpers.DCR['ser']['outs'][0]['pk_script']

    def test_init(self):
        tx_out = tx.DecredTxOut(
            self.value, self.version, self.output_script)

        self.assertEqual(tx_out, helpers.DCR['ser']['outs'][0]['output'])

    def test_bad_value(self):
        with self.assertRaises(ValueError) as context:
            tx.DecredTxOut('Hello World', self.version, self.output_script)
        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_bad_version(self):
        with self.assertRaises(ValueError) as context:
            tx.DecredTxOut(self.value, 'Hello World', self.output_script)
        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_bad_script(self):
        with self.assertRaises(ValueError) as context:
            tx.DecredTxOut(self.value, self.version, 'Hello World')
        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_copy(self):
        res = tx.DecredTxOut(
            self.value, self.version, self.output_script)
        copy = res.copy()
        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)

    def test_from_bytes_long(self):
        with self.assertRaises(NotImplementedError) as context:
            tx.DecredTxOut.from_bytes(b'\xff' * 1000)
        self.assertIn(
            'No support for abnormally long pk_scripts.',
            str(context.exception))


class TestDecredInputWitness(DecredTestCase):

    def setUp(self):
        super().setUp()
        helper_witness = helpers.DCR['ser']['witnesses'][0]
        self.value = helper_witness['value']
        self.height = helper_witness['height']
        self.index = helper_witness['index']
        self.stack_script = helper_witness['stack_script']
        self.redeem_script = helper_witness['redeem_script']

    def test_init(self):
        input_witness = tx.DecredInputWitness(
            value=self.value,
            height=self.height,
            index=self.index,
            stack_script=self.stack_script,
            redeem_script=self.redeem_script)

        self.assertEqual(
            input_witness,
            helpers.DCR['ser']['witnesses'][0]['witness'])

    def test_init_errors(self):

        with self.assertRaises(ValueError) as context:
            tx.DecredInputWitness('Hello World', self.height, self.index,
                                  self.stack_script, self.redeem_script)

        self.assertIn('Expected byte-like object', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredInputWitness(self.value, 'Hello World', self.index,
                                  self.stack_script, self.redeem_script)

        self.assertIn('Expected byte-like object', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredInputWitness(self.value, self.height, 'Hello World',
                                  self.stack_script, self.redeem_script)

        self.assertIn('Expected byte-like object', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredInputWitness(self.value, self.height, self.index,
                                  'Hello World', self.redeem_script)

        self.assertIn('Expected byte-like object', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredInputWitness(self.value, self.height, self.index,
                                  self.redeem_script, 'Hello World')

        self.assertIn('Expected byte-like object', str(context.exception))

    def test_copy(self):
        res = tx.DecredInputWitness(
            value=self.value,
            height=self.height,
            index=self.index,
            stack_script=self.stack_script,
            redeem_script=self.redeem_script)
        copy = res.copy()

        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)

    def test_from_bytes(self):
        with self.assertRaises(NotImplementedError) as context:
            tx.DecredInputWitness.from_bytes(self)

        self.assertIn('Not Yet Implemented', str(context.exception))


class TestDecredTx(DecredTestCase):

    def setUp(self):
        super().setUp()

        self.version = helpers.DCR['ser']['version']

        self.outpoint_index = helpers.DCR['ser']['ins'][0]['index']
        self.outpoint_tx_id = helpers.DCR['ser']['ins'][0]['hash']
        self.outpoint_tree = helpers.DCR['ser']['ins'][0]['tree']
        self.sequence = helpers.DCR['ser']['ins'][0]['sequence']

        self.outpoint = tx.DecredOutpoint(
            self.outpoint_tx_id, self.outpoint_index, self.outpoint_tree)
        self.tx_in = tx.DecredTxIn(self.outpoint, self.sequence)

        self.output_value = helpers.DCR['ser']['outs'][0]['value']
        self.output_version = helpers.DCR['ser']['outs'][0]['version']
        self.output_script = helpers.DCR['ser']['outs'][0]['pk_script']
        self.tx_out = tx.DecredTxOut(
            self.output_value, self.output_version, self.output_script)

        self.lock_time = helpers.DCR['ser']['locktime']
        self.expiry = helpers.DCR['ser']['expiry']

        self.witness_value = helpers.DCR['ser']['witnesses'][0]['value']
        self.height = helpers.DCR['ser']['witnesses'][0]['height']
        self.witness_index = helpers.DCR['ser']['witnesses'][0]['index']
        self.stack_script = helpers.DCR['ser']['witnesses'][0]['stack_script']
        self.redeem_script = \
            helpers.DCR['ser']['witnesses'][0]['redeem_script']
        self.witness = tx.DecredInputWitness(
            value=self.witness_value,
            height=self.height,
            index=self.witness_index,
            stack_script=self.stack_script,
            redeem_script=self.redeem_script)

    def test_init(self):
        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        self.assertEqual(transaction, helpers.DCR['ser']['tx']['p2sh_2_p2pkh'])

    def test_init_errors(self):
        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version='Hello World',
                tx_ins=[self.tx_in],
                tx_outs=[self.tx_out],
                lock_time=self.lock_time,
                expiry=self.expiry,
                tx_witnesses=[self.witness])

            self.assertIn('Expected byte-like object', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version=self.version,
                tx_ins=['Hello World'],
                tx_outs=[self.tx_out],
                lock_time=self.lock_time,
                expiry=self.expiry,
                tx_witnesses=[self.witness])

        self.assertIn('Invalid TxIn.', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version=self.version,
                tx_ins=[self.tx_in],
                tx_outs=['Hello World'],
                lock_time=self.lock_time,
                expiry=self.expiry,
                tx_witnesses=[self.witness])

        self.assertIn('Invalid TxOut.', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version=self.version,
                tx_ins=[self.tx_in],
                tx_outs=[self.tx_out],
                lock_time='Hello World',
                expiry=self.expiry,
                tx_witnesses=[self.witness])

        self.assertIn('Expected byte-like object', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version=self.version,
                tx_ins=[self.tx_in],
                tx_outs=[self.tx_out],
                lock_time=self.lock_time,
                expiry='Hello World',
                tx_witnesses=[self.witness])

        self.assertIn('Expected byte-like object', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version=self.version,
                tx_ins=[self.tx_in],
                tx_outs=[self.tx_out],
                lock_time=self.lock_time,
                expiry=self.expiry,
                tx_witnesses=['Hello World'])

        self.assertIn('Invalid TxWitness', str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version=self.version,
                tx_ins=[self.tx_in] * 256,
                tx_outs=[self.tx_out],
                lock_time=self.lock_time,
                expiry=self.expiry,
                tx_witnesses=[self.witness] * 256)

        self.assertIn('Too many inputs or outputs. Stop that.',
                      str(context.exception))

        # with self.assertRaises(ValueError) as context:
        #     tx.DecredTx(
        #         version=self.version,
        #         tx_ins=[self.tx_in] * 2,
        #         tx_outs=[self.tx_out],
        #         lock_time=self.lock_time,
        #         expiry=self.expiry,
        #         tx_witnesses=[self.witness])
        #
        # self.assertIn('Witness and TxIn lists must be same length. ',
        #               str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version=self.version,
                tx_ins=[],
                tx_outs=[self.tx_out],
                lock_time=self.lock_time,
                expiry=self.expiry,
                tx_witnesses=[])

        self.assertIn('Too few inputs or outputs. Stop that.',
                      str(context.exception))

        long_witness = tx.DecredInputWitness(
            self.witness_value,
            self.height,
            self.witness_index,
            self.stack_script * 64,
            self.redeem_script * 64)
        with self.assertRaises(ValueError) as context:
            tx.DecredTx(
                version=self.version,
                tx_ins=[self.tx_in] * 255,
                tx_outs=[self.tx_out] * 255,
                lock_time=self.lock_time,
                expiry=self.expiry,
                tx_witnesses=[long_witness] * 255)

        self.assertIn('Tx is too large. Expect less than 100kB.',
                      str(context.exception))

    def test_tx_id(self):
        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        self.assertEqual(transaction.tx_id, helpers.DCR['ser']['tx']['hash'])
        self.assertEqual(
            transaction.tx_id_le,
            helpers.DCR['ser']['tx']['hash_le'])

    def test_calculate_fee(self):
        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        self.assertEqual(transaction.calculate_fee(), 33400)

    def test_from_bytes(self):
        with self.assertRaises(NotImplementedError) as context:
            tx.DecredTx.from_bytes(self)

        self.assertIn('Not Yet Implemented', str(context.exception))  # TODO

    def test_witness_signing_hash(self):
        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        test_witness_hash = transaction.witness_signing_hash()
        expected = utils.blake256(tx.DecredTx.witness_signing(transaction))

        self.assertEqual(test_witness_hash, expected)

    def test_witness(self):
        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])
        tx_wit = b'\x01\x00' + b'\x02\x00' + b'\x01' + \
            helpers.DCR['ser']['witnesses'][0]['witness']
        self.assertEqual(transaction.witness(), tx_wit)

    def test_witness_hash(self):
        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        self.assertEqual(
            transaction.witness_hash(),
            helpers.DCR['ser']['witnesses'][0]['hash'])

    def test_script_code(self):
        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        self.assertEqual(
            transaction.script_code(index=0),
            helpers.DCR['ser']['witnesses'][0]['redeem_script'])

    def test_script_code_fail(self):
        self.witness = tx.DecredInputWitness(
            value=self.witness_value,
            height=self.height,
            index=self.witness_index,
            stack_script=self.stack_script,
            redeem_script=b'')

        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        self.assertIsNone(transaction.script_code(index=0))

    def test_sighash_none(self):
        transaction = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        with self.assertRaises(NotImplementedError) as context:
            transaction.sighash_none()

        self.assertIn(
            'SIGHASH_NONE is a bad idea.',
            str(context.exception))

    def test_copy(self):
        res = tx.DecredTx(
            version=self.version,
            tx_ins=[self.tx_in],
            tx_outs=[self.tx_out],
            lock_time=self.lock_time,
            expiry=self.expiry,
            tx_witnesses=[self.witness])

        copy = res.copy()

        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)

    def test_txhash(self):
        '''
        https://github.com/decred/dcrd/blob/master/wire/msgtx_test.go#L139-L140
        '''
        outpoint = tx.DecredOutpoint(
            tx_id=b'\x00' * 32,
            index=b'\xff' * 4,
            tree=b'\x00')
        tx_ins = [tx.DecredTxIn(outpoint=outpoint, sequence=b'\xff' * 4)]
        tx_outs = [tx.DecredTxOut(value=utils.i2le_padded(5000000000, 8),
                                  version=b'\xf0\xf0',
                                  output_script=helpers.DCR['ser']['hash_pk'])]
        tx_witnesses = [
            tx.DecredInputWitness(value=utils.i2le_padded(5000000000, 8),
                                  height=b'\x34' * 4,
                                  index=b'\x2E' * 4,
                                  stack_script=bytes([0x04, 0x31, 0xdc, 0x00,
                                                      0x1b, 0x01, 0x62]),
                                  redeem_script=b'')]
        version = helpers.DCR['ser']['version']
        t = tx.DecredTx(
            version=version,
            tx_ins=tx_ins,
            tx_outs=tx_outs,
            lock_time=b'\x00' * 4,
            expiry=b'\x00' * 4,
            tx_witnesses=tx_witnesses)

        self.assertEqual(t.tx_id, helpers.DCR['ser']['tx']['expected_hash'])

    def test_sighash(self):
        # test_sighash setup:
        tx_in_0 = tx.DecredTxIn.from_bytes(helpers.DCR1['ser']['ins'][0]['in'])
        tx_in_1 = tx.DecredTxIn.from_bytes(helpers.DCR1['ser']['ins'][1]['in'])
        tx_in_2 = tx.DecredTxIn.from_bytes(helpers.DCR1['ser']['ins'][2]['in'])

        tx_ins = [tx_in_0, tx_in_1, tx_in_2]

        tx_out_0 = tx.DecredTxOut.from_bytes(
            helpers.DCR1['ser']['outs'][0]['output'])
        tx_out_1 = tx.DecredTxOut.from_bytes(
            helpers.DCR1['ser']['outs'][1]['output'])

        tx_outs = [tx_out_0, tx_out_1]

        tx_witness_0 = tx.DecredInputWitness(
            value=helpers.DCR1['ser']['witness'][0]['value'],
            height=helpers.DCR1['ser']['witness'][0]['height'],
            index=helpers.DCR1['ser']['witness'][0]['index'],
            stack_script=helpers.DCR1['ser']['witness'][0]['stack_script'],
            redeem_script=b'')
        tx_witness_1 = tx.DecredInputWitness(
            value=helpers.DCR1['ser']['witness'][1]['value'],
            height=helpers.DCR1['ser']['witness'][1]['height'],
            index=helpers.DCR1['ser']['witness'][1]['index'],
            stack_script=helpers.DCR1['ser']['witness'][1]['stack_script'],
            redeem_script=b'')
        tx_witness_2 = tx.DecredInputWitness(
            value=helpers.DCR1['ser']['witness'][2]['value'],
            height=helpers.DCR1['ser']['witness'][2]['height'],
            index=helpers.DCR1['ser']['witness'][2]['index'],
            stack_script=helpers.DCR1['ser']['witness'][2]['stack_script'],
            redeem_script=b'')

        tx_witnesses = [tx_witness_0, tx_witness_1, tx_witness_2]

        t = tx.DecredTx(
            version=helpers.DCR1['ser']['version'],
            tx_ins=tx_ins,
            tx_outs=tx_outs,
            lock_time=helpers.DCR1['ser']['locktime'],
            expiry=helpers.DCR1['ser']['expiry'],
            tx_witnesses=tx_witnesses)

        # test sighash_all:
        self.assertEqual(
            t.sighash_all(
                index=0,
                script=helpers.SIGHASH_DCR['prevout_pk']),
            helpers.SIGHASH_DCR['all'])

        # test all_anyonecanpay:
        self.assertEqual(
            t.sighash_all(
                index=0,
                script=helpers.SIGHASH_DCR['prevout_pk'],
                anyone_can_pay=True),
            helpers.SIGHASH_DCR['all_anyonecanpay'])

#        # test sighash_single:
#        self.assertEqual(
#            t.sighash_single(
#                index=0,
#                script=helpers.SIGHASH_DCR['prevout_pk']),
#            helpers.SIGHASH_DCR['single'])
#
#        # test single_anyonecanpay:
#        self.assertEqual(
#            t.sighash_single(
#                index=0,
#                script=helpers.SIGHASH_DCR['prevout_pk'],
#                anyone_can_pay=True),
#            helpers.SIGHASH_DCR['single_anyonecanpay'])
