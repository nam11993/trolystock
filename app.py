"""
Web app tra cứu dữ liệu chứng khoán Việt Nam
Chạy: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from vnstock import Vnstock
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Cấu hình trang
st.set_page_config(
    page_title="Tra cứu chứng khoán VN",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Tra cứu Chứng khoán Việt Nam")
st.markdown("---")

# Sidebar
st.sidebar.header("⚙️ Cài đặt")

# Input mã chứng khoán
symbol = st.sidebar.text_input("Nhập mã chứng khoán", value="VNM").upper()

# Chọn nguồn dữ liệu
source = st.sidebar.selectbox("Nguồn dữ liệu", ["VCI", "TCBS", "MSN"])

# Chọn khoảng thời gian
days = st.sidebar.slider("Số ngày lịch sử", 30, 365, 90)
end_date = datetime.now()
start_date = end_date - timedelta(days=days)

# Button để lấy dữ liệu
if st.sidebar.button("🔍 Tra cứu", type="primary"):
    try:
        with st.spinner(f"Đang tải dữ liệu {symbol}..."):
            # Khởi tạo
            stock = Vnstock().stock(symbol=symbol, source=source)
            
            # Tab layout
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Giá & Biểu đồ", "🏢 Thông tin công ty", "💰 Tài chính", "📋 Chỉ số"])
            
            # TAB 1: Giá và Biểu đồ
            with tab1:
                st.subheader(f"Dữ liệu giá {symbol}")
                
                # Lấy dữ liệu giá
                try:
                    price_data = stock.quote.history(
                        start=start_date.strftime('%Y-%m-%d'),
                        end=end_date.strftime('%Y-%m-%d'),
                        interval='1D'
                    )
                except Exception as e:
                    st.error(f"Lỗi khi lấy dữ liệu giá: {str(e)}")
                    st.info(f"💡 Thử đổi nguồn dữ liệu sang TCBS hoặc MSN")
                    price_data = pd.DataFrame()
                
                if not price_data.empty and len(price_data) > 0:
                    # Hiển thị thông tin realtime
                    col1, col2, col3, col4, col5 = st.columns(5)
                    latest = price_data.iloc[-1]
                    
                    with col1:
                        st.metric("Giá đóng cửa", f"{latest['close']:,.0f}", 
                                 f"{latest['close'] - latest['open']:,.0f}")
                    with col2:
                        st.metric("Cao nhất", f"{latest['high']:,.0f}")
                    with col3:
                        st.metric("Thấp nhất", f"{latest['low']:,.0f}")
                    with col4:
                        st.metric("Khối lượng", f"{latest['volume']:,.0f}")
                    with col5:
                        change_pct = ((latest['close'] - latest['open']) / latest['open']) * 100
                        st.metric("Thay đổi %", f"{change_pct:.2f}%")
                    
                    st.markdown("---")
                    
                    # Biểu đồ nến (Candlestick)
                    fig = go.Figure(data=[go.Candlestick(
                        x=price_data.index,
                        open=price_data['open'],
                        high=price_data['high'],
                        low=price_data['low'],
                        close=price_data['close'],
                        name=symbol
                    )])
                    
                    fig.update_layout(
                        title=f"Biểu đồ nến {symbol}",
                        yaxis_title="Giá (VND)",
                        xaxis_title="Ngày",
                        height=500,
                        template="plotly_white"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Biểu đồ khối lượng
                    fig_volume = go.Figure()
                    fig_volume.add_trace(go.Bar(
                        x=price_data.index,
                        y=price_data['volume'],
                        name='Khối lượng',
                        marker_color='lightblue'
                    ))
                    
                    fig_volume.update_layout(
                        title="Khối lượng giao dịch",
                        yaxis_title="Khối lượng",
                        xaxis_title="Ngày",
                        height=300,
                        template="plotly_white"
                    )
                    
                    st.plotly_chart(fig_volume, use_container_width=True)
                    
                    # Bảng dữ liệu chi tiết
                    st.subheader("Dữ liệu chi tiết")
                    st.dataframe(price_data.tail(20), use_container_width=True)
                else:
                    st.warning("Không có dữ liệu giá!")
            
            # TAB 2: Thông tin công ty
            with tab2:
                st.subheader(f"Thông tin công ty {symbol}")
                try:
                    company_info = stock.company.overview()
                    if not company_info.empty:
                        st.dataframe(company_info, use_container_width=True)
                    else:
                        st.info("Không có thông tin công ty")
                except Exception as e:
                    st.error(f"Lỗi khi lấy thông tin công ty: {str(e)}")
            
            # TAB 3: Báo cáo tài chính
            with tab3:
                st.subheader("Báo cáo tài chính")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Bảng cân đối kế toán**")
                    try:
                        balance_sheet = stock.finance.balance_sheet(period='quarter', lang='vi')
                        st.dataframe(balance_sheet.head(10), use_container_width=True)
                    except Exception as e:
                        st.error(f"Lỗi: {str(e)}")
                
                with col2:
                    st.markdown("**Báo cáo kết quả kinh doanh**")
                    try:
                        income = stock.finance.income_statement(period='quarter', lang='vi')
                        st.dataframe(income.head(10), use_container_width=True)
                    except Exception as e:
                        st.error(f"Lỗi: {str(e)}")
            
            # TAB 4: Chỉ số tài chính
            with tab4:
                st.subheader("Chỉ số tài chính")
                try:
                    ratio = stock.finance.ratio(period='quarter', lang='vi')
                    if not ratio.empty:
                        st.dataframe(ratio.head(10), use_container_width=True)
                    else:
                        st.info("Không có dữ liệu chỉ số tài chính")
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")
        
        st.success(f"✅ Đã tải xong dữ liệu cho {symbol}!")
        
    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")
        st.info("Vui lòng kiểm tra lại mã chứng khoán hoặc kết nối internet.")

# Sidebar - Danh sách mã phổ biến
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Mã phổ biến")
popular_stocks = {
    "VNM": "Vinamilk",
    "VCB": "Vietcombank",
    "FPT": "FPT Corp",
    "HPG": "Hòa Phát",
    "VHM": "Vinhomes",
    "VIC": "Vingroup",
    "MWG": "Mobile World",
    "VRE": "Vincom Retail",
    "GAS": "PV Gas",
    "MSN": "Masan Group"
}

for code, name in popular_stocks.items():
    st.sidebar.markdown(f"**{code}** - {name}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("💡 Dữ liệu từ vnstock API")
