# VitalRay Shopify Theme

Theme cho store **VitalRay**, dựng trên [Dawn 16.0.0](https://github.com/Shopify/dawn), với bảng màu **Sage & Coral**.

## Cài theme lên store

1. Vào **Shopify Admin → Online Store → Themes**.
2. Bấm **Add theme → Connect from GitHub**, rồi chọn repo `tuyenddvpb/shopify` và nhánh chứa theme.
3. Theme sẽ hiện ở danh sách. Bấm **Customize** để xem trước, rồi **Publish** khi đã ưng.

Mỗi lần có code mới được push lên nhánh này, Shopify tự cập nhật theme.

## Hệ thống thiết kế

| Vai trò | Màu |
|---|---|
| Nền chính (scheme-1) | `#F5F3EE` |
| Nền sage (scheme-2) | `#E4EBE3` |
| Chữ / nền tối (scheme-3) | `#1F2A27` |
| Sage đậm (scheme-4) | `#4A6656` |
| Nút (san hô đậm, tương phản 4.6:1 với chữ trắng) | `#C4502F` |
| San hô trang trí | `#E2674A` |

**Font:** Playfair Display (tiêu đề) và DM Sans (nội dung).

CSS riêng của VitalRay nằm trong `assets/vitalray.css`.

## Các section tùy chỉnh (`sections/vr-*.liquid`)

Mọi chữ trong các section này đều sửa được trong Theme Editor.

| Section | Dùng cho |
|---|---|
| `vr-hero` | Hero trang chủ: tiêu đề, mô tả, nút, các huy hiệu |
| `vr-trust-bar` | Thanh cam kết (bảo hành, ship, bảo mật…) |
| `vr-category-cards` | Thẻ danh mục sản phẩm |
| `vr-stats` | Các con số nổi bật |
| `vr-features` | Lợi ích hoặc các bước sử dụng (bật "step numbers") |
| `vr-timeline` | Lộ trình sử dụng theo tuần |
| `vr-comparison` | Bảng so sánh ✓ / ✗ |
| `vr-testimonials` | Đánh giá khách hàng (tự ẩn khi chưa có đánh giá) |
| `vr-faq` | FAQ dạng accordion, có sẵn dữ liệu cấu trúc FAQ cho SEO |
| `vr-guarantee` | Khối bảo hành hoàn tiền |
| `vr-sticky-atc` | Thanh "Add to cart" dính ở cuối trang sản phẩm |

## Lưu ý nội dung

- **Đánh giá và số liệu:** chỉ đăng đánh giá thật và số liệu có căn cứ. Quảng cáo về sức khỏe bị Facebook, Google và FTC kiểm soát chặt.
- **Bảo hành:** số ngày bảo hành trên theme (mặc định 90) phải khớp với Refund Policy của store.
- **Thông số kỹ thuật:** 660/850nm, 3 mức cường độ, 15 phút, USB-C… phải khớp với sản phẩm thật. Hãy kiểm tra lại với nhà cung cấp.
