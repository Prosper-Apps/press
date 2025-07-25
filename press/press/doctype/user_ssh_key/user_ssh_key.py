# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import base64
import shlex
import struct
import subprocess
from typing import ClassVar

import frappe
from frappe.model.document import Document

from press.api.client import dashboard_whitelist


class SSHKeyValueError(ValueError):
	pass


class SSHFingerprintError(ValueError):
	pass


class UserSSHKey(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		is_default: DF.Check
		is_removed: DF.Check
		ssh_fingerprint: DF.Data | None
		ssh_public_key: DF.Code
		user: DF.Link
	# end: auto-generated types

	dashboard_fields: ClassVar = ["ssh_fingerprint", "is_default", "user", "is_removed"]

	valid_key_types: ClassVar = [
		"ssh-rsa",
		"ssh-ed25519",
		"ecdsa-sha2-nistp256",
		"ecdsa-sha2-nistp384",
		"ecdsa-sha2-nistp521",
		"sk-ecdsa-sha2-nistp256@openssh.com",
		"sk-ssh-ed25519@openssh.com",
	]

	def check_embedded_key_type(self, key_type: str, key_bytes: bytes):
		type_len = struct.unpack(">I", key_bytes[:4])[0]  # >I is big endian unsigned int
		offset = 4 + type_len
		embedded_type = key_bytes[4:offset]
		if embedded_type.decode("utf-8") != key_type:
			raise SSHKeyValueError(f"Key type {key_type} does not match key")

	def validate(self):
		if self.is_removed:  # to allow removing invalid keys
			return
		msg = "You must supply a key in OpenSSH public key format. Please try copy/pasting the key using one of the commands in documentation."
		try:
			key_type, key, *comment = self.ssh_public_key.strip().split()
			if key_type not in self.valid_key_types:
				raise SSHKeyValueError(f"Key type has to be one of {', '.join(self.valid_key_types)}")
			key_bytes = base64.b64decode(key)
			self.check_embedded_key_type(key_type, key_bytes)
			self.generate_ssh_fingerprint(self.ssh_public_key.encode())
		except SSHKeyValueError as e:
			frappe.throw(
				f"{e!s}\n{msg}",
			)
		except Exception:
			frappe.throw(msg)

	def after_insert(self):
		if self.is_default:
			self.make_other_keys_non_default()

	def on_update(self):
		if self.has_value_changed("is_default") and self.is_default:
			self.make_other_keys_non_default()

	@dashboard_whitelist()
	def delete(self):
		if self.is_default:
			other_key = frappe.get_all(
				"User SSH Key",
				filters={"user": self.user, "name": ("!=", self.name)},
				fields=["name"],
				limit=1,
			)
			if other_key:
				frappe.db.set_value("User SSH Key", other_key[0].name, "is_default", True)

		if frappe.db.exists("SSH Certificate", {"user_ssh_key": self.name}):
			self.is_removed = 1
			self.save()

		else:
			super().delete()

	def make_other_keys_non_default(self):
		frappe.db.set_value(
			"User SSH Key",
			{"user": self.user, "is_default": True, "name": ("!=", self.name)},
			"is_default",
			False,
		)

	def generate_ssh_fingerprint(self, key_bytes: bytes):
		try:
			self.ssh_fingerprint = (
				subprocess.check_output(
					shlex.split("ssh-keygen -lf -"), stderr=subprocess.STDOUT, input=key_bytes
				)
				.decode()
				.split()[1]
				.split(":")[1]
			)
		except subprocess.CalledProcessError as e:
			raise SSHKeyValueError(f"Error generating fingerprint: {e.output.decode()}") from e
