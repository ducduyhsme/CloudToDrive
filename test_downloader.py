"""
Unit and integration tests for colab_downloader.py with JDownloader 2 backend.
Verifies JD2 configuration generation, mock linkgrabber/downloads interaction,
queue operations, and Google Drive transfer logic.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json

sys.path.insert(0, os.path.dirname(__file__))

from colab_downloader import (
    JD2Service,
    ColabDownloaderApp,
    transfer_to_google_drive,
    sanitize_filename,
    format_size
)


class MockLinkgrabber:
    def __init__(self):
        self.links = []
        self._collecting = False

    def clear_list(self):
        self.links = []

    def add_links(self, params):
        raw_links = params[0].get("links", "").splitlines()
        for i, l in enumerate(raw_links, 1):
            name = l.split("/")[-1] if "/" in l else f"file_{i}"
            if not name or "." not in name:
                name = f"download_{i}.zip"
            self.links.append({
                "uuid": 1000 + i,
                "packageUUID": 500,
                "name": name,
                "bytesTotal": 1024 * 1024 * 50 * i,
                "url": l,
                "hosts": "test.com"
            })

    def is_collecting(self):
        return False

    def query_links(self, params=None):
        return list(self.links)

    def move_to_downloadlist(self, link_ids, package_ids):
        pass

    def remove_links(self, link_ids, package_ids):
        self.links = [l for l in self.links if l.get("uuid") not in link_ids]


class MockDownloadController:
    def start_downloads(self):
        pass

    def get_speed_in_bytes(self):
        return 1024 * 1024 * 15  # 15 MB/s


class MockDownloads:
    def query_links(self, params=None):
        return []


class MockJDDevice:
    def __init__(self):
        self.linkgrabber = MockLinkgrabber()
        self.downloadcontroller = MockDownloadController()
        self.downloads = MockDownloads()


class MockJDService(JD2Service):
    def __init__(self, jd_dir):
        super().__init__(jd_dir=jd_dir, port=3128)
        self.device = MockJDDevice()
        self._connected = True

    def _ensure_service_ready(self):
        return True


class TestJD2Downloader(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.local_temp = os.path.join(self.test_dir, "temp_downloads")
        self.mock_drive = os.path.join(self.test_dir, "drive", "MyDrive", "Downloads")
        os.makedirs(self.local_temp, exist_ok=True)
        os.makedirs(self.mock_drive, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("clean_file.mkv"), "clean_file.mkv")
        self.assertNotIn(":", sanitize_filename("bad:name?.mp4"))

    def test_format_size(self):
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1024 * 1024 * 50), "50.0 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024 * 3), "3.0 GB")

    def test_jd2_configuration_generation(self):
        service = JD2Service(jd_dir=self.test_dir)
        service.configure_settings(email="user@test.com", password="secret_password")

        remote_cfg = os.path.join(self.test_dir, "cfg", "org.jdownloader.api.RemoteAPIConfig.json")
        general_cfg = os.path.join(self.test_dir, "cfg", "org.jdownloader.settings.GeneralSettings.json")
        myjd_cfg = os.path.join(self.test_dir, "cfg", "org.jdownloader.api.myjdownloader.MyJDownloaderSettings.json")

        self.assertTrue(os.path.exists(remote_cfg))
        self.assertTrue(os.path.exists(general_cfg))
        self.assertTrue(os.path.exists(myjd_cfg))

        with open(remote_cfg, "r") as f:
            data = json.load(f)
            self.assertTrue(data.get("deprecatedapienabled"))

        with open(myjd_cfg, "r") as f:
            data = json.load(f)
            self.assertEqual(data.get("email"), "user@test.com")

    def test_queue_operations_with_mock_jd(self):
        mock_service = MockJDService(self.test_dir)
        app = ColabDownloaderApp(jd_service=mock_service)

        # Test link resolution with mock
        app.text_area.value = "https://rapidgator.net/file/1/video.mp4\nhttps://mediafire.com/file/2/archive.zip"
        app._ensure_service_ready = lambda: True

        app._on_resolve_links()

        self.assertEqual(len(app.pending_items), 2)
        self.assertEqual(len(app.queue_list.options), 2)
        self.assertIn("video.mp4", app.queue_list.options[0])

        # Test Sort
        app._on_queue_sort()
        self.assertTrue(app.pending_items[0]["name"] <= app.pending_items[1]["name"])

        # Test Up / Down
        first_name = app.pending_items[0]["name"]
        app.queue_list.value = (app.queue_list.options[1],)
        app._on_queue_up()
        self.assertEqual(app.pending_items[1]["name"], first_name)

        # Test Remove
        app.queue_list.value = (app.queue_list.options[0],)
        app._on_queue_remove()
        self.assertEqual(len(app.pending_items), 1)

    def test_transfer_to_google_drive(self):
        src_file = os.path.join(self.local_temp, "downloaded_package.bin")
        payload = b"JD2 Payload Bytes " * 1024 * 512
        with open(src_file, "wb") as f:
            f.write(payload)

        self.assertTrue(os.path.exists(src_file))
        success, dest_path = transfer_to_google_drive(src_file, self.mock_drive)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(dest_path))
        self.assertFalse(os.path.exists(src_file))  # Ensure cleaned up
        self.assertEqual(os.path.getsize(dest_path), len(payload))


if __name__ == "__main__":
    unittest.main()
