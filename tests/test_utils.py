import unittest
from types import SimpleNamespace

from config import MAX_UPLOAD_BYTES
from src.utils import get_upload_bytes


class UploadValidationTests(unittest.TestCase):
    def test_unsupported_upload_type_is_rejected(self):
        with self.assertRaises(ValueError):
            get_upload_bytes(SimpleNamespace(name="resume.exe", getvalue=lambda: b"content"))

    def test_oversized_upload_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "10 MB"):
            get_upload_bytes(SimpleNamespace(
                name="resume.pdf",
                getvalue=lambda: b"x" * (MAX_UPLOAD_BYTES + 1),
            ))


if __name__ == "__main__":
    unittest.main()
