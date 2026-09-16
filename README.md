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

**CloudToDrive** is a universal multi-hoster download manager designed for cloud runtime environments (such as Google Colab, Jupyter servers, and remote VPS). Powered by the official **JDownloader 2 (JD2) Headless** daemon and an interactive `ipywidgets` GUI, it crawls, resolves, and batches links from over **1,000+ file hosting providers**, and automatically transfers downloaded files directly to your **Google Drive `Downloads/`** folder.

---

## ✨ Key Features

- **1,000+ File Hosting Providers Supported**: Rapidgator, 1fichier, MediaFire, Mega, Google Drive, DDownload, Turbobit, Fshare, YouTube, Pixeldrain, Gofile, and more — leveraging continuously updated official JDownloader 2 plugins.
- **Interactive Web / Notebook GUI**:
  - **Multi-line Links Input**: Paste multiple URLs at once (one per line).
  - **"Resolve Links" (Green)**: Triggers JDownloader LinkGrabber to crawl URLs, inspect real filenames, file sizes, and populates the **Queue Preview**.
  - **Queue Preview Management**: Full toolbar with `▲ Up`, `▼ Down`, `Sort A-Z`, `Select All`, `None`, `▶ Start Download`, `Cancel`, and `Remove`.
  - **"Quick Download" (Blue)**: One-click fully automated resolving and downloading directly without opening the Queue Preview.
- **No Account Required**: Runs via JDownloader 2's **Local RemoteAPI (Port 3128)** on `127.0.0.1` using `myjdapi`.
- **Optional MyJDownloader Integration**: Supports connecting your `my.jdownloader.org` account for remote captcha solving via mobile app/web for captcha-protected hosters.
- **Automated Google Drive Sync & Disk Guard**: Automatically transfers completed files into `/content/drive/MyDrive/Downloads/` and cleans up temporary local files immediately to prevent running out of disk space.

---

## ⚡ Quick Start

### Method 1: Upload and Run `.ipynb` (Recommended)
1. Open [Google Colab](https://colab.research.google.com/).
2. Select **Upload** → Upload [`Colab_Downloader.ipynb`](Colab_Downloader.ipynb).
3. Click **Runtime** → **Run all** (or execute Cell 1 and Cell 2 sequentially).
4. Grant Google Drive access permissions when prompted.
5. The interactive GUI will display directly in Cell 2.

---

### Method 2: Manual Setup in a New Notebook
Create two cells in your notebook:

#### Cell 1: Mount Google Drive & Install Environment
```python
from google.colab import drive
drive.mount('/content/drive')

!apt-get update -qq && apt-get install -y -qq default-jre aria2 megatools
!pip install -q --upgrade myjdapi ipywidgets requests
```

#### Cell 2: Run the Downloader Application
Copy and paste the entire code from [`colab_downloader.py`](colab_downloader.py) into Cell 2 and run it.

---

## 📁 Repository Structure

```
├── Colab_Downloader.ipynb   # Ready-to-run Jupyter / Colab Notebook
├── colab_downloader.py      # Core Python application with GUI & JD2 service
├── test_downloader.py       # Automated unit tests for JD2 config, queue & transfers
├── docs/
│   └── README_VI.md         # Vietnamese documentation
├── README.md                # English documentation (this file)
└── .gitignore               # Git ignore configuration
```

---

## ⚙️ How It Works

1. **Bootstrap & Service Init**: The script verifies Java JRE, fetches official `JDownloader.jar`, writes `org.jdownloader.api.RemoteAPIConfig.json` (opening local port `3128`), and launches the headless daemon.
2. **LinkGrabber & Decryption**: When clicking **"Resolve Links"**, URLs are fed into JDownloader's LinkGrabber. The crawler contacts hosters and retrieves true filenames and exact file sizes.
3. **Multi-Chunk Download**: JDownloader 2 downloads files using multi-connection chunking to local buffer directory `/content/temp_downloads/`.
4. **Google Drive Sync**: A background worker monitors active transfers. As each file finishes, it streams the file into `/content/drive/MyDrive/Downloads/` and deletes the local temporary copy to keep storage clean.

---

## 🧪 Testing

Run the automated test suite locally:
```bash
python test_downloader.py
```
All unit tests verify filename sanitization, size formatting, configuration generation, mock LinkGrabber queues, and Google Drive buffered transfers.

---

## 📝 License

This project is open-source and licensed under the [MIT License](LICENSE).
All download decrypters and hoster plugins are powered by the official [JDownloader 2](https://jdownloader.org/) engine.
