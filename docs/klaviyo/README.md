# Email Klaviyo cho VitalRay

10 email HTML trong thư mục `emails/` đã có sẵn biến cá nhân hóa của Klaviyo. Mỗi email đã có logo, ảnh, nút màu san hô, hàng cam kết, dòng miễn trừ trách nhiệm và link hủy đăng ký.

## Cách đưa 1 email vào Klaviyo

1. Vào **Klaviyo → Content → Templates → Create template → Code (HTML editor)**.
2. Dán toàn bộ nội dung file `.html` vào, đặt tên template giống tên file, rồi **Save**.
3. Khi tạo email trong flow, chọn **Use template** và chọn template vừa lưu.
4. Dán **Subject** và **Preview text** ở bảng bên dưới.
5. Bấm **Preview and test** với một hồ sơ (profile) đã có sự kiện thật để kiểm tra biến hiển thị đúng.

> **Trước khi bật flow:** vào **Settings → Organization** điền tên và địa chỉ doanh nghiệp. Footer email dùng `{{ organization.full_address }}`, và luật CAN-SPAM của Mỹ bắt buộc email marketing phải có địa chỉ gửi.

## Flow 1 · Welcome series (chào mừng)

- **Trigger:** khi khách được thêm vào list (*Added to list → Newsletter*). Shopify tự đồng bộ người đăng ký sang list này.
- **Bộ lọc:** *Placed Order zero times since starting this flow*. Nghĩa là khách mua rồi thì dừng gửi.

| # | Gửi sau | File | Subject | Preview text |
|---|---|---|---|---|
| 1 | Ngay lập tức | `01-welcome-1-hello.html` | Welcome to VitalRay ☀️ | Gentle red light care for hard-working hands — here's what to expect. |
| 2 | 2 ngày | `02-welcome-2-how-to.html` | How to use VitalRay in 3 simple steps | 15 minutes a day. No appointments, no setup. |
| 3 | 3 ngày | `03-welcome-3-guarantee.html` | Try it for 90 days — on us | Free tracked shipping, a 90-day money-back guarantee and 15% off two. |

## Flow 2 · Abandoned checkout (nhắc thanh toán dở)

- **Trigger:** *Started Checkout*.
- **Bộ lọc:** *Placed Order zero times since starting this flow*, và *Has not been in flow in the last 7 days*.

| # | Gửi sau | File | Subject | Preview text |
|---|---|---|---|---|
| 1 | 1 giờ | `04-checkout-1-reminder.html` | You left something behind | Your VitalRay is still in your cart. |
| 2 | 1 ngày | `05-checkout-2-questions.html` | Any questions before you order? | Quick answers about using VitalRay, shipping and returns. |
| 3 | 2 ngày | `06-checkout-3-bundle.html` | Last reminder: your cart + 15% off two | Treat both hands and save 15% automatically. |

Các email này dùng `event.extra.line_items` để hiện sản phẩm trong giỏ và `event.extra.checkout_url` cho nút quay lại thanh toán. Đây là dữ liệu chuẩn mà tích hợp Shopify gửi sang Klaviyo.

## Flow 3 · Browse abandonment (xem sản phẩm nhưng chưa mua)

- **Trigger:** *Viewed Product*.
- **Bộ lọc:** *Started Checkout zero times since starting this flow*, *Placed Order zero times since starting this flow*, và *Has not been in flow in the last 14 days*.

| # | Gửi sau | File | Subject | Preview text |
|---|---|---|---|---|
| 1 | 2 giờ | `07-browse-1.html` | Still thinking about {{ event.ProductName\|default:"VitalRay Wrist" }}? | Cordless red light care, 15 minutes a day. |

Flow này cần **Klaviyo onsite tracking** đang bật: **Online Store → Themes → Customize → App embeds → Klaviyo** phải được bật.

## Flow 4 · Post-purchase (sau khi mua)

- **Trigger:** *Placed Order*.

| # | Gửi sau | File | Subject | Preview text |
|---|---|---|---|---|
| 1 | 1 giờ | `08-post-1-thank-you.html` | Thank you! Here's what happens next | Your order is in. Here's the timeline. |
| 2 | 7 ngày | `09-post-2-getting-started.html` | Getting the most out of your VitalRay | A few tips for your first two weeks. |
| 3 | 28 ngày | `10-post-3-feedback.html` | How's it going with your VitalRay? | We'd love to hear from you. |

> **Judge.me** cũng tự gửi email xin đánh giá. Để khách không nhận 2 email xin đánh giá, bạn tắt email nhắc của Judge.me, hoặc giữ email số 3 ở trên như hiện tại: email này xin góp ý qua trả lời thư, không xin đánh giá.

## Form đăng ký (Signup form)

Gợi ý nội dung cho popup Klaviyo, hiện sau 8 giây hoặc khi khách sắp rời trang:

- **Tiêu đề:** Gentle care for hard-working hands
- **Mô tả:** Join the VitalRay list for routine tips, new products and members-only offers.
- **Nút:** Join the list
- **Sau khi đăng ký:** Welcome! Check your inbox.

Nếu muốn tặng mã giảm giá khi đăng ký (ví dụ 10%), hãy tạo mã trong Shopify trước, rồi thêm mã vào email Welcome số 1.

## Lưu ý nội dung

- **Không có tuyên bố chữa bệnh:** các email không viết "chữa", "giảm đau", "điều trị" để tránh vi phạm quy định của FTC (Mỹ) và ASA (Anh).
- **Giữ số liệu khớp với store:** 90 ngày hoàn tiền, ship 1–3 ngày, giao 7–15 ngày và giảm 15% khi mua 2 phải đúng với store. Đổi trên store thì đổi cả trong email.
- **Ảnh:** ảnh dùng trong email lấy từ **Content → Files** của Shopify. Nếu xóa file ở đó, ảnh trong email sẽ bị vỡ.
