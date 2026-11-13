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
3. Với mỗi store Shopify (tối đa `max_stores_per_run`):
   - Mở `app.shophunter.io/shops/track`, nhập link vào ô **Shopify Store URL**, bấm **Track Store**.
   - Trong **Recent Activity**, tìm đúng dòng có domain của store. Dòng đó hiện **Tracked** màu xanh thì bấm **View Shop** của chính dòng đó. Dòng hiện **Not a Shopify Store** thì thử lại với domain `xxx.myshopify.com` của store (nếu tìm được); vẫn bị từ chối thì bỏ qua store.
   - Nếu chờ mãi không có nút View Shop, mở `app.shophunter.io/collections/shops`, cuộn tìm khung có domain của store và bấm vào tên store.
   - Trên trang shop: đọc các box **Store Overview**, **Revenue Performance** và chụp ảnh **Revenue Trends**. Nếu trang shop không hiện domain của store, report ghi chú "có thể đã mở nhầm store".
4. Xuất `reports/report-<ngày giờ>-run<số>.html` rồi tự mở.

Khi report có dưới 40 store, nó là **một file duy nhất** với ảnh nằm sẵn bên trong. Có thể gửi qua Zalo hoặc email, hay mở trên điện thoại. Trong report có ô tìm kiếm, lọc theo từ khóa và sắp xếp theo doanh thu, số ad hoặc độ lâu của ad.

## Chạy số lượng lớn

**1. File từ khóa.** Tạo `keywords.txt`, mỗi dòng một từ khóa. Dòng trống và dòng bắt đầu bằng `#` được bỏ qua.

```
# Sức khỏe
posture corrector
neck massager
knee brace
```

```
python -m adsfinder run --file keywords.txt --max-stores 100
```

Hoặc đặt `"keywords_file": "keywords.txt"` trong `config.json`, sau đó chỉ cần `python -m adsfinder run`.

**2. Chạy tiếp khi bị dừng.** Mất điện, đóng cửa sổ, `Ctrl+C`, hay một từ khóa bị lỗi, thì chạy:

```
python -m adsfinder run --resume
```

App tiếp tục lượt gần nhất: bỏ qua các từ khóa đã quét xong, quét lại từ khóa bị lỗi, rồi kiểm tra store và tra ShopHunter cho toàn bộ ads của lượt đó. Store đã tra trong 24 giờ thì không tra lại. Muốn thêm từ khóa vào lượt đang dở: `python -m adsfinder run --resume "từ khóa mới"` hoặc `--resume --file them.txt`.

**3. Report cho nhiều store.**
- Report chia trang: 25, 50 hoặc 100 store mỗi trang.
- Từ 40 store trở lên, ảnh được lưu ra thư mục `reports\assets\` cạnh file HTML thay vì nhúng vào file, để file nhẹ và mở nhanh. Khi gửi cho người khác, gửi kèm cả thư mục `assets`, hoặc xuất bản nhúng ảnh bằng `python -m adsfinder report --embed`.
- Gộp nhiều lượt chạy vào một report:
  ```
  python -m adsfinder report --days 7
  ```

Tùy chọn hay dùng:

| Lệnh | Tác dụng |
|---|---|
| `--max-ads 20` | số ad tối đa mỗi từ khóa |
| `--max-stores 5` | số store tối đa tra ShopHunter |
| `--no-shophunter` | chỉ lấy ads, không tra ShopHunter |
| `--refresh` | tra lại ShopHunter dù store đã tra trong 24 giờ qua |
| `--file keywords.txt` | đọc từ khóa từ file |
| `--resume` | chạy tiếp lượt gần nhất |
| `python -m adsfinder report` | xuất lại report lượt gần nhất (`--run 5` cho lượt số 5) |
| `python -m adsfinder report --days 7` | gộp các lượt trong 7 ngày qua |
| `report --embed` / `--no-embed` | nhúng ảnh vào HTML / lưu ảnh ra `reports\assets\` |

Nhấn `Ctrl+C` để dừng giữa chừng: app vẫn xuất report với dữ liệu đã lấy được.

## Cấu hình (`config.json`)

| Khóa | Mặc định | Ý nghĩa |
|---|---|---|
| `country` | `US` | quốc gia trong Ad Library |
| `media_type` | `video` | `video`, `image` hoặc `all` |
| `max_ads_per_keyword` | 40 | |
| `min_days_running` | 0 | bỏ ad chạy ít hơn số ngày này |
| `max_stores_per_run` | 15 | giới hạn số store tra ShopHunter mỗi lượt |
| `shophunter_wait_seconds` | 180 | thời gian chờ dòng Recent Activity hiện Tracked |
| `shophunter_cache_hours` | 24 | store đã tra trong khoảng này thì dùng lại |
| `delay_seconds` | [2, 5] | nghỉ ngẫu nhiên giữa các thao tác |
| `shophunter_boxes` | 3 box ở trên | tên các box cần đọc |
| `shophunter_image_boxes` | `["Revenue Trends"]` | box nào chụp ảnh |
| `store_check_workers` | 8 | số store kiểm tra Shopify cùng lúc |
| `store_check_timeout` | 20 | giây tối đa cho mỗi store; quá thì ghi "chưa rõ" và đi tiếp |
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
