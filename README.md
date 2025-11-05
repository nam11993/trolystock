# 📈 Trợ lý Chứng khoán Việt Nam với AI

Web app tra cứu và phân tích chứng khoán Việt Nam tích hợp AI GPT để tư vấn đầu tư.

## ✨ Tính năng

### 1. Tra cứu dữ liệu chứng khoán
- ✅ Dữ liệu giá lịch sử (OHLCV) 1 năm
- ✅ Biểu đồ nến (Candlestick) tương tác
- ✅ Biểu đồ khối lượng giao dịch
- ✅ Thông tin công ty chi tiết
- ✅ Báo cáo tài chính (BCTC, BCKQKD)
- ✅ Các chỉ số tài chính (P/E, ROE, ROA...)

### 2. AI Tư vấn đầu tư 🤖
- ✅ Chat với AI về bất kỳ cổ phiếu nào
- ✅ Phân tích kỹ thuật và cơ bản
- ✅ Đánh giá rủi ro và cơ hội
- ✅ Tư vấn quản lý danh mục
- ✅ So sánh cổ phiếu
- ✅ Học kiến thức từ file tùy chỉnh

## 🚀 Cài đặt

### 1. Clone repository
```bash
git clone https://github.com/nam11993/trolystock.git
cd trolystock
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng
```bash
streamlit run app.py
```

### 4. Mở trình duyệt
- Truy cập: `http://localhost:8503`

## 🔑 Cấu hình OpenAI API

### Lấy API Key
1. Truy cập: https://platform.openai.com/api-keys
2. Đăng ký/Đăng nhập
3. Tạo API Key mới
4. Copy API Key

### Nhập vào ứng dụng
1. Mở sidebar
2. Mở rộng "🔑 Cấu hình OpenAI API"
3. Paste API Key
4. Hoàn tất!

## 📚 Dạy AI kiến thức mới

### Cách 1: Chỉnh sửa file `ai_knowledge.txt`
- File kiến thức cơ bản của AI
- Chỉnh sửa trực tiếp

### Cách 2: Thêm file vào thư mục `knowledge/` ⭐ MỚI
- Tạo file `.txt` hoặc `.md` trong thư mục `knowledge/`
- AI tự động đọc TẤT CẢ file
- Dễ dàng tổ chức theo chủ đề

**Ví dụ:**
```
knowledge/
  ├── nganh_ngan_hang.txt       # Kiến thức ngành ngân hàng
  ├── co_phieu_yeu_thich.md     # Phân tích cổ phiếu ưa thích
  ├── kinh_nghiem_dau_tu.txt    # Kinh nghiệm cá nhân
  └── chien_luoc_2024.md        # Chiến lược năm nay
```

📖 **Chi tiết**: Xem file `knowledge/README.md`

## 💬 Cách sử dụng AI

### Phân tích kỹ thuật
```
Phân tích kỹ thuật VNM
VNM có xu hướng tăng không?
```

### Phân tích cơ bản
```
Đánh giá định giá VCB
P/E của FPT có cao không?
```

### So sánh cổ phiếu
```
So sánh VCB và TCB
FPT và VNM, nên chọn cái nào?
```

### Tư vấn mua/bán
```
Nên mua HPG ở giá này không?
VNM giảm 20%, nên bán không?
```

## 📊 Nguồn dữ liệu

- **vnstock API**: Dữ liệu chứng khoán Việt Nam
- Nguồn mặc định: **TCBS**
- Hỗ trợ: VCI, MSN

## 🛠️ Công nghệ

- **Frontend**: Streamlit
- **Data**: vnstock, pandas
- **Visualization**: Plotly
- **AI**: OpenAI GPT-4o-mini
- **Language**: Python 3.12+

## 📁 Cấu trúc project

```
trolystock/
├── app.py                      # Main app
├── app_simple.py              # Simple version (no AI)
├── vnstock_demo.py            # Demo script
├── ai_knowledge.txt           # AI knowledge base
├── knowledge/                 # 📁 Thư mục kiến thức (thêm file vào đây!)
│   ├── README.md             # Hướng dẫn sử dụng thư mục
│   ├── co_phieu_pho_bien.txt # Ví dụ: Kiến thức cổ phiếu
│   └── TEMPLATE.txt          # Template tạo file mới
├── HUONG_DAN_SU_DUNG_AI.md   # AI usage guide
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## 🎯 Ví dụ sử dụng

### 1. Tra cứu cổ phiếu
1. Nhập mã: `VNM`
2. Nhấn Enter hoặc "Tra cứu"
3. Xem 4 tab: Giá, Công ty, Tài chính, Chỉ số, AI

### 2. Hỏi AI
1. Vào tab "🤖 AI Phân tích"
2. Nhập câu hỏi: "Phân tích VNM có nên mua không?"
3. AI phân tích và tư vấn

### 3. Câu hỏi gợi ý
- 📊 Phân tích kỹ thuật
- 💰 Đánh giá định giá
- ⚠️ Rủi ro đầu tư
- 🎯 Mục tiêu giá

## ⚠️ Lưu ý quan trọng

- ❌ **KHÔNG** đưa ra lời khuyên đầu tư chắc chắn
- ⚠️ AI chỉ cung cấp **tham khảo**, không phải lời khuyên tài chính
- 📊 Luôn tự nghiên cứu trước khi đầu tư
- 💰 Bạn chịu trách nhiệm với quyết định của mình

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón!
- Fork repository
- Tạo branch mới
- Commit changes
- Push và tạo Pull Request

## 📝 License

MIT License - Xem file LICENSE

## 📧 Liên hệ

- GitHub: [@nam11993](https://github.com/nam11993)
- Repository: [trolystock](https://github.com/nam11993/trolystock)

---

**⭐ Nếu thấy hữu ích, hãy star repo này!**
