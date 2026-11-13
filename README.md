# FB Ads Finder

Tìm sản phẩm dropship: tìm từ khóa trên Meta Ad Library → lấy danh sách ad video → lấy link store → tra từng store trên ShopHunter → xuất một trang báo cáo HTML tĩnh.

App chạy hoàn toàn trên máy bạn và điều khiển một cửa sổ Chrome đã đăng nhập sẵn Facebook và ShopHunter.

## Cài đặt (một lần)

1. Cài [Python 3.10+](https://www.python.org/downloads/). Khi cài, tick **Add python.exe to PATH**.
2. Mở PowerShell trong thư mục app:
   ```
   pip install -r requirements.txt
   copy config.example.json config.json
   ```
   Không cần chạy `playwright install`: app dùng Chrome có sẵn trên máy.
3. Bấm đúp **`start-chrome.bat`**. Một cửa sổ Chrome riêng mở ra, mở sẵn Ad Library và ShopHunter.
   **Lần đầu, đăng nhập Facebook và ShopHunter trong cửa sổ này.** Các lần sau Chrome tự nhớ đăng nhập (lưu ở thư mục `chrome-profile`).
4. Kiểm tra kết nối:
   ```
   python -m adsfinder check
   ```

### Vì sao không dùng thẳng Chrome đang mở?

Từ Chrome 136, Google không cho bật cổng điều khiển trên hồ sơ Chrome mặc định, để mã độc không lấy được phiên đăng nhập của bạn. Vì vậy app dùng một hồ sơ Chrome riêng (`chrome-profile`). Bạn chỉ phải đăng nhập lại một lần. Cổng 9222 chỉ nghe trên `127.0.0.1`, máy khác không vào được. Không dùng xong thì tắt cửa sổ Chrome đó.

## Chạy

Luôn mở Chrome bằng `start-chrome.bat` trước, rồi:

```
python -m adsfinder run "posture corrector" "pet hair remover"
```

Bỏ trống từ khóa thì app lấy `keywords` trong `config.json`. Bạn cũng có thể bấm đúp `run.bat`.

App sẽ:
1. Mở Ad Library (US, ad đang chạy, chỉ video), cuộn để lấy tối đa `max_ads_per_keyword` ad, đọc page, ngày bắt đầu chạy, số phiên bản, link "Shop now" và chụp ảnh từng ad.
2. Gộp ad theo store, kiểm tra store có phải Shopify không.
3. Với mỗi store Shopify (tối đa `max_stores_per_run`): mở `app.shophunter.io/shops/track`, nhập link vào ô **Shopify Store URL**, chờ đến khi thấy **Tracked** / **View shop**, mở **View shop**, đọc các box **Store Overview**, **Revenue Performance** và chụp ảnh **Revenue Trends**.
4. Xuất `reports/report-<ngày giờ>-run<số>.html` rồi tự mở.

File report là **một file duy nhất**, ảnh nằm sẵn bên trong. Có thể gửi qua Zalo hoặc email, hay mở trên điện thoại. Trong report có ô tìm kiếm, lọc theo từ khóa và sắp xếp theo doanh thu, số ad hoặc độ lâu của ad.

Tùy chọn hay dùng:

| Lệnh | Tác dụng |
|---|---|
| `--max-ads 20` | số ad tối đa mỗi từ khóa |
| `--max-stores 5` | số store tối đa tra ShopHunter |
| `--no-shophunter` | chỉ lấy ads, không tra ShopHunter |
| `--refresh` | tra lại ShopHunter dù store đã tra trong 24 giờ qua |
| `python -m adsfinder report` | xuất lại report lượt gần nhất |

Nhấn `Ctrl+C` để dừng giữa chừng: app vẫn xuất report với dữ liệu đã lấy được.

## Cấu hình (`config.json`)

| Khóa | Mặc định | Ý nghĩa |
|---|---|---|
| `country` | `US` | quốc gia trong Ad Library |
| `media_type` | `video` | `video`, `image` hoặc `all` |
| `max_ads_per_keyword` | 40 | |
| `min_days_running` | 0 | bỏ ad chạy ít hơn số ngày này |
| `max_stores_per_run` | 15 | giới hạn số store tra ShopHunter mỗi lượt |
| `shophunter_wait_seconds` | 180 | thời gian chờ ShopHunter phân tích |
| `shophunter_cache_hours` | 24 | store đã tra trong khoảng này thì dùng lại |
| `delay_seconds` | [2, 5] | nghỉ ngẫu nhiên giữa các thao tác |
| `shophunter_boxes` | 3 box ở trên | tên các box cần đọc |
| `shophunter_image_boxes` | `["Revenue Trends"]` | box nào chụp ảnh |
| `exclude_domains` | facebook, amazon,... | domain không coi là store |

## Khi có lỗi

Mỗi khi không đọc được trang, app lưu ảnh chụp và HTML của trang vào `data/debug/`. Facebook và ShopHunter hay đổi giao diện: gửi các file đó để sửa phần đọc trang. Phần này nằm trong `adsfinder/adlibrary.py` (`EXTRACT_JS`) và `adsfinder/shophunter.py` (`STATE_JS`, `BOXES_JS`).

Gặp yêu cầu đăng nhập hoặc captcha, app dừng lại và chờ bạn xử lý trong cửa sổ Chrome rồi nhấn Enter.

## Lưu ý

- Điều khoản của Meta và ShopHunter không cho phép thu thập dữ liệu tự động. App chạy chậm như người dùng thật và giới hạn số store mỗi lượt, nhưng tài khoản vẫn có thể bị giới hạn hoặc khóa. Đừng tăng tốc độ hay số lượng quá nhiều.
- Dữ liệu lưu trong `data/adsfinder.db` (SQLite), ảnh trong `data/shots` và `data/shophunter`.

## Kiểm thử

```
python -m unittest discover -s tests -t .
```

Bài test đầy đủ (`tests/test_e2e.py`) chạy toàn bộ quy trình trên các trang giả lập Ad Library và ShopHunter. Bài này cần biến `CHROME_BIN` trỏ tới file chrome; thiếu biến này thì bài được bỏ qua.
