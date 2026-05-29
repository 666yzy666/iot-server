import tempfile
import unittest
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import ExtendedKeyUsageOID

from certs.ca.ca_tool import CertificateAuthority


class CertificateAuthorityTests(unittest.TestCase):
	def test_creates_ca_server_and_device_certificates(self):
		with tempfile.TemporaryDirectory() as tmp:
			workspace = Path(tmp)
			ca = CertificateAuthority(workspace)

			ca.create_ca(common_name="Test Local CA", days=3650)
			server = ca.sign_server(common_name="localhost", dns_name="localhost", ip_address="127.0.0.1", days=825)
			device = ca.sign_device(device_id="device001", days=365)

			output = workspace / "output"
			self.assertTrue((output / "ca" / "ca.crt").exists())
			self.assertTrue((output / "ca" / "private" / "ca.key").exists())
			self.assertTrue(server.certificate_path.exists())
			self.assertTrue(server.private_key_path.exists())
			self.assertTrue(device.certificate_path.exists())
			self.assertTrue(device.private_key_path.exists())
			self.assertTrue(server.certificate_path.is_relative_to(output))
			self.assertTrue(server.private_key_path.is_relative_to(output))
			self.assertTrue(device.certificate_path.is_relative_to(output))
			self.assertTrue(device.private_key_path.is_relative_to(output))

			server_cert = x509.load_pem_x509_certificate(server.certificate_path.read_bytes())
			device_cert = x509.load_pem_x509_certificate(device.certificate_path.read_bytes())

			server_usage = server_cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
			device_usage = device_cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value

			self.assertIn(ExtendedKeyUsageOID.SERVER_AUTH, server_usage)
			self.assertIn(ExtendedKeyUsageOID.CLIENT_AUTH, device_usage)


if __name__ == "__main__":
	unittest.main()
