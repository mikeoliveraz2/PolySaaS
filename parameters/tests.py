from cryptography.fernet import Fernet
from django.test import TestCase, override_settings

from parameters.crypto import decrypt_json_dict, encrypt_json_dict
from parameters.models import Parameter


class ParameterCryptoTests(TestCase):
    @override_settings(PARAMETER_FERNET_KEY=Fernet.generate_key().decode("ascii"))
    def test_encrypt_decrypt_roundtrip(self):
        token = encrypt_json_dict({"k": "v", "n": 1})
        self.assertIsInstance(token, str)
        out = decrypt_json_dict(token)
        self.assertEqual(out, {"k": "v", "n": 1})

    @override_settings(PARAMETER_FERNET_KEY="")
    def test_model_get_decrypted_secrets_empty(self):
        p = Parameter.objects.create(matchingKey="X", sequence=1)
        self.assertEqual(p.get_decrypted_secrets(), {})
