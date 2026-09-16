# 🚀 Google Colab Multi-Link Downloader (Powered by JDownloader 2)

Ứng dụng tải file đa nguồn chuyên nghiệp chạy trực tiếp trên **Google Colab**, sử dụng engine chính thức **JDownloader 2 (JD2) Headless** kết hợp giao diện đồ họa trực quan xây dựng bằng `ipywidgets` theo đúng thiết kế bạn yêu cầu:
- **Hỗ trợ 1000+ hoster**: Fshare, Rapidgator, 1fichier, Mediafire, Mega, Google Drive, DDownload, Turbobit, YouTube,... tận dụng kho plugin được cập nhật liên tục của JDownloader.
- **Không bắt buộc tạo tài khoản**: JDownloader 2 được cấu hình tự động mở cổng **Local RemoteAPI (3128)** trên Colab và kết nối nội bộ qua `myjdapi`.
- **Hỗ trợ MyJDownloader (Tùy chọn)**: Cho phép cấu hình tài khoản `my.jdownloader.org` nếu bạn cần giải captcha từ xa cho các hoster bảo vệ cao.
- **Nút "Resolve Links"** (xanh lá): Quét link qua JDownloader LinkGrabber, trích xuất tên file thật, dung lượng và hiển thị bảng **Queue Preview**.
- **Nút "Quick Download"** (xanh dương): Tự động quét và tải ngay lập tức, bỏ qua Queue Preview.
- **Bảng Queue Preview**: Đầy đủ các nút chức năng: `▲ Up`, `▼ Down`, `Sort A-Z`, `Select All`, `None`, `▶ Start Download`, `Cancel`, `Remove`.
- **Tự động chuyển Google Drive**: File sau khi tải về server Colab sẽ được tự động chuyển vào thư mục `Downloads` trên **Google Drive** của bạn, đồng thời dọn dẹp file tạm trên Colab để chống tràn bộ nhớ.

---

## 📁 Cấu trúc thư mục

- [`colab_downloader.py`](colab_downloader.py): Mã nguồn Python tích hợp JDownloader 2 Headless (`JD2Service`), giao diện `ipywidgets` và bộ chuyển Google Drive an toàn.
- [`Colab_Downloader.ipynb`](Colab_Downloader.ipynb): File Jupyter Notebook đã được cấu hình sẵn 2 cell, chỉ cần tải lên Colab và bấm chạy.
- [`test_downloader.py`](test_downloader.py): Bộ kiểm thử tự động (Unit Test) kiểm tra cấu hình JD2, mock LinkGrabber, thao tác hàng đợi và chuyển file Drive.

---

## ⚡ Hướng dẫn sử dụng trên Google Colab

### Cách 1: Tải trực tiếp file `.ipynb` lên Colab (Khuyên dùng)
1. Truy cập [Google Colab](https://colab.research.google.com/).
2. Chọn **Upload** (Tải lên) → Chọn file [`Colab_Downloader.ipynb`](Colab_Downloader.ipynb).
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
Sao chép toàn bộ nội dung từ file [`colab_downloader.py`](colab_downloader.py) dán vào Cell 2 và bấm Run.

---

## ⚙️ Cơ chế hoạt động của JDownloader 2 trên Colab
1. **Khởi tạo**: Script tự động kiểm tra Java, tải file `JDownloader.jar` chính thức từ máy chủ JDownloader và cấu hình mở cổng Local API `127.0.0.1:3128`.
2. **LinkGrabber / Crawler**: Khi người dùng nhấn **"Resolve Links"**, script gửi liên kết tới JD2, chờ crawler xử lý và nhận lại danh sách tên file, dung lượng chính xác từ server chứa file.
3. **Download Engine**: JD2 tải đa luồng (multi-chunk) về thư mục tạm `/content/temp_downloads/`.
4. **Google Drive Sync**: Một tiến trình nền theo dõi tiến độ tải, ngay khi từng file hoàn tất, nó sẽ di chuyển ngay vào `/content/drive/MyDrive/Downloads/` và xóa file tạm trên ổ đĩa Colab.
