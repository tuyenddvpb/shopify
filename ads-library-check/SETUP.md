# Thiết lập máy local để Claude tự kiểm tra Meta Ad Library

Thư mục `ads-library-check/` có các file sau:

| File | Dành cho | Vai trò |
|---|---|---|
| `SETUP.md` | Bạn | Hướng dẫn cài đặt (file này) |
| `CLAUDE.md` | Claude | Bối cảnh dự án và luật làm việc. Claude tự đọc khi mở session trong thư mục này |
| `TASK.md` | Claude | Các bước kiểm tra Ad Library, từ khoá và đối thủ cần soi |
| `RESULTS_TEMPLATE.md` | Claude | Mẫu báo cáo. Claude chép mẫu này ra file kết quả rồi điền vào |
| `screenshots/` | Claude | Thư mục lưu ảnh chụp quảng cáo |

## 1. Chuẩn bị (làm một lần)

1. **Cài Claude Code.** Chọn một trong hai cách:
   - **Claude desktop app** (Mac hoặc Windows), có sẵn trình duyệt tích hợp. Đây là cách dễ nhất.
   - **Claude Code CLI**, kèm extension **Claude in Chrome** cài trên Google Chrome.
2. **Lấy code về máy:**

```bash
git clone https://github.com/tuyenddvpb/shopify.git
```

```bash
cd shopify && git checkout claude/loving-lovelace-i3iwji
```

   Nếu đã clone từ trước thì chỉ cần lấy bản mới nhất:

```bash
git fetch origin claude/loving-lovelace-i3iwji && git checkout claude/loving-lovelace-i3iwji && git pull
```

3. **Đăng nhập Facebook trong trình duyệt mà Claude sẽ dùng.** Từ giữa năm 2024, Ad Library hiện kết quả đầy đủ khi đã đăng nhập.
   - Nếu dùng desktop app: mở trình duyệt tích hợp, vào facebook.com, **bạn tự gõ mật khẩu**. Trình duyệt sẽ nhớ phiên đăng nhập cho các lần sau.
   - Nếu dùng extension: đăng nhập Facebook trên Chrome như bình thường.
   - **Không đưa mật khẩu cho Claude.** Claude được dặn trong `CLAUDE.md` là không được gõ mật khẩu.

## 2. Chạy session

1. Mở session Claude Code với thư mục làm việc là `shopify/ads-library-check`.
   - Desktop app: chọn folder này khi tạo session mới.
   - CLI: chạy lệnh bên dưới.

```bash
cd shopify/ads-library-check && claude
```

2. Dán câu lệnh sau vào session:

```
Đọc CLAUDE.md và TASK.md rồi thực hiện toàn bộ TASK.md trên trình duyệt. Mỗi khi xong 1 phần thì lưu kết quả vào file. Khi xong hết thì commit và push lên nhánh claude/loving-lovelace-i3iwji.
```

3. Thời gian chạy khoảng 1–2 giờ: 8 từ khoá, 8 đối thủ và khoảng 10 trang đích. Nếu trình duyệt hỏi cấp quyền cho facebook.com hoặc các trang đối thủ, bạn chọn **Allow**.

## 3. Sau khi chạy xong

- Claude sẽ push các file `ads-library-check/RESULTS-<ngày>.md` và ảnh trong `screenshots/` lên nhánh.
- Bạn quay lại session cloud này và nhắn **"đã có kết quả Ad Library"**. Mình sẽ đọc kết quả và làm tiếp bước 3 (mổ xẻ trang đích), bước 6 (góc sáng tạo) và thiết kế theme cho store A.

## Gặp sự cố

| Tình huống | Cách xử lý |
|---|---|
| Facebook bắt xác minh, hiện captcha hoặc checkpoint | Bạn tự xử lý trên trình duyệt, rồi nhắn Claude chạy tiếp. Claude được dặn là dừng lại và hỏi bạn, không tự vượt qua |
| Ad Library báo "You're temporarily blocked" | Dừng 30–60 phút rồi mới chạy tiếp. Claude được dặn là chạy chậm và không mở nhiều tab cùng lúc |
| Push bị lỗi do chưa có quyền GitHub trên máy | Đăng nhập bằng `gh auth login` hoặc dùng GitHub Desktop, rồi bảo Claude push lại |
