# Hướng dẫn sử dụng vnstock API

## Cài đặt

```bash
pip install -r requirements.txt
```

hoặc

```bash
pip install vnstock3
```

## Chạy chương trình

```bash
python vnstock_demo.py
```

## Các tính năng chính

1. **Thông tin công ty**: Lấy thông tin tổng quan về công ty
2. **Dữ liệu giá lịch sử**: Lấy dữ liệu OHLCV (Open, High, Low, Close, Volume)
3. **Dữ liệu realtime**: Thông tin giao dịch trong ngày
4. **Báo cáo tài chính**: Bảng cân đối kế toán, báo cáo kết quả kinh doanh
5. **Chỉ số tài chính**: Các chỉ số như P/E, ROE, ROA, etc.
6. **Danh sách mã chứng khoán**: Tất cả mã cổ phiếu trên thị trường

## Thay đổi mã cổ phiếu

Để lấy dữ liệu của mã khác, thay đổi tham số `symbol`:

```python
stock = Vnstock().stock(symbol='VCB', source='VCI')  # VCB = Vietcombank
stock = Vnstock().stock(symbol='FPT', source='VCI')  # FPT Corporation
stock = Vnstock().stock(symbol='HPG', source='VCI')  # Hoa Phat Group
```

## Nguồn dữ liệu

- `VCI`: Vietcap Securities (mặc định)
- `TCBS`: Techcombank Securities
- `MSN`: MSN Finance

## Tài liệu tham khảo

- GitHub: https://github.com/thinh-vu/vnstock
- Documentation: https://docs.vnstock.site/
