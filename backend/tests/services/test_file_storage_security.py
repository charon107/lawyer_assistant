"""Path-traversal hardening for file storage.

User-controlled upload filenames flow into ``make_storage_filename`` and
``LocalFileStorage.save``. A filename containing ``../`` segments must not be
able to write outside the per-user directory. Chinese filenames (common in this
legal app) must be preserved.
"""

import pytest

from app.services.file_storage import LocalFileStorage, make_storage_filename


class TestMakeStorageFilename:
    @pytest.mark.parametrize(
        "evil",
        [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\cmd.exe",
            "/etc/shadow",
            "foo/../../bar.sh",
            "a\x00b.txt",
        ],
    )
    def test_strips_traversal_and_separators(self, evil: str):
        result = make_storage_filename(evil)
        # uuid prefix + sanitized name; no path separators or parent refs survive
        assert "/" not in result
        assert "\\" not in result
        assert ".." not in result
        assert "\x00" not in result

    def test_preserves_chinese_filename(self):
        result = make_storage_filename("劳动合同.pdf")
        assert "劳动合同" in result
        assert result.endswith(".pdf")


class TestLocalFileStorageSavePathSafety:
    @pytest.mark.anyio
    async def test_traversal_filename_stays_within_user_dir(self, tmp_path):
        storage = LocalFileStorage(base_dir=tmp_path)
        user_id = "user-123"
        storage_path = await storage.save(user_id, "../../evil.sh", b"payload")

        user_dir = (tmp_path / user_id).resolve()
        written = (tmp_path / storage_path).resolve()
        # Must resolve to a real file physically inside the user's directory.
        assert written.is_file()
        assert written.is_relative_to(user_dir)

    @pytest.mark.anyio
    async def test_normal_filename_roundtrips(self, tmp_path):
        storage = LocalFileStorage(base_dir=tmp_path)
        storage_path = await storage.save("u1", "report.pdf", b"data")
        assert await storage.load(storage_path) == b"data"
