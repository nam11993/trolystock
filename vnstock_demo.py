"""
Demo lấy dữ liệu chứng khoán Việt Nam qua vnstock API
Cài đặt: pip install vnstock3
"""

from vnstock3 import Vnstock

# Khởi tạo đối tượng Vnstock
stock = Vnstock().stock(symbol='VNM', source='VCI')

# 1. Lấy thông tin công ty
print("=" * 50)
print("THÔNG TIN CÔNG TY VNM (Vinamilk)")
print("=" * 50)
company_info = stock.company.overview()
print(company_info)

# 2. Lấy dữ liệu giá lịch sử
print("\n" + "=" * 50)
print("DỮ LIỆU GIÁ LỊCH SỬ (30 ngày gần nhất)")
print("=" * 50)
price_data = stock.quote.history(start='2024-10-01', end='2024-11-05', interval='1D')
print(price_data.tail(10))  # In 10 ngày gần nhất

# 3. Lấy thông tin giao dịch realtime
print("\n" + "=" * 50)
print("THÔNG TIN REALTIME")
print("=" * 50)
realtime_data = stock.quote.intraday()
print(realtime_data)

# 4. Lấy báo cáo tài chính
print("\n" + "=" * 50)
print("BÁO CÁO TÀI CHÍNH - BẢNG CÂN ĐỐI KẾ TOÁN")
print("=" * 50)
balance_sheet = stock.finance.balance_sheet(period='quarter', lang='vi')
print(balance_sheet.head())

# 5. Lấy báo cáo kết quả kinh doanh
print("\n" + "=" * 50)
print("BÁO CÁO KẾT QUẢ KINH DOANH")
print("=" * 50)
income_statement = stock.finance.income_statement(period='quarter', lang='vi')
print(income_statement.head())

# 6. Lấy dữ liệu các chỉ số tài chính
print("\n" + "=" * 50)
print("CHỈ SỐ TÀI CHÍNH")
print("=" * 50)
ratio = stock.finance.ratio(period='quarter', lang='vi')
print(ratio.head())

# 7. Lấy danh sách tất cả mã chứng khoán
print("\n" + "=" * 50)
print("DANH SÁCH MÃ CHỨNG KHOÁN (10 mã đầu tiên)")
print("=" * 50)
from vnstock3 import Vnstock
all_stocks = Vnstock().stock(source='VCI').listing.all_symbols()
print(all_stocks.head(10))

print("\n✅ Hoàn thành! Dữ liệu đã được lấy thành công.")
