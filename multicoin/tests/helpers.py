# From Dev++ slides
# https://docs.google.com/presentation/d/1YGZf1VKKOnCdpuaVzU35CAXy8uGcztq0OBlTNMGSmkw/edit?usp=sharing

from ..script import examples

version = bytes.fromhex('01000000')
num_inputs = bytes.fromhex('01')
outpoint_tx_id = bytes.fromhex('813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1')  # noqa: E501
outpoint_index = bytes.fromhex('00000000')
script_sig_len = bytes.fromhex('6b')
stack_script = bytes.fromhex('483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01')  # noqa: E501
redeem_script = bytes.fromhex('210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a')  # noqa: E501
sequence = bytes.fromhex('feffffff')
num_outputs = bytes.fromhex('02')
output_value_0 = bytes.fromhex('a135ef0100000000')
output_script_0 = bytes.fromhex('76a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac')  # noqa: E501
output_value_1 = bytes.fromhex('99c3980000000000')
output_script_1 = bytes.fromhex('76a9141c4bc762dd5423e332166702cb75f40df79fea1288ac')  # noqa: E501
lock_time = bytes.fromhex('19430600')

script_sig = bytes.fromhex('483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a')  # noqa: E501
outpoint = '813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d100000000'  # noqa: E501
tx_in = '813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff'  # noqa: E501
tx_out_0 = 'a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac'  # noqa: E501
tx_out_1 = '99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac'  # noqa: E501

P2PKH_SPEND = bytes.fromhex('0100000001813f79011acb80925dfe69b3def355fe914bd1d96a3f5f71bf8303c6a989c7d1000000006b483045022100ed81ff192e75a3fd2304004dcadb746fa5e24c5031ccfcf21320b0277457c98f02207a986d955c6e0cb35d446a89d3f56100f4d7f67801c31967743a9c8e10615bed01210349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278afeffffff02a135ef01000000001976a914bc3b654dca7e56b04dca18f2566cdaf02e8d9ada88ac99c39800000000001976a9141c4bc762dd5423e332166702cb75f40df79fea1288ac19430600')  # noqa: E501
'0349fc4e631e3624a545de3f89f5d8684c7b8138bd94bdd531d2e213bf016b278a'
# From blockchain.info
# https://blockchain.info/rawtx/0739d0c7b7b7ff5f991e8e3f72a6f5eb56563880df982c4ab813cd71bc7a6a03?format=hex

RAW_P2SH_TO_P2PKH = '010000000101d15c2cc4621b2a319ba53714e2709f8ba2dbaf23f8c35a4bddcb203f9b391000000000df473044022000e02ea97289a35181a9bfabd324f12439410db11c4e94978cdade6a665bf1840220458b87c34d8bb5e4d70d01041c7c2d714ea8bfaca2c2d2b1f9e5749c3ee17e3d012102ed0851f0b4c4458f80e0310e57d20e12a84642b8e097fe82be229edbd7dbd53920f6665740b1f950eb58d646b1fae9be28cef842da5e51dc78459ad2b092e7fd6e514c5163a914bb408296de2420403aa79eb61426bb588a08691f8876a91431b31321831520e346b069feebe6e9cf3dd7239c670400925e5ab17576a9140d22433293fe9652ea00d21c5061697aef5ddb296888ac0000000001d0070000000000001976a914f2539f42058da784a9d54615ad074436cf3eb85188ac00000000'  # noqa: E501


OP_IF_P2SH = '3MpTk145zbm5odhRALfT9BnUs8DB5w4ydw'
OP_IF_SCRIPT_HASH = bytes.fromhex('dccafab9536343713ef4b9a1d443a1b6ca8c8dd1')
OP_IF_OUTPUT_SCRIPT = b'\xa9' + OP_IF_SCRIPT_HASH + b'\x87'

# Use '00' * 65 and '11' * 65 as pubkeys
PK_0 = '00' * 65
PK_1 = '11' * 65
MSIG_TWO_TWO_SCRIPT = examples.msig_two_two.format(PK_0, PK_1)
MSIG_TWO_TWO_P2SH = '3R23EEkAzy7HPWKN8rcL4ZzSjEWNsipxWV'
MSIG_TWO_TWO_SCRIPT_HASH = bytes.fromhex('ffe3e2be6ba8d465041d3da1cdfe472b901b215a')  # noqa: E501
MSIG_TWO_TWO_OUTPUT_SCRIPT = b'\xa9' + MSIG_TWO_TWO_SCRIPT_HASH + b'\x87'

P2PKH_0 = '13VmALKHkCdSN1JULkP6RqW3LcbpWvgryV'
P2PKH_1 = '1N59mqr5yg38K11PTY2HdZTN7KmAHeCyHE'
