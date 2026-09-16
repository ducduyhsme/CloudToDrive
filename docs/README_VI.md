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

**CloudToDrive** là giải pháp tải file đa nguồn tất-cả-trong-một (All-in-One) được thiết kế tối ưu hóa cho môi trường Google Colab và Jupyter. Toàn bộ logic ứng dụng, daemon JDownloader 2, giao diện điều khiển và engine truyền dữ liệu FUSE đều được tích hợp gói gọn trong một tệp duy nhất: [`Colab_Downloader.ipynb`](../Colab_Downloader.ipynb).

Sử dụng engine chính thức **JDownloader 2 (JD2) Headless** kết hợp với giao diện `ipywidgets`, công cụ cho phép giải mã liên kết từ hơn **1.000+ nhà lưu trữ (file hosts)** và stream dữ liệu trực tiếp vào thư mục `Downloads/` trên **Google Drive** mà không làm đầy đĩa ảo của Colab.

---

## ✨ Tính năng nổi bật

- **Tệp Notebook Độc Lập Tất-Cả-Trong-Một**: Toàn bộ mã nguồn đã được gộp hoàn chỉnh vào [`Colab_Downloader.ipynb`](../Colab_Downloader.ipynb). Không cần cài đặt tệp Python phụ trợ nào bên ngoài.
- **Bypass giới hạn 87GB của Colab (Direct-to-Drive Streaming)**: Stream trực tiếp dữ liệu tải vào thư mục Google Drive đã mount (`/content/drive/MyDrive/Downloads/`), **bỏ qua hoàn toàn phân vùng đĩa ảo Colab** (`/content/`). Cho phép tải file dung lượng cực lớn (100GB, 200GB+) mà không lo bị tràn đĩa.
- **Hiển thị dung lượng đĩa Colab thời gian thực**: Widget badge hiển thị dung lượng đĩa Colab còn trống (`💾 Dung lượng Colab khả dụng: XX GB`) cập nhật liên tục mỗi 2 giây khi đang tải, chứng minh đĩa ảo Colab được bảo toàn 100%.
- **Giao diện chuẩn hóa đơn nhất (Single-Instance GUI)**: Tự động xóa các output cũ (`clear_output(wait=True)`) khi khởi chạy hoặc tải lại cell, đảm bảo luôn chỉ hiển thị đúng 1 widget điều khiển duy nhất, không bị xếp chồng hay nhân đôi.
- **Tương thích hoàn hảo hệ thống tệp FUSE Google Drive**: Tự động vô hiệu hóa Pre-allocation (Sparse Files) và áp dụng chế độ Single Connection (`chunks = 1`) để ghi tuần tự, loại bỏ triệt để lỗi phân vùng FUSE.
- **Hai chế độ chạy linh hoạt (Cell 2)**:
  - `RUN_MODE = "interactive"`: Giao diện đồ họa đầy đủ với bảng Queue Preview, điều chỉnh thứ tự và nút thao tác nhanh.
  - `RUN_MODE = "direct"`: Chạy stream trực tiếp hiển thị tiến trình dạng console/HTML mà không cần tải thư viện widget bên ngoài.
- **Các tiện ích điều khiển trên GUI**:
  - **Khung nhập Links**: Hỗ trợ dán nhiều liên kết cùng lúc (mỗi dòng một link).
  - **Nút "Sample Link" (Xanh nhạt)**: Bấm 1 chạm để điền ngay link mẫu Yandex Disk (`https://disk.yandex.com/d/7OcBsRWfzoTozg`, ~9.55GB) để kiểm tra tốc độ.
  - **Nút "Resolve Links" (Xanh lá)**: Quét link qua JDownloader LinkGrabber, trích xuất tên file thật, dung lượng và hiển thị bảng **Queue Preview**.
  - **Bảng Queue Preview**: Hỗ trợ quản lý hàng đợi với các nút `▲ Up`, `▼ Down`, `Sort A-Z`, `Select All`, `None`, `▶ Start Download`, `Cancel`, `Remove`.
  - **Nút "Quick Download" (Xanh dương)**: Tự động giải mã và stream thẳng vào Google Drive ngay lập tức.
- **Không bắt buộc tài khoản**: Chạy qua cổng nội bộ **Local RemoteAPI (Port 3128)** trên `127.0.0.1` qua `myjdapi`.
- **Hỗ trợ MyJDownloader (Tùy chọn)**: Điền tài khoản `my.jdownloader.org` để giải captcha từ xa trên điện thoại/web nếu tải từ hoster bảo mật cao.

---

## ⚡ Hướng dẫn sử dụng trên Google Colab

### Chạy trực tiếp Notebook

1. Truy cập [Google Colab](https://colab.research.google.com/).
2. Chọn **Upload** (Tải lên) → Chọn file [`Colab_Downloader.ipynb`](../Colab_Downloader.ipynb).
3. Bấm **Runtime** → **Run all** (hoặc chạy lần lượt Cell 1 và Cell 2).
4. Cấp quyền truy cập Google Drive khi Colab yêu cầu kết nối.
5. Tại Cell 2, dán link tải của bạn (hoặc bấm **Sample Link**), sau đó chọn **Quick Download** hoặc **Resolve Links**!

---

## 📁 Cấu trúc thư mục

- [`Colab_Downloader.ipynb`](../Colab_Downloader.ipynb): Tệp Notebook Colab hoàn chỉnh tích hợp sẵn (Cell 1: Cài môi trường & Mount Drive, Cell 2: Toàn bộ engine tải & GUI).
- [`test_downloader.py`](../test_downloader.py): Bộ kiểm thử tự động (Unit Test) kiểm tra cấu hình, FUSE Drive, LinkGrabber và stream trực tiếp từ `Colab_Downloader.ipynb`.
- [`README.md`](../README.md): Tài liệu hướng dẫn Tiếng Anh.
- [`docs/README_VI.md`](README_VI.md): Tài liệu hướng dẫn Tiếng Việt.

---

## ⚙️ Cơ chế hoạt động

1. **Khởi tạo dịch vụ**: Notebook kiểm tra Java JRE, tải `JDownloader.jar` chính thức, tạo cấu hình `RemoteAPIConfig.json` (cổng `3128`) và khởi động tiến trình daemon nền.
2. **Cấu hình tối ưu Google Drive**: Ghi tệp `GeneralSettings.json` với `createpreallocatedlargefiles: false`, `maxchunksperserver: 1`, `maxchunksperdownload: 1` và `defaultdownloadfolder: /content/drive/MyDrive/Downloads/`.
3. **LinkGrabber & Decryption**: Phân giải link qua LinkGrabber để lấy tên tệp thật và kích thước chính xác từ máy chủ.
4. **Direct FUSE Streaming**: Stream tuần tự dữ liệu trực tiếp vào `/content/drive/MyDrive/Downloads/`, giữ nguyên 100% dung lượng đĩa cục bộ Colab không bị tiêu hao.

---

## 🧪 Kiểm thử tự động

Chạy bộ kiểm thử trên môi trường nội bộ:
```bash
python test_downloader.py
```
Toàn bộ 11 bài kiểm thử tự động xác minh: tính toàn vẹn cấu hình FUSE, crawler LinkGrabber, cơ chế stream trực tiếp, hiển thị dung lượng đĩa thời gian thực và đồng bộ tệp an toàn.

---

## 📝 Giấy phép

Dự án được phân phối mã nguồn mở theo [Giấy phép MIT](../LICENSE).
Toàn bộ plugin giải mã và crawler liên kết được cung cấp bởi engine chính thức [JDownloader 2](https://jdownloader.org/).
