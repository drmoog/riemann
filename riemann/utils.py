import hashlib
import riemann
from . import blake256 as b256


def i2le(number):
    '''
    Args:
        number (int)
    Returns:
        bytearray
    '''
    if number == 0:
        return b'\x00'
    return number.to_bytes((number.bit_length() + 7) // 8, 'little')


def i2le_padded(number, length):
    '''
    Args:
        number (int)
        length (int)
    Returns:
        bytearray
    '''
    return number.to_bytes(length, 'little')


def le2i(b, signed=False):
    '''
    Args:
        b (byte-like)
        signed (bool)
    Returns:
        int
    '''
    return int.from_bytes(b, 'little', signed=signed)


def be2i(b, signed=False):
    '''
    Args:
        b (byte-like)
        signed (bool)
    Returns:
        int
    '''
    return int.from_bytes(b, 'big', signed=signed)


def change_endianness(b):
    '''
    Args:
        b (iter)
    Returns:
        iter
    '''
    return b[::-1]


def rmd160(msg_bytes):
    '''
    Args:
        msg_bytes (byte-like)
    Returns:
        bytes
    '''
    h = hashlib.new('ripemd160')
    h.update(msg_bytes)
    return h.digest()


def sha256(msg_bytes):
    '''
    Args:
        msg_bytes (byte-like)
    Returns:
        bytes
    '''
    return hashlib.sha256(msg_bytes).digest()


def hash160(msg_bytes):
    '''
    Args:
        msg_bytes (byte-like)
    Returns:
        bytes
    '''
    h = hashlib.new('ripemd160')
    if 'decred' in riemann.get_current_network_name():
        h.update(blake256(msg_bytes))
        return h.digest()
    h.update(sha256(msg_bytes))
    return h.digest()


def hash256(msg_bytes):
    '''
    Args:
        msg_bytes (byte-like)
    Returns:
        bytes
    '''
    if 'decred' in riemann.get_current_network_name():
        return blake256(blake256(msg_bytes))
    return hashlib.sha256(hashlib.sha256(msg_bytes).digest()).digest()


def blake256(msg_bytes):
    '''
    Args:
        msg_bytes (byte-like)
    Returns:
        bytes
    '''
    return b256.blake_hash(msg_bytes)
