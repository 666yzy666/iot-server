import argparse
import shutil
import ipaddress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


@dataclass(frozen=True)
class CertificateOutput:
	certificate_path: Path
	private_key_path: Path


class CertificateAuthority:
	def __init__(self, workspace: Path):
		self.workspace = Path(workspace)
		self.output_dir = self.workspace / "output"
		self.ca_dir = self.output_dir / "ca"
		self.ca_private_dir = self.ca_dir / "private"
		self.private_dir = self.output_dir / "private"
		self.issued_dir = self.output_dir / "issued"

	@property
	def ca_cert_path(self) -> Path:
		return self.ca_dir / "ca.crt"

	@property
	def ca_key_path(self) -> Path:
		return self.ca_private_dir / "ca.key"

	def create_ca(self, common_name: str = "IoT Server Local CA", days: int = 3650) -> CertificateOutput:
		if self.ca_cert_path.exists() or self.ca_key_path.exists():
			raise FileExistsError(f"CA already exists under {self.ca_dir}")

		self.ca_private_dir.mkdir(parents=True, exist_ok=True)
		key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
		subject = self._name(common_name, organizational_unit="Development")
		now = self._now()
		cert = (
			x509.CertificateBuilder()
			.subject_name(subject)
			.issuer_name(subject)
			.public_key(key.public_key())
			.serial_number(x509.random_serial_number())
			.not_valid_before(now)
			.not_valid_after(now + timedelta(days=days))
			.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
			.add_extension(x509.KeyUsage(
				digital_signature=False,
				content_commitment=False,
				key_encipherment=False,
				data_encipherment=False,
				key_agreement=False,
				key_cert_sign=True,
				crl_sign=True,
				encipher_only=False,
				decipher_only=False,
			), critical=True)
			.add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
			.sign(key, hashes.SHA256())
		)

		self._write_private_key(self.ca_key_path, key)
		self._write_certificate(self.ca_cert_path, cert)
		return CertificateOutput(self.ca_cert_path, self.ca_key_path)

	def sign_server(self, common_name: str = "localhost", dns_name: str = "localhost", ip_address: str = "127.0.0.1", days: int = 825) -> CertificateOutput:
		return self._sign_leaf(
			name="server",
			common_name=common_name,
			organizational_unit="Server",
			days=days,
			extended_usage=ExtendedKeyUsageOID.SERVER_AUTH,
			san=x509.SubjectAlternativeName([
				x509.DNSName(dns_name),
				x509.IPAddress(ipaddress.ip_address(ip_address)),
			]),
			key_encipherment=True,
		)

	def sign_device(self, device_id: str, days: int = 365) -> CertificateOutput:
		return self._sign_leaf(
			name=device_id,
			common_name=device_id,
			organizational_unit="Devices",
			days=days,
			extended_usage=ExtendedKeyUsageOID.CLIENT_AUTH,
			san=x509.SubjectAlternativeName([x509.UniformResourceIdentifier(f"urn:iot-device:{device_id}")]),
			key_encipherment=False,
		)

	def _sign_leaf(self, name: str, common_name: str, organizational_unit: str, days: int, extended_usage: ExtendedKeyUsageOID, san: x509.SubjectAlternativeName, key_encipherment: bool) -> CertificateOutput:
		if not self.ca_cert_path.exists() or not self.ca_key_path.exists():
			raise FileNotFoundError("CA not found. Create it first.")

		self.private_dir.mkdir(parents=True, exist_ok=True)
		self.issued_dir.mkdir(parents=True, exist_ok=True)
		key_path = self.private_dir / f"{name}.key"
		cert_path = self.issued_dir / f"{name}.crt"
		if key_path.exists() or cert_path.exists():
			raise FileExistsError(f"Certificate or key already exists for {name}")

		ca_key = serialization.load_pem_private_key(self.ca_key_path.read_bytes(), password=None)
		ca_cert = x509.load_pem_x509_certificate(self.ca_cert_path.read_bytes())
		key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
		now = self._now()
		cert = (
			x509.CertificateBuilder()
			.subject_name(self._name(common_name, organizational_unit=organizational_unit))
			.issuer_name(ca_cert.subject)
			.public_key(key.public_key())
			.serial_number(x509.random_serial_number())
			.not_valid_before(now)
			.not_valid_after(now + timedelta(days=days))
			.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
			.add_extension(x509.KeyUsage(
				digital_signature=True,
				content_commitment=False,
				key_encipherment=key_encipherment,
				data_encipherment=False,
				key_agreement=False,
				key_cert_sign=False,
				crl_sign=False,
				encipher_only=False,
				decipher_only=False,
			), critical=True)
			.add_extension(x509.ExtendedKeyUsage([extended_usage]), critical=False)
			.add_extension(san, critical=False)
			.add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
			.add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
			.sign(ca_key, hashes.SHA256())
		)

		self._write_private_key(key_path, key)
		self._write_certificate(cert_path, cert)
		return CertificateOutput(cert_path, key_path)

	def _name(self, common_name: str, organizational_unit: str) -> x509.Name:
		return x509.Name([
			x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
			x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
			x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
			x509.NameAttribute(NameOID.ORGANIZATION_NAME, "IoT Server"),
			x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit),
			x509.NameAttribute(NameOID.COMMON_NAME, common_name),
		])

	def _now(self) -> datetime:
		return datetime.now(timezone.utc) - timedelta(minutes=1)

	def _write_private_key(self, path: Path, key) -> None:
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_bytes(key.private_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PrivateFormat.TraditionalOpenSSL,
			encryption_algorithm=serialization.NoEncryption(),
		))

	def _write_certificate(self, path: Path, cert: x509.Certificate) -> None:
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def main() -> None:
	parser = argparse.ArgumentParser(description="Create local CA and sign IoT server/device certificates.")
	parser.add_argument("--workspace", default=Path(__file__).resolve().parent, type=Path)
	subparsers = parser.add_subparsers(dest="command", required=True)

	ca_parser = subparsers.add_parser("create-ca")
	ca_parser.add_argument("--common-name", default="IoT Server Local CA")
	ca_parser.add_argument("--days", default=3650, type=int)

	server_parser = subparsers.add_parser("sign-server")
	server_parser.add_argument("--common-name", default="localhost")
	server_parser.add_argument("--dns-name", default="localhost")
	server_parser.add_argument("--ip-address", default="127.0.0.1")
	server_parser.add_argument("--days", default=825, type=int)

	device_parser = subparsers.add_parser("sign-device")
	device_parser.add_argument("--device-id", required=True)
	device_parser.add_argument("--days", default=365, type=int)

	subparsers.add_parser("install-server", help="Copy CA and server certificate files to certs/ for docker-compose mounts.")

	args = parser.parse_args()
	ca = CertificateAuthority(args.workspace)
	if args.command == "create-ca":
		output = ca.create_ca(args.common_name, args.days)
	elif args.command == "sign-server":
		output = ca.sign_server(args.common_name, args.dns_name, args.ip_address, args.days)
	elif args.command == "sign-device":
		output = ca.sign_device(args.device_id, args.days)
	else:
		root_certs = args.workspace.parent
		files = [
			(ca.ca_cert_path, root_certs / "ca.crt"),
			(ca.issued_dir / "server.crt", root_certs / "server.crt"),
			(ca.private_dir / "server.key", root_certs / "server.key"),
			(ca.ca_cert_path, root_certs / "cacert.pem"),
			(ca.issued_dir / "server.crt", root_certs / "cert.pem"),
			(ca.private_dir / "server.key", root_certs / "key.pem"),
		]
		for source, target in files:
			if not source.exists():
				raise FileNotFoundError(f"Missing {source}. Run create-ca and sign-server first.")
			shutil.copyfile(source, target)
		print(f"installed: {root_certs / 'ca.crt'}")
		print(f"installed: {root_certs / 'server.crt'}")
		print(f"installed: {root_certs / 'server.key'}")
		return

	print(f"certificate: {output.certificate_path}")
	print(f"private_key: {output.private_key_path}")


if __name__ == "__main__":
	main()
