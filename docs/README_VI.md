<div align="center">

# 🚀 CloudToDrive

<p align="center">
  <b>Trình tải file đa nguồn tốc độ cao tích hợp JDownloader 2 Headless & tự động đồng bộ Google Drive</b>
</p>

[![English](https://img.shields.io/badge/Language-English-lightgrey?style=for-the-badge)](../README.md)
[![Tiếng Việt](https://img.shields.io/badge/Language-Ti%E1%BA%BFng_Vi%E1%BB%87t-brightgreen?style=for-the-badge)](README_VI.md)

</div>

---

## 📖 Giới thiệu

**CloudToDrive** là ứng dụng tải file đa nguồn mạnh mẽ được thiết kế để chạy trên các môi trường đám mây (như Google Colab, Jupyter Server). Công cụ sử dụng engine chính thức **JDownloader 2 (JD2) Headless** kết hợp với giao diện trực quan `ipywidgets`, cho phép giải mã hàng loạt liên kết, xem trước và điều chỉnh hàng đợi tải, sau đó tự động chuyển toàn bộ file đã tải về vào thư mục `Downloads` trên **Google Drive**.

---

## ✨ Tính năng nổi bật

- **Hỗ trợ 1000+ dịch vụ lưu trữ (Hosters)**: Fshare, Rapidgator, 1fichier, Mediafire, Mega, Google Drive, DDownload, Turbobit, YouTube,... tận dụng kho plugin được cập nhật liên tục từ cộng đồng JDownloader.
- **Giao diện trực quan (GUI)**:
  - **Khung nhập Links**: Hỗ trợ dán nhiều liên kết cùng lúc (mỗi dòng một link).
  - **Nút "Resolve Links" (Xanh lá)**: Quét link qua JDownloader LinkGrabber, trích xuất tên file thật, dung lượng và hiển thị bảng **Queue Preview**.
  - **Bảng Queue Preview**: Hỗ trợ quản lý linh hoạt với các nút `▲ Up`, `▼ Down`, `Sort A-Z`, `Select All`, `None`, `▶ Start Download`, `Cancel`, `Remove`.
  - **Nút "Quick Download" (Xanh dương)**: Tự động giải mã và bắt đầu tải ngay lập tức, bỏ qua Queue Preview.
- **Không bắt buộc tạo tài khoản**: JDownloader 2 được cấu hình tự động mở cổng **Local RemoteAPI (3128)** và kết nối nội bộ qua thư viện `myjdapi`.
- **Hỗ trợ MyJDownloader (Tùy chọn)**: Hỗ trợ điền tài khoản `my.jdownloader.org` để giải captcha từ xa qua điện thoại/trình duyệt khi tải các hoster bảo mật cao.
- **Tự động chuyển Google Drive & Chống đầy ổ cứng**: Sau khi tải xong từng file về thư mục tạm, script tự động chuyển an toàn vào `/content/drive/MyDrive/Downloads/` và xóa ngay file tạm local.

---

## ⚡ Hướng dẫn sử dụng trên Google Colab

### Cách 1: Tải trực tiếp file `.ipynb` lên Colab (Khuyên dùng)
1. Truy cập [Google Colab](https://colab.research.google.com/).
2. Chọn **Upload** (Tải lên) → Chọn file [`Colab_Downloader.ipynb`](../Colab_Downloader.ipynb).
3. Bấm **Runtime** → **Run all** (hoặc chạy lần lượt Cell 1 và Cell 2).
4. Cấp quyền truy cập Google Drive khi Colab yêu cầu kết nối.
5. Giao diện tải sẽ xuất hiện trực tiếp ngay trong Cell 2.

---

### Cách 2: Chạy trực tiếp từ mã nguồn trong Notebook mới
Nếu bạn muốn tạo một Notebook mới trên Colab, chỉ cần tạo 2 cell:

#### Cell 1: Mount Google Drive & Cài đặt môi trường
```python
from google.colab import drive
drive.mount('/content/drive')

!apt-get update -qq && apt-get install -y -qq default-jre aria2 megatools
!pip install -q --upgrade myjdapi ipywidgets requests
```

#### Cell 2: Chạy mã nguồn Downloader
Sao chép toàn bộ nội dung từ file [`colab_downloader.py`](../colab_downloader.py) dán vào Cell 2 và bấm Run.

---

## 📁 Cấu trúc thư mục

- [`colab_downloader.py`](../colab_downloader.py): Mã nguồn Python chính chứa giao diện `ipywidgets`, tiến trình `JD2Service` và bộ chuyển Google Drive.
- [`Colab_Downloader.ipynb`](../Colab_Downloader.ipynb): Jupyter Notebook hoàn chỉnh chỉ cần bấm Run All.
- [`test_downloader.py`](../test_downloader.py): Bộ kiểm thử tự động (Unit Test).
- [`README.md`](../README.md): Tài liệu hướng dẫn bằng Tiếng Anh.
- [`docs/README_VI.md`](README_VI.md): Tài liệu hướng dẫn bằng Tiếng Việt.

---

## ⚙️ Cơ chế hoạt động của JDownloader 2
1. **Khởi tạo**: Tự động cài Java JRE, tải `JDownloader.jar` chính thức và mở cổng Local API `127.0.0.1:3128`.
2. **LinkGrabber / Crawler**: Gửi link vào JD2, crawler giải mã tên file thực và dung lượng từ máy chủ lưu trữ.
3. **Download Engine**: JD2 tải đa luồng (multi-chunk) về thư mục tạm `/content/temp_downloads/`.
4. **Google Drive Sync**: Giám sát tiến độ tải, chuyển ngay từng file hoàn thành vào `/content/drive/MyDrive/Downloads/` và xóa file tạm local.
