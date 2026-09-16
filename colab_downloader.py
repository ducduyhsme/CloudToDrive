"""
Google Colab Multi-Link Downloader with JDownloader 2 Headless Engine
Author: Antigravity Assistant
Description: High-speed multi-source downloader for Google Colab powered by JDownloader 2 (JD2).
Supports 1000+ file hosting providers with an interactive ipywidgets GUI matching the
Ultimate Downloader layout. Downloads files and automatically transfers them to Google Drive Downloads.
"""

import os
import re
import sys
import time
import json
import shutil
import subprocess
import threading
from typing import List, Optional, Tuple, Dict, Any
from uuid import uuid4

# Check and import requests
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"])
    import requests

# Check and import myjdapi
try:
    import myjdapi
    from myjdapi import Myjdapi
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "myjdapi"])
    import myjdapi
    from myjdapi import Myjdapi

# Check and import ipywidgets & IPython
try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output, HTML
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ipywidgets"])
    import ipywidgets as widgets
    from IPython.display import display, clear_output, HTML

# Detect Google Colab environment
IS_COLAB = "google.colab" in sys.modules or os.path.exists("/content")

# Configure environment paths
if IS_COLAB:
    COLAB_ROOT = "/content"
    JD_INSTALL_DIR = os.path.join(COLAB_ROOT, "jdownloader")
    TEMP_DOWNLOAD_DIR = os.path.join(COLAB_ROOT, "temp_downloads")
    DRIVE_MOUNT_POINT = os.path.join(COLAB_ROOT, "drive")
    DRIVE_BASE = os.path.join(DRIVE_MOUNT_POINT, "MyDrive")
    if not os.path.exists(DRIVE_BASE) and os.path.exists(os.path.join(DRIVE_MOUNT_POINT, "My Drive")):
        DRIVE_BASE = os.path.join(DRIVE_MOUNT_POINT, "My Drive")
    DRIVE_DOWNLOADS = os.path.join(DRIVE_BASE, "Downloads")
else:
    COLAB_ROOT = os.path.abspath("./colab_env")
    JD_INSTALL_DIR = os.path.join(COLAB_ROOT, "jdownloader")
    TEMP_DOWNLOAD_DIR = os.path.join(COLAB_ROOT, "temp_downloads")
    DRIVE_BASE = os.path.join(COLAB_ROOT, "drive", "MyDrive")
    DRIVE_DOWNLOADS = os.path.join(DRIVE_BASE, "Downloads")

os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
os.makedirs(JD_INSTALL_DIR, exist_ok=True)


# --- UTILITY HELPERS ---
def format_size(bytes_val: int) -> str:
    """Format bytes into human-readable string."""
    if not bytes_val or bytes_val <= 0:
        return "Unknown size"
    val = float(bytes_val)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if val < 1024.0:
            return f"{val:.1f} {unit}"
        val /= 1024.0
    return f"{val:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent invalid characters across filesystems."""
    if not filename:
        return f"download_{int(time.time())}"
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", filename).strip()
    return cleaned if cleaned else f"download_{int(time.time())}"


# --- JDOWNLOADER 2 HEADLESS SERVICE MANAGER ---
class JD2Service:
    """Manages installation, configuration, daemon process, and connection for JDownloader 2."""

    def __init__(self, jd_dir: str = JD_INSTALL_DIR, port: int = 3128):
        self.jd_dir = jd_dir
        self.port = port
        self.cfg_dir = os.path.join(jd_dir, "cfg")
        self.jar_path = os.path.join(jd_dir, "JDownloader.jar")
        self.jd_api = Myjdapi()
        self.jd_api.set_app_key("ColabDownloaderApp")
        self.device = None
        self.process: Optional[subprocess.Popen] = None
        self._connected = False

    def is_installed(self) -> bool:
        return os.path.exists(self.jar_path) and os.path.getsize(self.jar_path) > 1024 * 100

    def install_prerequisites(self, status_callback: Optional[callable] = None):
        """Ensure Java JRE is installed on system."""
        if shutil.which("java") is None and IS_COLAB:
            if status_callback:
                status_callback("📦 Installing Java JRE (default-jre) for JDownloader 2...")
            try:
                subprocess.run(["apt-get", "update", "-qq"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["apt-get", "install", "-y", "-qq", "default-jre"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"⚠️ Warning installing Java: {e}")

    def download_jdownloader_jar(self, status_callback: Optional[callable] = None):
        """Download official JDownloader.jar if missing."""
        if not self.is_installed():
            if status_callback:
                status_callback("⬇️ Downloading JDownloader.jar...")
            url = "http://installer.jdownloader.org/JDownloader.jar"
            try:
                resp = requests.get(url, timeout=30, stream=True)
                resp.raise_for_status()
                with open(self.jar_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            except Exception as e:
                raise RuntimeError(f"Failed to download JDownloader.jar: {e}")

    def configure_settings(self, email: str = "", password: str = "", device_name: str = "Colab_Downloader"):
        """Write configuration JSON files for Local API and MyJDownloader."""
        os.makedirs(self.cfg_dir, exist_ok=True)

        # 1. Enable Local RemoteAPI on port 3128
        remote_api_cfg = os.path.join(self.cfg_dir, "org.jdownloader.api.RemoteAPIConfig.json")
        remote_api_data = {
            "deprecatedapienabled": True,
            "deprecatedapilocalhostonly": True
        }
        with open(remote_api_cfg, "w", encoding="utf-8") as f:
            json.dump(remote_api_data, f, indent=2)

        # 2. Configure General Download Settings
        general_cfg = os.path.join(self.cfg_dir, "org.jdownloader.settings.GeneralSettings.json")
        general_data = {
            "defaultdownloadfolder": TEMP_DOWNLOAD_DIR,
            "autoextractenabled": False,
            "maxsimultanousdownloads": 3,
            "maxchunksperserver": 16
        }
        with open(general_cfg, "w", encoding="utf-8") as f:
            json.dump(general_data, f, indent=2)

        # 3. Optional: MyJDownloader credentials for remote captcha solving
        if email and password:
            myjd_cfg = os.path.join(self.cfg_dir, "org.jdownloader.api.myjdownloader.MyJDownloaderSettings.json")
            myjd_data = {
                "email": email.strip(),
                "password": password.strip(),
                "devicename": device_name.strip(),
                "autoconnectenabledv2": True
            }
            with open(myjd_cfg, "w", encoding="utf-8") as f:
                json.dump(myjd_data, f, indent=2)

    def start_service(self, status_callback: Optional[callable] = None):
        """Start the JDownloader 2 process in background if not already active."""
        # Check if already responding
        try:
            if self.jd_api.direct_connect("127.0.0.1", self.port):
                self.device = self.jd_api.get_device()
                self._connected = True
                if status_callback:
                    status_callback("✅ Connected to running JDownloader 2 instance.")
                return True
        except Exception:
            pass

        if shutil.which("java") is None:
            if not IS_COLAB:
                # Running in local test environment without java
                return False
            raise RuntimeError("Java is required to run JDownloader 2.")

        if status_callback:
            status_callback("🚀 Starting JDownloader 2 Headless Service (this may take ~20s on first start)...")

        cmd = ["java", "-Djava.awt.headless=true", "-jar", self.jar_path]
        self.process = subprocess.Popen(
            cmd,
            cwd=self.jd_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Poll connection to Local API
        start_time = time.time()
        timeout = 60
        while time.time() - start_time < timeout:
            time.sleep(2)
            try:
                if self.jd_api.direct_connect("127.0.0.1", self.port):
                    self.device = self.jd_api.get_device()
                    self._connected = True
                    if status_callback:
                        status_callback("✅ JDownloader 2 connected successfully.")
                    return True
            except Exception:
                pass

        if status_callback:
            status_callback("⚠️ Could not connect to Local API within timeout.")
        return False

    def connect_myjd(self, email: str, password: str, device_name: str = "Colab_Downloader") -> bool:
        """Connect via MyJDownloader Cloud."""
        try:
            self.jd_api.connect(email, password)
            self.device = self.jd_api.get_device(device_name)
            self._connected = True
            return True
        except Exception as e:
            print(f"⚠️ MyJDownloader cloud connection error: {e}")
            return False


# --- GOOGLE DRIVE FILE TRANSFER ---
def transfer_to_google_drive(
    local_path: str,
    drive_folder: str = DRIVE_DOWNLOADS,
    progress_callback: Optional[callable] = None
) -> Tuple[bool, str]:
    """
    Safely transfers a completed file from Colab local disk to Google Drive.
    Uses buffered chunked transfer to avoid memory overhead and deletes local file to save disk space.
    """
    if not os.path.exists(local_path):
        return False, f"Source file does not exist: {local_path}"

    os.makedirs(drive_folder, exist_ok=True)
    filename = os.path.basename(local_path)
    dest_path = os.path.join(drive_folder, filename)

    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        dest_path = os.path.join(drive_folder, f"{base}_{int(time.time())}{ext}")

    file_size = os.path.getsize(local_path)
    copied_bytes = 0
    buffer_size = 16 * 1024 * 1024  # 16 MB

    if progress_callback:
        progress_callback(0, f"Transferring to Google Drive: {os.path.basename(dest_path)}")

    try:
        with open(local_path, "rb") as fsrc, open(dest_path, "wb") as fdst:
            while True:
                chunk = fsrc.read(buffer_size)
                if not chunk:
                    break
                fdst.write(chunk)
                copied_bytes += len(chunk)
                if progress_callback and file_size > 0:
                    pct = (copied_bytes / file_size) * 100.0
                    progress_callback(pct, f"Moving to Drive: {pct:.1f}% ({format_size(copied_bytes)} / {format_size(file_size)})")

        if os.path.exists(dest_path) and os.path.getsize(dest_path) == file_size:
            os.remove(local_path)  # Delete local copy to free Colab disk
            return True, dest_path
        else:
            return False, "File size mismatch after moving to Google Drive"
    except Exception as e:
        return False, f"Transfer error: {str(e)}"


# --- IPYWIDGETS GUI APPLICATION ---
class ColabDownloaderApp:
    """Builds and manages the interactive UI matching the user's screenshots with JDownloader 2 backend."""

    def __init__(self, jd_service: Optional[JD2Service] = None):
        self.jd = jd_service or JD2Service()
        self.pending_items: List[Dict[str, Any]] = []
        self.sort_ascending = True
        self.is_downloading = False

        # Custom CSS for Dark Jupyter / Colab theme
        self.css_styles = widgets.HTML("""
        <style>
            .colab-dl-container {
                background-color: #1e1e1e;
                color: #e0e0e0;
                padding: 16px;
                border-radius: 8px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            .widget-textarea textarea {
                background-color: #2d2d2d !important;
                color: #f1f1f1 !important;
                border: 1px solid #444 !important;
                border-radius: 4px !important;
                font-family: monospace !important;
                font-size: 13px !important;
            }
            .widget-textarea textarea::placeholder {
                color: #888 !important;
            }
            .widget-select-multiple select {
                background-color: #252526 !important;
                color: #d4d4d4 !important;
                border: 1px solid #3c3c3c !important;
                font-family: monospace !important;
                font-size: 13px !important;
            }
            .widget-select-multiple select option:checked {
                background-color: #04395e !important;
                color: #ffffff !important;
            }
            .queue-header {
                font-size: 14px;
                font-weight: bold;
                color: #f0f0f0;
                margin-bottom: 6px;
            }
        </style>
        """)

        # 1. Links Textarea (Image 1)
        self.text_area = widgets.Textarea(
            description='Links:',
            placeholder='Paste Links Here (Transfer.it, Mega, YouTube, etc.)...',
            layout=widgets.Layout(width='98%', height='140px')
        )

        # 2. Action Buttons (Image 2)
        self.btn_resolve = widgets.Button(
            description="Resolve Links",
            button_style='success',
            icon='search',
            tooltip='Resolve links with JDownloader 2 and show Queue Preview',
            layout=widgets.Layout(width='150px', height='36px')
        )
        self.btn_quick = widgets.Button(
            description="Quick Download",
            button_style='primary',
            icon='bolt',
            tooltip='Automatically resolve and download without preview',
            layout=widgets.Layout(width='160px', height='36px')
        )

        # 3. Queue Preview Container & Controls (Image 3)
        self.queue_header = widgets.HTML(
            "<div class='queue-header'>📄 <b>Queue Preview</b> <span style='font-weight:normal; color:#aaa;'>(Select items to manage)</span></div>"
        )
        self.queue_list = widgets.SelectMultiple(
            description='Queue:',
            options=[],
            layout=widgets.Layout(width='98%', height='160px')
        )

        # Toolbar Buttons (Under Queue Preview)
        self.btn_up = widgets.Button(description="▲ Up", layout=widgets.Layout(width='80px'))
        self.btn_down = widgets.Button(description="▼ Down", layout=widgets.Layout(width='80px'))
        self.btn_sort = widgets.Button(description="Sort A-Z", layout=widgets.Layout(width='90px'))
        self.btn_select_all = widgets.Button(description="Select All", layout=widgets.Layout(width='85px'))
        self.btn_none = widgets.Button(description="None", layout=widgets.Layout(width='65px'))
        self.btn_start = widgets.Button(
            description="▶ Start Download",
            button_style='success',
            layout=widgets.Layout(width='140px')
        )
        self.btn_cancel = widgets.Button(
            description="Cancel",
            button_style='warning',
            layout=widgets.Layout(width='75px')
        )
        self.btn_remove = widgets.Button(
            description="Remove",
            button_style='danger',
            layout=widgets.Layout(width='80px')
        )

        self.queue_toolbar = widgets.HBox([
            self.btn_up,
            self.btn_down,
            self.btn_sort,
            self.btn_select_all,
            self.btn_none,
            self.btn_start,
            self.btn_cancel,
            self.btn_remove
        ], layout=widgets.Layout(margin='8px 0 0 0'))

        self.queue_container = widgets.VBox([
            self.queue_header,
            self.queue_list,
            self.queue_toolbar
        ], layout=widgets.Layout(display='none', margin='12px 0'))

        # 4. Progress and Status Elements
        self.progress_bar = widgets.FloatProgress(
            value=0.0,
            min=0.0,
            max=100.0,
            description='Idle',
            bar_style='info',
            layout=widgets.Layout(width='98%', margin='8px 0')
        )
        self.status_label = widgets.HTML(value="")

        # Optional MyJDownloader Credentials Accordion (collapsed by default)
        self.myjd_email = widgets.Text(description='Email:', placeholder='my.jdownloader.org email (optional)', layout=widgets.Layout(width='280px'))
        self.myjd_pass = widgets.Password(description='Password:', placeholder='Password', layout=widgets.Layout(width='240px'))
        self.btn_save_cred = widgets.Button(description='Save Credentials', button_style='', layout=widgets.Layout(width='130px'))
        self.btn_save_cred.on_click(self._on_save_credentials)

        cred_box = widgets.VBox([
            widgets.HTML("<small style='color:#aaa;'>💡 Điền tài khoản MyJDownloader nếu muốn giải captcha từ xa cho các hoster bảo mật cao. Nếu không, JDownloader 2 sẽ chạy qua Local API không cần tài khoản.</small>"),
            widgets.HBox([self.myjd_email, self.myjd_pass, self.btn_save_cred])
        ])
        self.cred_accordion = widgets.Accordion(children=[cred_box])
        self.cred_accordion.set_title(0, '⚙️ Cấu hình MyJDownloader (Tùy chọn)')
        self.cred_accordion.selected_index = None  # collapsed by default

        self._bind_events()

    def _bind_events(self):
        """Bind UI events."""
        self.btn_resolve.on_click(self._on_resolve_links)
        self.btn_quick.on_click(self._on_quick_download)
        self.btn_up.on_click(self._on_queue_up)
        self.btn_down.on_click(self._on_queue_down)
        self.btn_sort.on_click(self._on_queue_sort)
        self.btn_select_all.on_click(self._on_queue_select_all)
        self.btn_none.on_click(self._on_queue_select_none)
        self.btn_start.on_click(self._on_queue_start)
        self.btn_cancel.on_click(self._on_queue_cancel)
        self.btn_remove.on_click(self._on_queue_remove)

    def _on_save_credentials(self, b=None):
        """Save MyJDownloader credentials."""
        email = self.myjd_email.value.strip()
        pwd = self.myjd_pass.value.strip()
        if email and pwd:
            self.jd.configure_settings(email=email, password=pwd)
            self.status_label.value = "<span style='color:#4caf50;'>✅ Saved MyJDownloader credentials.</span>"
        else:
            self.status_label.value = "<span style='color:#ff9800;'>⚠️ Please enter both email and password.</span>"

    def _ensure_service_ready(self) -> bool:
        """Make sure JDownloader 2 is initialized and connected."""
        if self.jd._connected and self.jd.device:
            return True

        def update_msg(msg: str):
            self.status_label.value = f"<span style='color:#29b6f6;'>{msg}</span>"

        # Check Colab Drive Mount
        if IS_COLAB:
            if not os.path.exists(os.path.join(COLAB_ROOT, "drive", "MyDrive")) and \
               not os.path.exists(os.path.join(COLAB_ROOT, "drive", "My Drive")):
                update_msg("📂 Mounting Google Drive...")
                try:
                    from google.colab import drive
                    drive.mount('/content/drive')
                except Exception as e:
                    print(f"Drive mount error: {e}")

        os.makedirs(DRIVE_DOWNLOADS, exist_ok=True)
        self.jd.install_prerequisites(update_msg)
        self.jd.download_jdownloader_jar(update_msg)
        self.jd.configure_settings(
            email=self.myjd_email.value.strip(),
            password=self.myjd_pass.value.strip()
        )
        ready = self.jd.start_service(update_msg)
        return ready

    def _extract_input_urls(self) -> List[str]:
        raw = self.text_area.value.strip()
        if not raw:
            return []
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def update_queue_display(self):
        """Refresh the Queue listbox."""
        options = []
        for i, item in enumerate(self.pending_items, 1):
            name = item.get("name") or item.get("filename") or "File"
            size_str = format_size(item.get("bytesTotal", 0))
            display_text = f"{i}. 📦 {name} ({size_str}) → Downloads/{name}"
            options.append(display_text)

        self.queue_list.options = options
        self.queue_list.value = tuple(options)

    def _on_resolve_links(self, b=None):
        """Resolve links with JDownloader 2 Linkgrabber and populate Queue Preview."""
        urls = self._extract_input_urls()
        if not urls:
            self.status_label.value = "<span style='color:#ffa000;'>⚠️ Please paste at least one link.</span>"
            return

        self.btn_resolve.disabled = True
        self.btn_quick.disabled = True
        self.status_label.value = "<span style='color:#29b6f6;'>🔍 Initializing JDownloader 2 Engine...</span>"

        if not self._ensure_service_ready():
            self.btn_resolve.disabled = False
            self.btn_quick.disabled = False
            self.status_label.value = "<span style='color:#e53935;'>❌ Could not connect to JDownloader 2 service.</span>"
            return

        self.status_label.value = f"<span style='color:#29b6f6;'>🔍 JDownloader 2 LinkGrabber: Crawling {len(urls)} link(s)...</span>"

        try:
            # Clear old linkgrabber list
            try:
                self.jd.device.linkgrabber.clear_list()
            except Exception:
                pass

            # Add links to Linkgrabber
            self.jd.device.linkgrabber.add_links([{
                "autostart": False,
                "links": "\n".join(urls),
                "packageName": "Colab_Queue",
                "destinationFolder": TEMP_DOWNLOAD_DIR,
                "overwritePackagizerRules": True
            }])

            # Poll is_collecting until crawling finishes
            start_wait = time.time()
            time.sleep(2)
            while time.time() - start_wait < 45:
                try:
                    if not self.jd.device.linkgrabber.is_collecting():
                        break
                except Exception:
                    pass
                time.sleep(1.5)

            # Query crawled links
            crawled = self.jd.device.linkgrabber.query_links([{
                "bytesTotal": True,
                "status": True,
                "enabled": True,
                "hosts": True,
                "url": True,
                "availability": True
            }])

            self.pending_items = crawled if isinstance(crawled, list) else []

        except Exception as e:
            self.status_label.value = f"<span style='color:#e53935;'>❌ LinkGrabber error: {str(e)[:100]}</span>"
            self.btn_resolve.disabled = False
            self.btn_quick.disabled = False
            return

        self.btn_resolve.disabled = False
        self.btn_quick.disabled = False

        if not self.pending_items:
            self.status_label.value = "<span style='color:#ffa000;'>⚠️ No downloadable items resolved by JDownloader 2. Check if links are valid.</span>"
            return

        self.update_queue_display()
        self.queue_container.layout.display = 'block'
        self.status_label.value = f"<span style='color:#66bb6a;'>✅ JDownloader 2 resolved {len(self.pending_items)} item(s). Click <b>Start Download</b> to begin.</span>"

    def _on_quick_download(self, b=None):
        """Bypass Queue Preview and start downloading immediately."""
        urls = self._extract_input_urls()
        if not urls:
            self.status_label.value = "<span style='color:#ffa000;'>⚠️ Please paste at least one link.</span>"
            return

        self.queue_container.layout.display = 'none'
        self.btn_resolve.disabled = True
        self.btn_quick.disabled = True
        self.status_label.value = "<span style='color:#29b6f6;'>⚡ Quick Download: Initializing JDownloader 2...</span>"

        if not self._ensure_service_ready():
            self.btn_resolve.disabled = False
            self.btn_quick.disabled = False
            self.status_label.value = "<span style='color:#e53935;'>❌ Could not connect to JDownloader 2 service.</span>"
            return

        try:
            # Clear old queue
            try:
                self.jd.device.linkgrabber.clear_list()
            except Exception:
                pass

            # Add with autostart
            self.status_label.value = "<span style='color:#29b6f6;'>⚡ JDownloader 2: Adding and starting links...</span>"
            self.jd.device.linkgrabber.add_links([{
                "autostart": True,
                "links": "\n".join(urls),
                "packageName": "Colab_Quick",
                "destinationFolder": TEMP_DOWNLOAD_DIR,
                "overwritePackagizerRules": True
            }])

            # Trigger download start
            time.sleep(2)
            try:
                self.jd.device.downloadcontroller.start_downloads()
            except Exception:
                pass

            # Monitor downloads and drive moves in background thread
            threading.Thread(target=self._monitor_and_transfer, daemon=True).start()

        except Exception as e:
            self.status_label.value = f"<span style='color:#e53935;'>❌ Quick Download error: {str(e)[:100]}</span>"
            self.btn_resolve.disabled = False
            self.btn_quick.disabled = False

    def _on_queue_start(self, b=None):
        """Move selected items from Linkgrabber to download list and start downloading."""
        selected_strings = list(self.queue_list.value)
        if not selected_strings:
            self.status_label.value = "<span style='color:#ffa000;'>⚠️ Please select at least one item from Queue.</span>"
            return

        selected_indices = [int(s.split('.')[0].strip()) - 1 for s in selected_strings]
        selected_tasks = [self.pending_items[i] for i in selected_indices if 0 <= i < len(self.pending_items)]

        link_ids = [item.get("uuid") for item in selected_tasks if item.get("uuid")]
        package_ids = list(set([item.get("packageUUID") for item in selected_tasks if item.get("packageUUID")]))

        self.queue_container.layout.display = 'none'
        self.btn_resolve.disabled = True
        self.btn_quick.disabled = True

        try:
            self.status_label.value = "<span style='color:#29b6f6;'>▶️ Moving items to Download List...</span>"
            self.jd.device.linkgrabber.move_to_downloadlist(link_ids, package_ids)
            self.jd.device.downloadcontroller.start_downloads()

            threading.Thread(target=self._monitor_and_transfer, daemon=True).start()
        except Exception as e:
            self.status_label.value = f"<span style='color:#e53935;'>❌ Start Download error: {str(e)[:100]}</span>"
            self.btn_resolve.disabled = False
            self.btn_quick.disabled = False

    def _monitor_and_transfer(self):
        """Periodically check download progress and transfer completed files to Google Drive."""
        self.is_downloading = True
        transferred_files = set()

        try:
            while self.is_downloading:
                time.sleep(2)
                try:
                    speed_bps = self.jd.device.downloadcontroller.get_speed_in_bytes() or 0
                    speed_str = f"{format_size(speed_bps)}/s"

                    links = self.jd.device.downloads.query_links([{
                        "bytesLoaded": True,
                        "bytesTotal": True,
                        "finished": True,
                        "speed": True,
                        "status": True,
                        "running": True
                    }])

                    if not links:
                        # Check if any files in temp folder are completed
                        self._scan_and_transfer_completed(transferred_files)
                        continue

                    total_bytes = sum(l.get("bytesTotal", 0) for l in links)
                    loaded_bytes = sum(l.get("bytesLoaded", 0) for l in links)
                    all_finished = all(l.get("finished", False) for l in links)

                    pct = (loaded_bytes / total_bytes * 100.0) if total_bytes > 0 else 0.0
                    self.progress_bar.value = max(0.0, min(100.0, pct))
                    self.progress_bar.description = f"DL: {int(pct)}% ({speed_str})"

                    active_names = [l.get("name", "") for l in links if l.get("running")]
                    status_text = f"⬇️ Downloading: <b>{', '.join(active_names[:2])}</b> — <code>{speed_str}</code>" if active_names else "Processing downloads..."
                    self.status_label.value = status_text

                    # Transfer finished files
                    for link in links:
                        fname = link.get("name")
                        if link.get("finished") and fname and fname not in transferred_files:
                            local_file = os.path.join(TEMP_DOWNLOAD_DIR, fname)
                            if os.path.exists(local_file):
                                self.status_label.value = f"<span style='color:#1e88e5;'>📤 Moving to Google Drive: {fname}...</span>"
                                ok, dest = transfer_to_google_drive(local_file, DRIVE_DOWNLOADS)
                                if ok:
                                    transferred_files.add(fname)
                                    print(f"✅ Transferred to Google Drive: {fname}")

                    if all_finished and len(transferred_files) >= len(links):
                        break

                except Exception as loop_e:
                    time.sleep(2)

        finally:
            self._scan_and_transfer_completed(transferred_files)
            self.is_downloading = False
            self.btn_resolve.disabled = False
            self.btn_quick.disabled = False
            self.progress_bar.value = 100.0
            self.progress_bar.description = "Done"
            summary = (
                f"<div style='margin-top:8px; padding:10px; background-color:#2e3b2e; border-radius:4px;'>"
                f"<b>🎉 JDownloader 2 Finished!</b> Successfully transferred <b>{len(transferred_files)}</b> file(s) "
                f"to Google Drive: <code>MyDrive/Downloads/</code>."
                f"</div>"
            )
            self.status_label.value = summary

    def _scan_and_transfer_completed(self, transferred_files: set):
        """Scan temp folder for any files that have finished downloading and are not .part files."""
        if not os.path.exists(TEMP_DOWNLOAD_DIR):
            return
        for f in os.listdir(TEMP_DOWNLOAD_DIR):
            if f.endswith(".part") or f.endswith(".tmp"):
                continue
            if f in transferred_files:
                continue
            fpath = os.path.join(TEMP_DOWNLOAD_DIR, f)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
                ok, dest = transfer_to_google_drive(fpath, DRIVE_DOWNLOADS)
                if ok:
                    transferred_files.add(f)
                    print(f"✅ Transferred to Google Drive: {f}")

    def _on_queue_up(self, b=None):
        selected = list(self.queue_list.value)
        if not selected:
            return
        indices = sorted([int(s.split('.')[0]) - 1 for s in selected])
        for idx in indices:
            if idx > 0 and idx - 1 not in indices:
                self.pending_items[idx], self.pending_items[idx - 1] = self.pending_items[idx - 1], self.pending_items[idx]
        self.update_queue_display()
        new_sel = [self.queue_list.options[max(0, i - 1)] for i in indices]
        self.queue_list.value = tuple(new_sel)

    def _on_queue_down(self, b=None):
        selected = list(self.queue_list.value)
        if not selected:
            return
        indices = sorted([int(s.split('.')[0]) - 1 for s in selected], reverse=True)
        for idx in indices:
            if idx < len(self.pending_items) - 1 and idx + 1 not in indices:
                self.pending_items[idx], self.pending_items[idx + 1] = self.pending_items[idx + 1], self.pending_items[idx]
        self.update_queue_display()
        new_sel = [self.queue_list.options[min(len(self.pending_items) - 1, i + 1)] for i in indices]
        self.queue_list.value = tuple(new_sel)

    def _on_queue_sort(self, b=None):
        self.pending_items.sort(key=lambda t: (t.get("name") or "").lower(), reverse=not self.sort_ascending)
        self.sort_ascending = not self.sort_ascending
        self.btn_sort.description = "Sort Z-A" if not self.sort_ascending else "Sort A-Z"
        self.update_queue_display()

    def _on_queue_select_all(self, b=None):
        self.queue_list.value = tuple(self.queue_list.options)

    def _on_queue_select_none(self, b=None):
        self.queue_list.value = ()

    def _on_queue_cancel(self, b=None):
        self.queue_container.layout.display = 'none'
        self.status_label.value = "<span style='color:#aaa;'>Queue preview closed.</span>"

    def _on_queue_remove(self, b=None):
        selected = list(self.queue_list.value)
        if not selected:
            return
        indices_to_remove = {int(s.split('.')[0]) - 1 for s in selected}
        removed_items = [self.pending_items[i] for i in indices_to_remove]
        self.pending_items = [t for i, t in enumerate(self.pending_items) if i not in indices_to_remove]

        # Remove from JD Linkgrabber if possible
        try:
            link_ids = [item.get("uuid") for item in removed_items if item.get("uuid")]
            package_ids = list(set([item.get("packageUUID") for item in removed_items if item.get("packageUUID")]))
            if link_ids or package_ids:
                self.jd.device.linkgrabber.remove_links(link_ids, package_ids)
        except Exception:
            pass

        self.update_queue_display()
        if not self.pending_items:
            self.queue_container.layout.display = 'none'
            self.status_label.value = "<span style='color:#aaa;'>All items removed from queue.</span>"

    def render(self):
        """Render the complete widget tree."""
        button_row = widgets.HBox([
            self.btn_resolve,
            self.btn_quick
        ], layout=widgets.Layout(margin='6px 0'))

        app_view = widgets.VBox([
            self.css_styles,
            self.cred_accordion,
            self.text_area,
            button_row,
            self.queue_container,
            self.progress_bar,
            self.status_label
        ], layout=widgets.Layout(width='100%', padding='10px'))

        display(app_view)


# --- MAIN RUNNER ---
def run_app():
    """Launch the Colab Downloader application."""
    app = ColabDownloaderApp()
    app.render()
    return app


if __name__ == "__main__":
    run_app()
