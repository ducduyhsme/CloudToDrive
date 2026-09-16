<div align="center">

# 🚀 CloudToDrive

<p align="center">
  <b>High-speed multi-source downloader powered by JDownloader 2 Headless with automated Google Drive sync</b>
</p>

[![English](https://img.shields.io/badge/Language-English-blue?style=for-the-badge)](README.md)
[![Tiếng Việt](https://img.shields.io/badge/Language-Ti%E1%BA%BFng_Vi%E1%BB%87t-lightgrey?style=for-the-badge)](docs/README_VI.md)

</div>

---

## 📖 Overview

**CloudToDrive** is an all-in-one universal multi-hoster download manager designed specifically for Google Colab and Jupyter environments. All functionality is consolidated into a single, self-contained notebook: [`Colab_Downloader.ipynb`](Colab_Downloader.ipynb).

Powered by the official **JDownloader 2 (JD2) Headless** engine and a clean `ipywidgets` GUI, it crawls, resolves, and streams links from over **1,000+ file hosting providers** directly into your **Google Drive `Downloads/`** folder without filling or relying on Google Colab's virtual disk.

---

## ✨ Key Features

- **All-in-One Standalone Notebook**: Everything (UI, JD2 daemon service, FUSE drive streaming, and crawler) is merged into [`Colab_Downloader.ipynb`](Colab_Downloader.ipynb). No extra script files required.
- **Bypass Colab 87GB Disk Limit (Direct-to-Drive Streaming)**: Streams downloaded files directly into your mounted Google Drive (`/content/drive/MyDrive/Downloads/`), completely bypassing Colab's ~80-90GB virtual disk. You can download files of 100GB, 200GB+ without running out of disk space.
- **Real-Time Colab Disk Space Display**: A dedicated live badge updates every 2 seconds during downloads, displaying Colab's available disk space (`💾 Colab Available Disk: XX GB`) to confirm that local disk space is 100% preserved.
- **Single-Instance Clean GUI**: Uses `clear_output(wait=True)` to prevent duplicate or stacked widgets, ensuring only one clean interface is shown.
- **Google Drive FUSE Compatibility**: Automatically disables file pre-allocation/sparse file creation and enforces single-connection (`chunks = 1`) sequential writes to prevent FUSE filesystem errors.
- **Dual Execution Modes (Cell 2)**:
  - `RUN_MODE = "interactive"`: Interactive GUI with Queue Preview, sorting, and management buttons.
  - `RUN_MODE = "direct"`: Headless console/HTML streaming engine for automated, zero-UI downloading.
- **Interactive GUI Features**:
  - **Multi-line Links Input**: Paste multiple URLs at once (one per line).
  - **"Sample Link" (Cyan)**: 1-click button to insert the sample Yandex Disk link (`https://disk.yandex.com/d/7OcBsRWfzoTozg`, ~9.55GB) for instant speed testing.
  - **"Resolve Links" (Green)**: Triggers JDownloader LinkGrabber to crawl URLs, inspect real filenames and exact sizes, and populates the **Queue Preview**.
  - **Queue Preview Management**: Full toolbar with `▲ Up`, `▼ Down`, `Sort A-Z`, `Select All`, `None`, `▶ Start Download`, `Cancel`, and `Remove`.
  - **"Quick Download" (Blue)**: 1-click fully automated resolving and streaming directly into Google Drive without opening the Queue Preview.
- **No Account Required**: Runs via JDownloader 2's **Local RemoteAPI (Port 3128)** on `127.0.0.1` using `myjdapi`.
- **Optional MyJDownloader Integration**: Supports connecting your `my.jdownloader.org` account for remote captcha solving via mobile app/web for captcha-protected hosters.

---

## ⚡ Quick Start

### Run Directly on Google Colab

1. Open [Google Colab](https://colab.research.google.com/).
2. Select **Upload** → Upload [`Colab_Downloader.ipynb`](Colab_Downloader.ipynb).
3. Click **Runtime** → **Run all** (or execute Cell 1 and Cell 2 sequentially).
4. Grant Google Drive access permissions when prompted.
5. In Cell 2, paste any URL(s) (or click **Sample Link**), then click **Quick Download** or **Resolve Links**!

---

## 📁 Repository Structure

- [`Colab_Downloader.ipynb`](Colab_Downloader.ipynb): Complete all-in-one Google Colab notebook (Cell 1: Environment Setup & Drive Mount, Cell 2: Download Engine & GUI).
- [`test_downloader.py`](test_downloader.py): Automated test suite verifying configuration, LinkGrabber logic, FUSE parameters, and direct streaming directly against `Colab_Downloader.ipynb`.
- [`README.md`](README.md): English documentation.
- [`docs/README_VI.md`](docs/README_VI.md): Vietnamese documentation.

---

## ⚙️ How It Works

1. **Bootstrap & Service Init**: The notebook verifies Java JRE, fetches official `JDownloader.jar`, writes `org.jdownloader.api.RemoteAPIConfig.json` (opening local port `3128`), and launches the headless daemon.
2. **Drive FUSE Optimization**: Generates `GeneralSettings.json` with `createpreallocatedlargefiles: false`, `maxchunksperserver: 1`, `maxchunksperdownload: 1`, and `defaultdownloadfolder: /content/drive/MyDrive/Downloads/`.
3. **LinkGrabber & Decryption**: When clicking **"Resolve Links"**, URLs are fed into JDownloader's LinkGrabber. The crawler contacts hosters and retrieves true filenames and exact file sizes.
4. **Direct Google Drive Streaming**: JDownloader 2 streams data sequentially directly into `/content/drive/MyDrive/Downloads/`. Colab local disk space is not consumed at all.

---

## 🧪 Testing

Run the automated test suite locally:
```bash
python test_downloader.py
```
All 11 unit tests verify filename sanitization, size formatting, configuration generation, LinkGrabber queues, direct streaming, real-time disk info widget, and Google Drive buffered transfers.

---

## 📝 License

This project is open-source and licensed under the [MIT License](LICENSE).
All download decrypters and hoster plugins are powered by the official [JDownloader 2](https://jdownloader.org/) engine.
