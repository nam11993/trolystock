"""
Web app tra cứu dữ liệu chứng khoán Việt Nam - Phiên bản đơn giản
Chạy: streamlit run app_simple.py
"""

import streamlit as st
import pandas as pd
import requests
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

# Chọn khoảng thời gian
days = st.sidebar.slider("Số ngày lịch sử", 30, 365, 90)

# Button để lấy dữ liệu
if st.sidebar.button("🔍 Tra cứu", type="primary"):
    try:
        with st.spinner(f"Đang tải dữ liệu {symbol}..."):
            
            # API từ SSI
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Gọi API
            url = "https://apipubaws.tcbs.com.vn/stock-insight/v2/stock/bars-long-term"
            params = {
                "ticker": symbol,
                "type": "stock",
                "resolution": "D",
                "from": int(start_date.timestamp()),
                "to": int(end_date.timestamp())
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    # Chuyển đổi dữ liệu
                    df = pd.DataFrame(data['data'])
                    df['tradingDate'] = pd.to_datetime(df['tradingDate'])
                    df = df.sort_values('tradingDate')
                    df.set_index('tradingDate', inplace=True)
                    
                    # Đổi tên cột cho dễ hiểu
                    df = df.rename(columns={
                        'open': 'Mở cửa',
                        'high': 'Cao nhất',
                        'low': 'Thấp nhất',
                        'close': 'Đóng cửa',
                        'volume': 'Khối lượng'
                    })
                    
                    # Hiển thị metrics
                    st.subheader(f"Thông tin {symbol}")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    with col1:
                        change = latest['Đóng cửa'] - prev['Đóng cửa']
                        st.metric("Giá đóng cửa", f"{latest['Đóng cửa']:,.1f}", f"{change:,.1f}")
                    with col2:
                        st.metric("Cao nhất", f"{latest['Cao nhất']:,.1f}")
                    with col3:
                        st.metric("Thấp nhất", f"{latest['Thấp nhất']:,.1f}")
                    with col4:
                        st.metric("Khối lượng", f"{latest['Khối lượng']:,.0f}")
                    with col5:
                        change_pct = ((latest['Đóng cửa'] - prev['Đóng cửa']) / prev['Đóng cửa']) * 100
                        st.metric("Thay đổi %", f"{change_pct:.2f}%")
                    
                    st.markdown("---")
                    
                    # Tab layout
                    tab1, tab2 = st.tabs(["📊 Biểu đồ", "📋 Dữ liệu"])
                    
                    with tab1:
                        # Biểu đồ nến
                        fig = go.Figure(data=[go.Candlestick(
                            x=df.index,
                            open=df['Mở cửa'],
                            high=df['Cao nhất'],
                            low=df['Thấp nhất'],
                            close=df['Đóng cửa'],
                            name=symbol
                        )])
                        
                        fig.update_layout(
                            title=f"Biểu đồ nến {symbol}",
                            yaxis_title="Giá (VND)",
                            xaxis_title="Ngày",
                            height=500,
                            template="plotly_white",
                            xaxis_rangeslider_visible=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Biểu đồ khối lượng
                        fig_volume = go.Figure()
                        colors = ['red' if df.iloc[i]['Đóng cửa'] < df.iloc[i]['Mở cửa'] else 'green' 
                                 for i in range(len(df))]
                        
                        fig_volume.add_trace(go.Bar(
                            x=df.index,
                            y=df['Khối lượng'],
                            name='Khối lượng',
                            marker_color=colors
                        ))
                        
                        fig_volume.update_layout(
                            title="Khối lượng giao dịch",
                            yaxis_title="Khối lượng",
                            xaxis_title="Ngày",
                            height=300,
                            template="plotly_white"
                        )
                        
                        st.plotly_chart(fig_volume, use_container_width=True)
                    
                    with tab2:
                        # Bảng dữ liệu chi tiết
                        st.subheader("Dữ liệu chi tiết")
                        st.dataframe(
                            df[['Mở cửa', 'Cao nhất', 'Thấp nhất', 'Đóng cửa', 'Khối lượng']].tail(50),
                            use_container_width=True
                        )
                        
                        # Thống kê
                        st.subheader("Thống kê")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Giá**")
                            st.write(f"- Trung bình: {df['Đóng cửa'].mean():,.1f}")
                            st.write(f"- Cao nhất (trong kỳ): {df['Cao nhất'].max():,.1f}")
                            st.write(f"- Thấp nhất (trong kỳ): {df['Thấp nhất'].min():,.1f}")
                        
                        with col2:
                            st.write("**Khối lượng**")
                            st.write(f"- TB mỗi ngày: {df['Khối lượng'].mean():,.0f}")
                            st.write(f"- Cao nhất: {df['Khối lượng'].max():,.0f}")
                            st.write(f"- Thấp nhất: {df['Khối lượng'].min():,.0f}")
                    
                    st.success(f"✅ Đã tải xong dữ liệu cho {symbol}!")
                else:
                    st.error(f"❌ Không tìm thấy dữ liệu cho mã {symbol}")
                    st.info("💡 Vui lòng kiểm tra lại mã chứng khoán")
            else:
                st.error(f"❌ Lỗi API: {response.status_code}")
                st.info("💡 Vui lòng thử lại sau")
                
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: Không thể kết nối tới server")
        st.info("💡 Vui lòng kiểm tra kết nối internet và thử lại")
    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")
        st.info("💡 Vui lòng thử lại hoặc kiểm tra lại mã chứng khoán")

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
    "MSN": "Masan Group",
    "TCB": "Techcombank",
    "VPB": "VPBank",
    "POW": "PV Power",
    "SSI": "SSI Securities"
}

for code, name in popular_stocks.items():
    if st.sidebar.button(f"{code} - {name}", key=code, use_container_width=True):
        st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.info("💡 Dữ liệu từ TCBS API")
st.sidebar.caption("Cập nhật: Realtime")
