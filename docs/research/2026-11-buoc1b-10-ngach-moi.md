# Bước 1b: 10 ngách mới, quét Reddit (06/11/2026)

> Đã loại trừ 4 ngách của đợt trước: tay lạnh, chó già, mãn kinh, viêm cân gan chân.
> Trạng thái: **đã xong cả 2 luồng** (Reddit và Google Trends đợt 2, cập nhật 07/11/2026). Bảng xếp hạng ở mục 2 là bản chốt.

## 1. Cách quét

| Giai đoạn | Nội dung | Số lượng |
|---|---|---|
| A: Khám phá | 5 cụm tín hiệu × 24 subreddit (xem bên dưới) | 120 trang, **1.094 bài** |
| B: Đọc bình luận | 65 thread dạng "món đồ đáng tiền nhất" hoặc "đã thử hết không ăn thua" | **1.792 bình luận** |
| C: Kiểm chứng | 32 lượt tìm có chủ đích trong subreddit chuyên sâu của từng ngách ứng viên | 31 trang, **621 bài** |

- 5 cụm tín hiệu ở giai đoạn A: `"wish there was"`, `"game changer"`, `"best purchase"`, `"nothing works"`, `"finally found"`.
- Nguồn dữ liệu là RSS công khai của Reddit, giới hạn khoảng 1 request mỗi phút. Tổng thời gian quét khoảng 4 giờ.
- Thang điểm giữ nguyên như báo cáo bước 1, mỗi tiêu chí chấm 1–5:
  - Nỗi đau 25%
  - Quy mô 20%
  - Hợp dropship 20%
  - Cạnh tranh 15% (điểm cao nghĩa là ít cạnh tranh)
  - Thời điểm 10%
  - Rủi ro chính sách và hoàn hàng 10% (điểm cao nghĩa là ít rủi ro)

## 2. Bảng xếp hạng chốt (Reddit kết hợp Trends)

"Quy mô" là lượng tìm kiếm tại Mỹ trong 5 năm, so với mốc `heated gloves` = 1.0. "YoY" so sánh 52 tuần gần nhất với 52 tuần trước đó.

| Hạng | Ngách | Sản phẩm mồi | Trends: quy mô · YoY · mùa | Điểm |
|---|---|---|---|---|
| 1 | Ngủ cạnh người ngáy hoặc ngủ nông | Băng đô tai nghe ngủ, mặt nạ ngủ che sáng | sleep mask ×2.7 · +73% · đỉnh T12; sleep headphones ×0.67 · +210% | **4.25** |
| 2 | Gối bầu cho giường nhỏ | Gối nêm hoặc chữ J gọn, lật người được | ×1.70 · +30% · đỉnh T12 và T4–5 | **4.00** |
| 3 | Đau tay và cổ tay ban đêm | Nẹp đêm không velcro, găng nén | wrist brace ×1.65 · +32%; compression gloves ×0.45 · +56% | **3.95** |
| 4 | Tắm cho người đau mãn tính và cha mẹ già | Vòi sen cầm tay có công tắc ngắt nước, cọ cán dài | shower chair ×1.98 · +85%; handheld shower head ×0.92 · +88% · đỉnh T4–6 | **3.85** |
| 5 | Đau cổ, đã thử đủ loại gối *(mới, thay ngách migraine)* | Gối cổ cervical có thể chỉnh độ cao | ×0.82 · **+152%** · đỉnh T4–6 | **3.85** |
| 6 | Remote lật trang Kindle | Remote kèm giá kẹp, bán bundle quà | ×0.09 · +23% · 8 tuần gần nhất +90% · đỉnh T12–2 | **3.60** |
| 7 | Phục hồi sau sinh | Kit quà: bình rửa peri, túi chườm lạnh, gối donut | peri bottle ×0.29 · +22% | **3.50** |
| 8 | Đài nước cho mèo dễ vệ sinh | Đài inox không cần lõi lọc | ×1.02 · +84% · đỉnh T5–6 | **3.50** |
| 9 | Lông thú rụng | Lược deshedding, con lăn lông | dog shedding brush ×0.09 · +6% (đi ngang) | **3.50** |
| 10 | Người ngủ nóng | Gối hoặc chăn làm mát | cooling sheets ×0.79 · +65% · đỉnh T6–7 | **3.35** |

**Trends làm thay đổi thứ hạng ở những điểm sau:**
- **Băng dán miệng −24%/năm:** đỉnh đã qua từ 12/2024. Không dùng làm sản phẩm chính cho ngách ngáy. Chuyển sang tai nghe ngủ (+210%) và mặt nạ ngủ (+73%, đỉnh tháng 12).
- **Đẩy lên:**
  - Ghế tắm và vòi sen cầm tay (+85–88%).
  - Gối bầu (đỉnh tháng 12, đúng mùa hiện tại).
  - Gối cổ (+152%). Reddit cũng có nhiều tín hiệu cho ngách này, ví dụ *"tried Purple, Coop, latex… nothing works"* và các thread hỏi gối trên r/backpain, r/migraine.
- **Loại ngách đau nửa đầu:** "migraine ice cap" gần như bằng 0 (−50%). FL-41 tăng +200% nhưng quy mô chỉ ×0.05. Chuyển xuống dự bị.
- **Lông thú tụt hạng:** từ khoá đi ngang, có lẽ người dùng tìm bằng từ khác ("deshedding tool", "pet hair roller"). Đợt 1 chỉ bắt được 1 đợt viral.
- **Lưu ý dữ liệu:** rất nhiều từ khoá có tuần cao nhất trùng nhau vào 05–12/04/2026. Có thể đây là bất thường của Google, không phải nhu cầu thật. Vì vậy YoY của những từ đỉnh tháng 4–6 có thể bị phóng đại một phần.

**Dự bị:**
- Máy TENS cho đau lưng (×3.0, +16%)
- Kính FL-41
- Hộp hâm cơm 12V cho tài xế (quá nhỏ)
- Ghế quỳ làm vườn (×0.10, +108%, đỉnh tháng 5)
- Laminator (×1.46, nhưng khách là giáo viên mua mùa tựu trường, không hợp dropship)

## 3. Chi tiết từng ngách

### 1. Bạn đời ngáy (54 bài)
- **Chân dung khách hàng:** nữ 30–55 tuổi, ngủ nông, phải nằm chung giường với người ngáy. Người mua là **người bị làm phiền**, không phải người ngáy.
- **Trích dẫn:**
  - *"SAHM, husband says he wants a divorce if we don't sleep in the same bed, but his snoring is the reason we sleep separately."*
  - *"My partner snores and I need to find a way to ignore the sound - ear plugs don't work!"*
  - *"I Used to Think Sleep Earbuds Were a Total Waste of Money. Now I Have No Idea How I Ever Slept…"*
- **Góc cải tiến:** nút bịt tai thường không ăn thua và earbuds gây đau khi nằm nghiêng. Có thể bán băng đô tai nghe phát tiếng ồn che lấp, kèm băng dán miệng cho người ngáy. Thông điệp: "cứu giấc ngủ của 2 người".
- **Trends đợt 1:** snoring ×7.6 so với mốc găng sưởi, +17%/năm, cao điểm tháng 12–2.
- **Rủi ro:** không được hứa chữa ngáy hay ngưng thở khi ngủ (claim y tế).

### 2. Lông thú rụng (86 bài)
- **Chân dung khách hàng:** chủ chó lông dày như husky, golden, chó chăn cừu Đức.
- **Trích dẫn:**
  - *"Dog sheds so much I can't keep up with the cleaning, what actually works?"*
  - *"At My Breaking Point With Pet Hair and Dirty Floors."*
  - *"What tools have you tried that ACTUALLY get rid of pet hair on clothes?"*
- **Góc cải tiến:** combo "từ gốc đến ngọn": lược deshedding cho chó, con lăn tái sử dụng cho sofa và quần áo, bóng giặt gom lông. Giá rẻ, nhẹ, không có rủi ro y tế.
- **Trends đợt 1:** pet hair remover +96%, nhưng mức tăng đến từ 1 đợt bùng viral, nên phải theo dõi thêm.

### 3. Đau tay và cổ tay ban đêm (CarpalTunnel và Fibromyalgia)
- **Chân dung khách hàng:** nữ 35–60 tuổi bị hội chứng ống cổ tay hoặc đau cơ xơ hoá, làm văn phòng hoặc đan móc.
- **Trích dẫn:**
  - *"Velcro-less night brace recommendation?"*
  - *"I am having excruciating pain in my hands at night that is disrupting my sleep."*
  - *"Painful Stiffness in wrist and fingers - has anyone experience with heated gloves?"*
- **Góc cải tiến:** nẹp ban đêm không dùng velcro vì velcro mắc vào chăn và cào da.
- **Lợi thế đặc biệt:** cùng tệp khách với **găng sưởi**. Người đau tay vì lạnh cũng hỏi về găng sưởi, nên có thể upsell chéo giữa 2 ngách.

### 4. Remote lật trang Kindle (27 bài, đang lên)
- **Chân dung khách hàng:** nữ 20–40 tuổi mê đọc sách (BookTok), đọc trên giường hoặc vừa đọc vừa đi máy chạy bộ.
- **Trích dẫn:**
  - *"I used a $10 Amazon gift card and got one of those remote page turner dealios… my oh my what a game changer."*
  - *"Kindle + Walking pad + Page turner = heaven."*
  - *"Chinese page turner maker releases Kindle-support firmware."* Nguồn hàng từ Trung Quốc đã sẵn.
- **Góc cải tiến:** bundle remote, giá kẹp Kindle cố định trên giường hoặc máy chạy bộ, đèn đọc sách, rồi làm quà tặng dịp lễ. Rất hợp làm video TikTok kiểu "nằm đọc khỏi thò tay ra khỏi chăn".
- **Rủi ro:** thấp. Giá trị đơn hàng (AOV) thấp nên phải bán theo bundle.

### 5. Phục hồi sau sinh
- **Chân dung khách hàng:** mẹ sắp sinh (36 tuần trở lên) hoặc người mua quà baby shower.
- **Trích dẫn:**
  - *"The biggest game changers were an upside down peri bottle, reusable ice packs, and a donut pillow."*
  - *"I am using the dermaplast spray, witch hazel pads and foam, peri bottle… and nothing is helping."*
  - *"What would you have loved in a postpartum care package?"*
- **Góc cải tiến:** gói kit đóng hộp đẹp để làm quà. Người mua là bạn bè hoặc mẹ của sản phụ.
- **Rủi ro:** hàng vệ sinh cá nhân không đổi trả được. Tránh đưa vào kit các thứ thoa hay xịt có thành phần y tế.

### 6. Gối bầu cho giường nhỏ (26 bài)
- **Trích dẫn:**
  - *"PSA: buy the stupid pregnancy pillow before you think you 'really need' it."*
  - *"Best pregnancy pillow for hip pain when you don't have much bed space?"*
  - *"Pregnancy Pillow That Allows Flipping?"*
- **Góc cải tiến:** gối chữ U to chiếm hết giường và khó trở mình. Bán loại nêm hoặc chữ J gọn, lật người được, vỏ mát.
- **Upsell sau sinh:** chuyển thành gối cho con bú.

### 7. Đài nước cho mèo dễ vệ sinh (34 bài)
- **Trích dẫn:**
  - *"Any water fountains that don't get full of gunk?"*
  - *"Pet fountain - disinterest and pink slime."*
  - *"Mats under water fountain are trapping water/ruining hardwood!"*
- **Góc cải tiến:** đài inox không cần lõi lọc, rửa được bằng máy rửa bát, kèm thảm silicon chống tràn. Thị trường đông đối thủ (Catit, Petlibro), nên phải thắng bằng điểm "chất nhờn hồng (biofilm), lõi lọc, khó rửa".

### 8. Người ngủ nóng (53 bài)
- **Trích dẫn:**
  - *"Tried cooling sheets and a fan and still wake up soaked. What actually works?"*
  - *"Are cooling sheets mostly marketing…?"*
- **Nhận xét:** khách đã hoài nghi với các sản phẩm "cooling" nên chuyển đổi khó. Thời điểm cũng chưa hợp vì đang vào đông, mùa bán là tháng 4–8. Để dành cho mùa hè.

### 9. Đau nửa đầu do ánh sáng (r/migraine)
- **Trích dẫn:**
  - *"Rough lighting in office - got my Fl-41 glasses on."*
  - *"Blue light glasses made my aura disappear immediately."*
  - *"Husband bought me a mini freezer to have next to my side of the bed…"* (giữ túi chườm lạnh luôn sẵn).
- **Góc cải tiến:** kính FL-41 thời trang để đeo ở văn phòng, kèm mũ chườm lạnh.
- **Rủi ro:** claim y tế, quảng cáo Meta dễ bị từ chối. Chỉ nói "giảm chói" và "dễ chịu hơn".

### 10. Tắm cho người đau mãn tính và cha mẹ già (47 bài)
- **Trích dẫn:**
  - *"i bought a shower chair, but still find myself avoiding showers due to discomfort."*
  - *"What are good shower tools for people with low mobility in their arms?"*
  - *"Time for Mom to get a bath chair."*
- **Góc cải tiến:** ghế tắm thì nhiều người đã có. Khoảng trống là **bộ dụng cụ quanh ghế**: vòi sen cầm tay có công tắc ngắt nước, cọ lưng cán dài, kệ treo tầm với.
- **Rủi ro:** ghế cồng kềnh, phí vận chuyển cao. Nên bán phụ kiện nhỏ, không bán ghế.

## 4. Bản đồ bang (Trends đợt 2)

| Ngách | Top bang |
|---|---|
| Găng sưởi (mốc) | VT, AK, WI, ME, ND |
| Gối bầu | HI, FL, TX, CA, LA |
| Bình rửa peri | LA, FL, TX, TN, DC |
| Ghế tắm | FL, TX, SC, HI, AZ (vùng có nhiều người về hưu) |
| Vòi sen cầm tay | FL, DE, NJ, HI, NV |
| Nẹp cổ tay | HI, VA, CA, WA, NV |
| Gối cổ | WY, DC, CA, TX, NV |
| Mặt nạ ngủ | DC, HI, CA, TX, GA |
| Ga mát | MS, LA, SC, FL, TX (miền Nam nóng ẩm) |
| Đài nước cho mèo | WV, OR, RI, PA, NV |
| Remote Kindle | DC, WV, OK, KY, VA |

Với từ khoá nhỏ (dưới ×0.1), bản đồ bang có nhiều nhiễu. Chỉ nên dùng bản đồ của những từ khoá có quy mô từ ×0.5 trở lên.

## 5. Khuyến nghị

1. **Bán ngay mùa này (tháng 11–1):**
   - **Ngách 1 (tai nghe ngủ và mặt nạ ngủ):** đỉnh tháng 12, mua làm quà được. Không đụng tới claim chữa ngáy.
   - **Ngách 2 (gối bầu):** đỉnh tháng 12.
   - **Ngách 6 (remote Kindle):** quà Giáng sinh, đỉnh tháng 12–2.
2. **Ghép với găng sưởi:** ngách 3 (nẹp cổ tay, găng nén). Cùng tệp khách đau tay, chạy upsell chéo.
3. **Chuẩn bị từ bây giờ cho mùa xuân (bán từ tháng 3):**
   - Ngách 4 (vòi sen và dụng cụ tắm): target FL, TX, AZ, giống ngách chó già.
   - Ngách 5 (gối cổ).
   - Ngách 8 (đài nước cho mèo).
4. **Từ khoá cho bước 2 (Meta Ad Library):**
   - `sleep headphones`, `sleep mask`, `snoring partner`
   - `pregnancy pillow`
   - `night wrist brace`, `compression gloves`
   - `handheld shower head`, `shower chair`
   - `cervical pillow`
   - `kindle page turner`
   - `postpartum kit`
   - `cat fountain stainless`
