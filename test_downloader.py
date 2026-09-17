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
import types

sys.path.insert(0, os.path.dirname(__file__))

# Dynamically load the all-in-one engine directly from Colab_Downloader.ipynb
_nb_path = os.path.join(os.path.dirname(__file__), "Colab_Downloader.ipynb")
with open(_nb_path, "r", encoding="utf-8") as _nb_f:
    _nb_data = json.load(_nb_f)

_cell_code = "".join(_nb_data["cells"][2]["source"])
_clean_code = "\n".join([_line for _line in _cell_code.splitlines() if not _line.strip().startswith("!")])

_mod = types.ModuleType("colab_downloader")
_mod.__file__ = os.path.abspath(_nb_path)
exec(_clean_code, _mod.__dict__)
sys.modules["colab_downloader"] = _mod

JD2Service = _mod.JD2Service
ColabDownloaderApp = _mod.ColabDownloaderApp
transfer_to_google_drive = _mod.transfer_to_google_drive
sanitize_filename = _mod.sanitize_filename
format_size = _mod.format_size
get_colab_disk_info = _mod.get_colab_disk_info
resolve_yandex_disk_direct_link = _mod.resolve_yandex_disk_direct_link
download_direct = _mod.download_direct
save_credentials_to_drive = _mod.save_credentials_to_drive
load_credentials_from_drive = _mod.load_credentials_from_drive




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
    def __init__(self):
        self.state = "STOPPED"
        self.start_called = 0
        self.force_called = 0

    def start_downloads(self):
        self.state = "RUNNING"
        self.start_called += 1

    def get_current_state(self):
        return self.state

    def force_download(self, link_ids=None, package_ids=None):
        self.state = "RUNNING"
        self.force_called += 1

    def get_speed_in_bytes(self):
        return 1024 * 1024 * 15  # 15 MB/s


class MockDownloads:
    def __init__(self):
        self.links = []
        self.packages = []
        self.force_called = 0

    def query_links(self, params=None):
        return list(self.links)

    def query_packages(self, params=None):
        return list(self.packages)

    def force_download(self, link_ids=None, package_ids=None):
        self.force_called += 1


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

        with open(general_cfg, "r") as f:
            general_data = json.load(f)
            self.assertIn("Downloads", general_data.get("defaultdownloadfolder"))
            self.assertFalse(general_data.get("createpreallocatedlargefiles"))
            self.assertFalse(general_data.get("createpreallocatedlargefilesenabled"))
            self.assertFalse(general_data.get("useallocatesparsefile"))
            self.assertEqual(general_data.get("maxchunksperserver"), 1)
            self.assertEqual(general_data.get("maxchunksperdownload"), 1)
            self.assertEqual(general_data.get("maxsimultanousdownloads"), 1)

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
        self.assertIn("MyDrive/Downloads/", app.queue_list.options[0])

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

    def test_insert_sample_link(self):
        mock_service = MockJDService(self.test_dir)
        app = ColabDownloaderApp(jd_service=mock_service)
        app._on_insert_sample()
        self.assertIn("https://disk.yandex.com/d/7OcBsRWfzoTozg", app.text_area.value)

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

    def test_yandex_disk_sample_link(self):
        import requests
        sample_url = "https://disk.yandex.com/d/7OcBsRWfzoTozg"
        api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources?public_key={sample_url}"
        resp = requests.get(api_url, timeout=15)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("name", "").endswith(".rar"))
        self.assertGreater(data.get("size", 0), 1024 * 1024 * 1000)  # ~9.55 GB

    def test_get_colab_disk_info(self):
        info = get_colab_disk_info()
        self.assertIn("total_gb", info)
        self.assertIn("used_gb", info)
        self.assertIn("free_gb", info)
        self.assertGreater(info["total_gb"], 0)

    def test_resolve_yandex_disk_direct_link(self):
        sample_url = "https://disk.yandex.com/d/7OcBsRWfzoTozg"
        res = resolve_yandex_disk_direct_link(sample_url)
        self.assertIsNotNone(res)
        dl_url, fname, fsize = res
        self.assertTrue(dl_url.startswith("http"))
        self.assertTrue(fname.endswith(".rar"))
        self.assertGreater(fsize, 1024 * 1024 * 1000)

    def test_download_direct_empty_urls(self):
        res = download_direct("")
        self.assertFalse(res["success"])
        self.assertEqual(len(res["files"]), 0)

    def test_myjd_login_ui(self):
        mock_service = MockJDService(self.test_dir)
        app = ColabDownloaderApp(jd_service=mock_service)
        self.assertTrue(hasattr(app, "btn_login"))
        self.assertIn("Login", app.btn_login.description)

        # Test empty credentials check
        app.myjd_email.value = ""
        app.myjd_pass.value = ""
        app._on_login_myjd()
        self.assertIn("Vui lòng nhập đầy đủ", app.status_label.value)

        # Test Drive persistence functions
        save_credentials_to_drive("colab_user@test.com", "mypass123", "Test_Device")
        loaded = load_credentials_from_drive()
        self.assertEqual(loaded.get("email"), "colab_user@test.com")
        self.assertEqual(loaded.get("password"), "mypass123")


    def test_app_disk_info_widget(self):
        mock_service = MockJDService(self.test_dir)
        app = ColabDownloaderApp(jd_service=mock_service)
        self.assertIsNotNone(app.disk_info_widget)
        self.assertIn("Dung lượng Colab", app.disk_info_widget.value)
        self.assertIn("GB", app.disk_info_widget.value)

    def test_queue_start_auto_kicks_stopped_state(self):
        mock_service = MockJDService(self.test_dir)
        app = ColabDownloaderApp(jd_service=mock_service)

        # Setup pending items
        app.pending_items = [{
            "uuid": 1001,
            "packageUUID": 500,
            "name": "large_archive.zip",
            "bytesTotal": 1024 * 1024 * 100,
            "url": "https://example.com/test.zip"
        }]
        app.update_queue_display()
        app.queue_list.value = (app.queue_list.options[0],)

        # Ensure start state is STOPPED
        mock_service.device.downloadcontroller.state = "STOPPED"
        self.assertEqual(mock_service.device.downloadcontroller.get_current_state(), "STOPPED")

        # Trigger start download
        app._on_queue_start()

        # Downloadcontroller should be actively transitioned to RUNNING
        self.assertEqual(mock_service.device.downloadcontroller.get_current_state(), "RUNNING")
        self.assertGreaterEqual(mock_service.device.downloadcontroller.start_called, 1)

        # Test _monitor_tick auto-kick when controller dropped to STOPPED
        mock_service.device.downloadcontroller.state = "STOPPED"
        mock_service.device.downloads.links = [{
            "uuid": 1001,
            "name": "large_archive.zip",
            "bytesTotal": 1000,
            "bytesLoaded": 500,
            "speed": 1024 * 1024 * 5,
            "running": True,
            "finished": False,
            "status": "Downloading..."
        }]

        completed = set()
        done, cycles = app._monitor_tick([1001], [500], completed, 0)
        self.assertFalse(done)
        # Verify controller was auto-kicked back to RUNNING
        self.assertEqual(mock_service.device.downloadcontroller.get_current_state(), "RUNNING")
        self.assertIn("50%", app.progress_bar.description)
        self.assertIn("Streaming", app.status_label.value)
        self.assertIn("large_archive.zip", app.status_label.value)

    def test_monitor_tick_completion(self):
        mock_service = MockJDService(self.test_dir)
        app = ColabDownloaderApp(jd_service=mock_service)

        mock_service.device.downloads.links = [{
            "uuid": 1001,
            "name": "done_file.mp4",
            "bytesTotal": 5000,
            "bytesLoaded": 5000,
            "speed": 0,
            "running": False,
            "finished": True,
            "status": "Finished"
        }]

        completed = set()
        done, cycles = app._monitor_tick([1001], [500], completed, 1)
        self.assertTrue(done)
        self.assertIn("done_file.mp4", completed)
        self.assertEqual(app.progress_bar.value, 100.0)

    def test_monitor_tick_auto_extraction_and_completion(self):
        mock_service = MockJDService(self.test_dir)
        app = ColabDownloaderApp(jd_service=mock_service)

        # 1. Simulating Extraction in progress
        mock_service.device.downloads.links = [{
            "uuid": 2001,
            "name": "archive.rar",
            "bytesTotal": 1024 * 1024 * 500,
            "bytesLoaded": 1024 * 1024 * 500,
            "speed": 0,
            "running": False,
            "finished": False,
            "status": "Extracting..."
        }]

        completed = set()
        done, cycles = app._monitor_tick([2001], [600], completed, 2)
        self.assertFalse(done)
        self.assertEqual(app.progress_bar.description, "Extracting...")
        self.assertIn("giải nén", app.status_label.value)

        # 2. Simulating Extraction completed and links cleaned up
        mock_service.device.downloads.links = [{
            "uuid": 2001,
            "name": "archive.rar",
            "bytesTotal": 1024 * 1024 * 500,
            "bytesLoaded": 1024 * 1024 * 500,
            "speed": 0,
            "running": False,
            "finished": True,
            "status": "Extraction: OK"
        }]
        done, cycles = app._monitor_tick([2001], [600], completed, 3)
        self.assertTrue(done)
        self.assertEqual(app.progress_bar.value, 100.0)


if __name__ == "__main__":
    unittest.main()


