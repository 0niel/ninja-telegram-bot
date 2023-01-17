import base64
import random
import string
import urllib

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

from bot import config


def serialize_params(obj):
    return urllib.parse.urlencode(obj)


def generate_nonce() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))


def generate_rsa_keys() -> dict:
    """Generate RSA keys for the app."""

    key = RSA.generate(2048)

    private_key = key.export_key().decode()
    public_key = key.publickey().export_key().decode()

    return {"private": private_key, "public": public_key}


def decode_payload(payload: str, private_key: str):
    """Decode payload from Discourse"""
    payload = urllib.parse.unquote(payload)
    payload = payload.replace(" ", "")
    payload = base64.b64decode(payload)

    key = RSA.import_key(private_key)
    cipher = PKCS1_v1_5.new(key)
    sentinel = get_random_bytes(16)  # 16 bytes is the block size of AES
    return cipher.decrypt(payload, sentinel).decode()


def generate_auth_url(client_id: int, public_key: str, nonce: str):
    scopes = "session_info,notifications,push,message_bus,read"  # one_time_password

    params = {
        "scopes": scopes,
        "client_id": client_id,
        "nonce": nonce,
        "auth_redirect": f"{config.get_settings().HOST}/auth",
        "application_name": "Ninja Telegram Bot",
        "public_key": public_key,
        # "push_url": f"{config.get_settings().HOST}/push",
    }

    return f"{config.get_settings().DISCOURSE_URL}/user-api-key/new?{serialize_params(params)}"
