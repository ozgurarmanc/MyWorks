import collections
import hashlib
import random


EllipticCurve = collections.namedtuple('EllipticCurve', 'name p a b g n h')

curve = EllipticCurve(
    'BN254',
    # Field characteristic.
    p=0x2523648240000001BA344D80000000086121000000000013A700000000000013,
    # Curve coefficients.
    a=0x0000000000000000000000000000000000000000000000000000000000000000,
    b=0x0000000000000000000000000000000000000000000000000000000000000002,
    # Base point.
    g=(0x2523648240000001BA344D80000000086121000000000013A700000000000012,
       0x0000000000000000000000000000000000000000000000000000000000000001),
    # Subgroup order.
    n=0x2523648240000001BA344D8000000007FF9F800000000010A10000000000000D,
    # Subgroup cofactor.
    h=0x01,
)
def inverse_mod(k, p):
    """Returns the inverse of k modulo p.
    This function returns the only integer x such that (x * k) % p == 1.
    k must be non-zero and p must be a prime.
    """
    if k == 0:
        raise ZeroDivisionError('division by zero')

    if k < 0:
        # k ** -1 = p - (-k) ** -1  (mod p)
        return p - inverse_mod(-k, p)

    # Extended Euclidean algorithm.
    s, old_s = 0, 1
    t, old_t = 1, 0
    r, old_r = p, k

    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t

    gcd, x, y = old_r, old_s, old_t

    assert gcd == 1
    assert (k * x) % p == 1

    return x % p


# Functions that work on curve points #########################################

def is_on_curve(point):
    """Returns True if the given point lies on the elliptic curve."""
    if point is None:
        # None represents the point at infinity.
        return True

    x, y = point

    return (y * y - x * x * x - curve.a * x - curve.b) % curve.p == 0

def point_neg(point):
    """Returns -point."""
    assert is_on_curve(point)

    if point is None:
        # -0 = 0
        return None

    x, y = point
    result = (x, -y % curve.p)

    assert is_on_curve(result)

    return result



def point_add(point1, point2):
    """Returns the result of point1 + point2 according to the group law."""
    assert is_on_curve(point1)
    assert is_on_curve(point2)

    if point1 is None:
        # 0 + point2 = point2
        return point2
    if point2 is None:
        # point1 + 0 = point1
        return point1

    x1, y1 = point1
    x2, y2 = point2

    if x1 == x2 and y1 != y2:
        # point1 + (-point1) = 0
        return None

    if x1 == x2:
        # This is the case point1 == point2.
        m = (3 * x1 * x1 + curve.a) * inverse_mod(2 * y1, curve.p)
    else:
        # This is the case point1 != point2.
        m = (y1 - y2) * inverse_mod(x1 - x2, curve.p)

    x3 = m * m - x1 - x2
    y3 = y1 + m * (x3 - x1)
    result = (x3 % curve.p,
              -y3 % curve.p)

    assert is_on_curve(result)

    return result


def scalar_mult(k, point):
    """Returns k * point computed using the double and point_add algorithm."""
    assert is_on_curve(point)

    if k % curve.n == 0 or point is None:
        return None

    if k < 0:
        # k * point = -k * (-point)
        return scalar_mult(-k, point_neg(point))

    result = None
    addend = point

    while k:
        if k & 1:
            # Add.
            result = point_add(result, addend)

        # Double.
        addend = point_add(addend, addend)

        k >>= 1

    assert is_on_curve(result)

    return result


# Keypair generation and ECDSA ################################################

def make_keypair():
    """Generates a random private-public key pair."""
    private_key = random.randrange(1, curve.n)
    public_key = scalar_mult(private_key, curve.g)
    return private_key, public_key




def hash_message(message):
    """Returns the truncated SHA521 hash of the message."""
    message_hash = hashlib.sha512(message).digest()
    e = int.from_bytes(message_hash, 'big')
    
    z = e 

    return z


"""
def sign_message(private_key, message):
    z = hash_message(message)

    r = 0
    s = 0

    while not r or not s:
        k = random.randrange(1, curve.n)
        x, y = scalar_mult(k, curve.g)

        r = x % curve.n
        s = ((z + r * private_key) * inverse_mod(k, curve.n)) % curve.n

    return (r, s)

def verify_signature(public_key, message, signature):
    z = hash_message(message)

    r, s = signature

    w = inverse_mod(s, curve.n)
    u1 = (z * w) % curve.n
    u2 = (r * w) % curve.n

    x, y = point_add(scalar_mult(u1, curve.g),
                     scalar_mult(u2, public_key))

    if (r % curve.n) == (x % curve.n):
        return 'signature matches'
    else:
        return 'invalid signature'

print('Curve:', curve.name)

private, public = make_keypair()
print("Private key:", hex(private))
print("Public key: (0x{:x}, 0x{:x})".format(*public))

msg = b'Hey'
signature = sign_message(private, msg)

print()
print('Message:', msg)
print('Signature: (0x{:x}, 0x{:x})'.format(*signature))
print('Verification:', verify_signature(public, msg, signature))

msg = b'Hi there!'
print()
print('Message:', msg)
print('Verification:', verify_signature(public, msg, signature))


msg = b'Hey'
print()
print('Message:', msg)
print("Public key: (0x{:x}, 0x{:x})".format(*public))
print('Verification:', verify_signature(public, msg, signature))
"""