"""
Web app tra cứu dữ liệu chứng khoán Việt Nam
Chạy: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from vnstock import Vnstock
from datetime import datetime, timedelta
import plotly.graph_objects as go
from openai import OpenAI
import json
import os

# Cấu hình trang
st.set_page_config(
    page_title="Tra cứu chứng khoán VN",
    page_icon="📈",
    layout="wide"
)

# File lưu cấu hình
CONFIG_FILE = "config.json"

def load_config():
    """Đọc cấu hình từ file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    """Lưu cấu hình vào file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return True
    except:
        return False

def load_ptkt_examples():
    """Đọc các file mẫu khuyến nghị Chim Cút"""
    examples = []
    example_files = [
        "knowledge/maukhuyennghichimcut1.txt",
        "knowledge/maukhuyennghichimcut2.txt",
        "knowledge/maukhuyennghichimcut3.txt"
    ]
    
    for file_path in example_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    examples.append(content)
        except Exception as e:
            st.warning(f"Không thể đọc file {file_path}: {str(e)}")
    
    return "\n\n---\n\n".join(examples) if examples else ""

# Title
st.title("📈 Trợ lý AI stock")
st.markdown("---")

# Load cấu hình đã lưu
saved_config = load_config()

# Khởi tạo session state cho lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "openai_api_key" not in st.session_state:
    # Tự động load API key từ file cấu hình
    st.session_state.openai_api_key = saved_config.get("openai_api_key", "")
if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = None
if "price_data" not in st.session_state:
    st.session_state.price_data = None
if "scan_mode" not in st.session_state:
    st.session_state.scan_mode = False
if "scan_symbols" not in st.session_state:
    st.session_state.scan_symbols = []

# Sidebar
st.sidebar.header("⚙️ Cài đặt")

# API Key input
with st.sidebar.expander("🔑 Cấu hình OpenAI API", expanded=not st.session_state.openai_api_key):
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.openai_api_key,
        help="Nhập API key từ https://platform.openai.com/api-keys",
        placeholder="sk-proj-..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Lưu & Kiểm tra", use_container_width=True):
            if api_key and api_key.startswith("sk-"):
                try:
                    # Test kết nối
                    test_client = OpenAI(api_key=api_key)
                    test_response = test_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    st.session_state.openai_api_key = api_key
                    # Lưu vào file
                    if save_config({"openai_api_key": api_key}):
                        st.success("✅ API key đã lưu vĩnh viễn!")
                    else:
                        st.warning("⚠️ Kết nối OK nhưng không lưu được vào file")
                except Exception as e:
                    st.error(f"❌ Lỗi kết nối: {str(e)}")
                    st.info("💡 Kiểm tra lại API key hoặc kết nối internet")
            else:
                st.error("❌ API key không hợp lệ! (phải bắt đầu với sk-)")
    
    with col2:
        if st.button("🗑️ Xóa API Key", use_container_width=True):
            st.session_state.openai_api_key = ""
            save_config({"openai_api_key": ""})
            st.success("✅ Đã xóa API key")
            st.rerun()
    
    if st.session_state.openai_api_key:
        st.info("🟢 API Key đã được lưu và tự động kết nối")

st.sidebar.markdown("---")

# Thêm nút xem bảng giá thị trường
st.sidebar.subheader("📊 Bảng giá thị trường")

if st.sidebar.button("📈 Xem bảng giá theo ngành", use_container_width=True, type="secondary"):
    st.session_state.market_view_mode = True
    st.rerun()

st.sidebar.markdown("---")

# Thêm tab tìm cổ phiếu tốt
st.sidebar.subheader("🔍 Tìm cổ phiếu đáng mua")

# Danh sách 20 mã phổ biến để test
popular_symbols = ["VNM", "VCB", "VHM", "VIC", "HPG", "MSN", "FPT", "MWG", "VRE", "PLX", 
                   "GAS", "TCB", "BID", "CTG", "VPB", "SSI", "HDB", "POW", "SAB", "MBB"]

if st.sidebar.button("🎯 Tìm cổ phiếu tốt (20 mã)", use_container_width=True, type="primary"):
    if not st.session_state.openai_api_key:
        st.sidebar.error("⚠️ Cần có OpenAI API Key để sử dụng tính năng này!")
    else:
        st.session_state.scan_mode = True
        st.session_state.scan_symbols = popular_symbols
        st.rerun()

st.sidebar.markdown("---")

# Form để có thể nhấn Enter
with st.sidebar.form(key="search_form"):
    # Input mã chứng khoán
    symbol = st.text_input("Nhập mã chứng khoán", value="VNM").upper()

    # Chọn nguồn dữ liệu (mặc định TCBS)
    source = st.selectbox("Nguồn dữ liệu", ["TCBS", "VCI", "MSN"])

    # Mặc định 1000 ngày lịch sử (~3-4 năm)
    days = 1000
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Button để lấy dữ liệu
    submit_button = st.form_submit_button("🔍 Tra cứu", type="primary", use_container_width=True)

# ==================== BẢNG GIÁ THỊ TRƯỜNG ====================
if hasattr(st.session_state, 'market_view_mode') and st.session_state.market_view_mode:
    st.header("📊 Bảng giá thị trường - 50 mã phổ biến")
    st.info("📈 Dữ liệu cập nhật theo thời gian thực từ TCBS")
    
    # Định nghĩa các nhóm ngành với 50 mã phổ biến nhất
    industry_groups = {
        "VN30": ["VCB", "VHM", "VIC", "HPG", "MSN", "VNM", "FPT", "MWG", "VRE", "PLX",
                 "GAS", "TCB", "BID", "CTG", "VPB", "MBB", "POW", "SAB", "SSI", "HDB"],
        "NGÂN HÀNG": ["ACB", "STB", "TPB", "VIB", "LPB"],
        "CHỨNG KHOÁN": ["VND", "HCM", "VCI", "FTS", "BSI"],
        "BẤT ĐỘNG SẢN": ["NVL", "DXG", "KDH", "PDR", "HDG"],
        "CÔNG NGHIỆP": ["HSG", "NKG", "DGC", "DCM", "GVR"],
        "NĂNG LƯỢNG": ["PVS", "PVD", "BSR", "PVC", "PVT"],
    }
    
    # Tạo container cho bảng
    with st.spinner("⏳ Đang tải 50 mã từ thị trường..."):
        all_data = []
        
        for industry, symbols in industry_groups.items():
            for symbol in symbols:
                try:
                    # Lấy dữ liệu giá
                    stock = Vnstock().stock(symbol=symbol, source="TCBS")
                    price_data = stock.quote.history(
                        start=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                        end=datetime.now().strftime('%Y-%m-%d'),
                        interval='1D'
                    )
                    
                    if not price_data.empty and len(price_data) > 0:
                        latest = price_data.iloc[-1]
                        close_price = float(latest['close'])
                        open_price = float(latest['open'])
                        change = close_price - open_price
                        change_pct = (change / open_price * 100) if open_price > 0 else 0
                        
                        all_data.append({
                            'Ngành': industry,
                            'Mã': symbol,
                            'Giá': close_price,
                            '+/-': change,
                            '%': change_pct
                        })
                except Exception as e:
                    continue
        
        # Hiển thị theo CỘT - mỗi ngành một cột
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Tạo các cột cho mỗi ngành
            st.markdown("### 📊 Bảng giá thị trường theo ngành")
            
            # Số cột hiển thị
            num_industries = len(industry_groups)
            cols = st.columns(num_industries)
            
            # Hiển thị từng ngành trong một cột riêng
            for idx, (industry, symbols) in enumerate(industry_groups.items()):
                with cols[idx]:
                    st.markdown(f"**{industry}**")
                    
                    # Lọc dữ liệu theo ngành
                    industry_df = df[df['Ngành'] == industry].copy()
                    
                    if not industry_df.empty:
                        # Sắp xếp theo % từ TĂNG đến GIẢM
                        industry_df = industry_df.sort_values(by='%', ascending=False).reset_index(drop=True)
                        
                        # Hiển thị từng mã trong cột
                        for _, row in industry_df.iterrows():
                            price = row['Giá']
                            change_pct = row['%']
                            
                            # Chọn màu dựa trên % thay đổi
                            if change_pct > 0:
                                color = "green"
                                bg_color = "#d4edda"
                            elif change_pct < 0:
                                color = "red"
                                bg_color = "#f8d7da"
                            else:
                                color = "black"
                                bg_color = "#ffffff"
                            
                            # Hiển thị mã với màu nền
                            st.markdown(
                                f'<div style="background-color: {bg_color}; padding: 5px; margin: 2px 0; border-radius: 3px;">'
                                f'<span style="font-weight: bold;">{row["Mã"]}</span> '
                                f'<span style="font-size: 0.9em;">{price:,.2f}</span> '
                                f'<span style="color: {color}; font-weight: bold;">{change_pct:+.2f}%</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
            
            st.markdown("---")
            st.success(f"✅ Đã tải {len(df)} mã cổ phiếu từ {num_industries} nhóm ngành")
        else:
            st.error("❌ Không thể tải dữ liệu từ thị trường")
    
    # Nút quay lại
    if st.button("🔙 Quay lại tra cứu"):
        st.session_state.market_view_mode = False
        st.rerun()
    
    st.markdown("---")

# ==================== SCAN CỔ PHIẾU TỐT ====================
if hasattr(st.session_state, 'scan_mode') and st.session_state.scan_mode:
    st.header("🔍 Tìm cổ phiếu có khuyến nghị MUA theo phương pháp Chim Cút")
    st.info("🤖 AI đang phân tích CHI TIẾT từng cổ phiếu... Chỉ hiển thị các mã có khuyến nghị MUA.")
    
    # Load kiến thức Chim Cút
    knowledge_base = load_ptkt_examples()
    
    scan_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    symbols = st.session_state.scan_symbols
    total = len(symbols)
    
    # Tạo OpenAI client
    if st.session_state.openai_api_key:
        client = OpenAI(api_key=st.session_state.openai_api_key)
        
        for idx, sym in enumerate(symbols):
            status_text.text(f"📊 Phân tích {sym}... ({idx+1}/{total})")
            progress_bar.progress((idx + 1) / total)
            
            try:
                # Lấy dữ liệu giống như nút PTKT - dùng chính xác API vnstock
                stock = Vnstock().stock(symbol=sym, source="TCBS")
                
                # Lấy dữ liệu 365 ngày
                history_365d = stock.quote.history(
                    start=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                    end=datetime.now().strftime('%Y-%m-%d'),
                    interval='1D'
                )
                
                if not history_365d.empty and len(history_365d) >= 50:
                    # Lấy thông tin giá mới nhất - giống PTKT
                    latest = history_365d.iloc[-1]
                    latest_price = float(latest['close'])
                    
                    # Tính toán các MA - giống PTKT
                    ma5 = float(history_365d['close'].rolling(5).mean().iloc[-1])
                    ma10 = float(history_365d['close'].rolling(10).mean().iloc[-1])
                    ma20 = float(history_365d['close'].rolling(20).mean().iloc[-1])
                    ma50 = float(history_365d['close'].rolling(50).mean().iloc[-1])
                    
                    # Khối lượng
                    avg_volume_20 = history_365d['volume'].rolling(20).mean().iloc[-1]
                    volume_ratio = (latest['volume'] / avg_volume_20) * 100 if avg_volume_20 > 0 else 0
                    
                    # Thay đổi giá
                    change = latest['close'] - latest['open']
                    change_pct = (change / latest['open']) * 100 if latest['open'] > 0 else 0
                    
                    # Lấy 30 ngày gần nhất để phân tích
                    recent_30 = history_365d.tail(30)
                    
                    # Tạo thông tin cổ phiếu chi tiết - giống PTKT
                    stock_info = f"""
📊 DỮ LIỆU CỔ PHIẾU {sym}:

GIÁ HIỆN TẠI:
- Giá đóng cửa: {latest['close']:,.2f} VND
- Thay đổi: {change:,.2f} VND ({change_pct:+.2f}%)
- Giá mở cửa: {latest['open']:,.2f} VND
- Cao nhất: {latest['high']:,.2f} VND
- Thấp nhất: {latest['low']:,.2f} VND

KHỐI LƯỢNG:
- KL hôm nay: {latest['volume']:,.0f}
- KL TB 20 ngày: {avg_volume_20:,.0f}
- Tỷ lệ KL/TB: {volume_ratio:.1f}% {'(CAO)' if volume_ratio > 150 else '(THẤP)' if volume_ratio < 50 else '(BÌNH THƯỜNG)'}

ĐƯỜNG TRUNG BÌNH (MA):
- MA5: {ma5:,.2f} VND → Giá {'TRÊN' if latest['close'] > ma5 else 'DƯỚI'} MA5 ({(latest['close']/ma5*100-100):+.2f}%)
- MA10: {ma10:,.2f} VND → Giá {'TRÊN' if latest['close'] > ma10 else 'DƯỚI'} MA10 ({(latest['close']/ma10*100-100):+.2f}%)
- MA20: {ma20:,.2f} VND → Giá {'TRÊN' if latest['close'] > ma20 else 'DƯỚI'} MA20 ({(latest['close']/ma20*100-100):+.2f}%)
- MA50: {ma50:,.2f} VND → Giá {'TRÊN' if latest['close'] > ma50 else 'DƯỚI'} MA50 ({(latest['close']/ma50*100-100):+.2f}%)

XU HƯỚNG 30 NGÀY GẦN ĐÂY:
- Giá cao nhất: {recent_30['high'].max():,.2f} VND
- Giá thấp nhất: {recent_30['low'].min():,.2f} VND
- Biên độ: {((recent_30['high'].max() - recent_30['low'].min()) / recent_30['low'].min() * 100):.2f}%
"""
                    
                    # Tạo system prompt giống PTKT - ÁP DỤNG ĐẦY ĐỦ KIẾN THỨC CHIM CÚT
                    system_prompt = f"""Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam theo phương pháp Chim Cút.

═══════════════════════════════════════════════════════
📚 KIẾN THỨC CỦA BẠN (3 mẫu phân tích Chim Cút chi tiết):
═══════════════════════════════════════════════════════
{knowledge_base}

🎯 NHIỆM VỤ PHÂN TÍCH NHANH:
Áp dụng CHÍNH XÁC kiến thức Chim Cút đã học:

1. **Xu hướng**: dựa vào giá so với MA5/10/20/50
2. **Volume**: So sánh với TB 20 ngày theo bảng kiến thức
3. **Vùng cung cầu**: Hỗ trợ & kháng cự từ data 30 ngày
4. **Khuyến nghị**: Theo bảng "Quy tắc tổng hợp"

CẤU TRÚC TRẢ LỜI NGẮN GỌN (200 từ):
• **I. Xu hướng** (ngắn/trung hạn với số liệu)
• **II. Volume & Momentum**
• **III. Vùng hỗ trợ & kháng cự**
• **IV. ▸ Khuyến Nghị Vị Thế: MUA / BÁN / GOM / QUAN SÁT**
• **V. Quản trị lệnh** (nếu MUA: giá vào, SL)
"""
                    
                    # User prompt với dữ liệu cổ phiếu
                    user_prompt = f"""{stock_info}

Hãy phân tích NHANH nhưng ĐẦY ĐỦ theo phương pháp Chim Cút.
BẮT BUỘC có phần "▸ Khuyến Nghị Vị Thế:" rõ ràng.
CHỈ khuyến nghị MUA khi THỰC SỰ có tín hiệu tốt theo kiến thức đã học."""

                    # Gọi AI phân tích - giống PTKT
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            max_tokens=800,
                            temperature=0.3
                        )
                        
                        ai_analysis = response.choices[0].message.content
                        
                        # Lọc CHỈ HIỂN THỊ các mã có khuyến nghị MUA
                        is_buy = False
                        analysis_upper = ai_analysis.upper()
                        
                        # Tìm phần khuyến nghị
                        if '▸' in analysis_upper or 'KHUYẾN NGHỊ' in analysis_upper or 'VỊ THẾ' in analysis_upper:
                            lines = analysis_upper.split('\n')
                            for line in lines:
                                if ('KHUYẾN NGHỊ' in line or 'VỊ THẾ' in line or '▸' in line):
                                    # Kiểm tra có từ MUA và KHÔNG có từ phủ định
                                    if 'MUA' in line:
                                        negative_words = ['KHÔNG', 'CHƯA', 'NÊN BÁN', 'QUAN SÁT', 'CHƯA MUA']
                                        if not any(neg in line for neg in negative_words):
                                            is_buy = True
                                            break
                        
                        # CHỈ thêm và hiển thị nếu có khuyến nghị MUA
                        if is_buy:
                            scan_results.append({
                                'symbol': sym,
                                'price': latest_price,
                                'analysis': ai_analysis
                            })
                            
                            # Hiển thị ngay - BỎ chữ VND, chỉ để số
                            with results_container:
                                with st.expander(f"✅ {sym} - {latest_price:,.2f}", expanded=True):
                                    st.markdown(f"**Giá hiện tại:** {latest_price:,.2f}")
                                    st.markdown(f"**Thay đổi:** {change:,.2f} ({change_pct:+.2f}%)")
                                    st.markdown("---")
                                    st.markdown(ai_analysis)
                    except Exception as e:
                        st.warning(f"⚠️ Lỗi phân tích AI cho {sym}: {str(e)}")
                        
            except Exception as e:
                continue
    
    progress_bar.empty()
    status_text.empty()
    
    # Tóm tắt kết quả
    if scan_results:
        st.success(f"✅ Tìm thấy {len(scan_results)} cổ phiếu có KHUYẾN NGHỊ MUA!")
        
        st.markdown("### 🎯 TÓM TẮT TOP CỔ PHIẾU KHUYẾN NGHỊ MUA:")
        for result in scan_results:
            st.markdown(f"**{result['symbol']}** - Giá: {result['price']:,.2f}")
    else:
        st.warning("⚠️ Không tìm thấy cổ phiếu nào có khuyến nghị MUA trong danh sách 10 mã.")
    
    # Reset scan mode
    if st.button("🔙 Quay lại tra cứu thường"):
        st.session_state.scan_mode = False
        st.rerun()
    
    st.markdown("---")

# Xử lý khi nhấn button hoặc Enter
if submit_button:
    # Lưu symbol vào session state
    st.session_state.current_symbol = symbol
    
    try:
        with st.spinner(f"Đang tải dữ liệu {symbol}..."):
            # Khởi tạo
            stock = Vnstock().stock(symbol=symbol, source=source)
            
            # Tab layout
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Giá & Biểu đồ", "🏢 Thông tin công ty", "💰 Tài chính", "📋 Chỉ số", "🤖 AI Phân tích"])
            
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
                    # Lưu vào session state
                    st.session_state.price_data = price_data
                except Exception as e:
                    st.error(f"Lỗi khi lấy dữ liệu giá: {str(e)}")
                    st.info(f"💡 Thử đổi nguồn dữ liệu sang TCBS hoặc MSN")
                    price_data = pd.DataFrame()
                    st.session_state.price_data = price_data
                
                if not price_data.empty and len(price_data) > 0:
                    # Hiển thị thông tin realtime
                    col1, col2, col3, col4, col5 = st.columns(5)
                    latest = price_data.iloc[-1]
                    
                    with col1:
                        st.metric("Giá đóng cửa", f"{latest['close']:,.2f}", 
                                 f"{latest['close'] - latest['open']:,.2f}")
                    with col2:
                        st.metric("Cao nhất", f"{latest['high']:,.2f}")
                    with col3:
                        st.metric("Thấp nhất", f"{latest['low']:,.2f}")
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
            
            # TAB 5: AI Phân tích
            with tab5:
                st.subheader(f"🤖 AI Phân tích cổ phiếu {symbol}")
                st.info("💡 **Phần AI đã được chuyển xuống cuối trang** (sau tất cả các tab).")
                st.markdown("**Lý do kỹ thuật:** AI chat cần nằm ngoài tabs để hoạt động ổn định khi rerun.")
        
        st.success(f"✅ Đã tải xong dữ liệu cho {symbol}!")
        
    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")
        st.info("Vui lòng kiểm tra lại mã chứng khoán hoặc kết nối internet.")

# ==================== PHẦN AI CHAT (NGOÀI TABS) ====================
# Đặt ở đây để tránh bị mất khi rerun
if st.session_state.current_symbol:
    symbol = st.session_state.current_symbol
    
    st.markdown("---")
    st.subheader(f"🤖 AI Phân tích cổ phiếu {symbol}")
    
    if not st.session_state.openai_api_key:
        st.warning("⚠️ Vui lòng nhập OpenAI API Key ở sidebar để sử dụng tính năng AI")
    else:
        # Kiểm tra xem có message đang chờ xử lý không
        user_messages = [m for m in st.session_state.messages if m["symbol"] == symbol and m["role"] == "user"]
        assistant_messages = [m for m in st.session_state.messages if m["symbol"] == symbol and m["role"] == "assistant"]
        is_processing = len(user_messages) > len(assistant_messages)
        
        # Chỉ hiển thị nút khi KHÔNG đang xử lý
        if not is_processing:
            # Nút phân tích
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🎯 PTKT Chim Cút", use_container_width=True, type="primary", key="ptkt_button"):
                    # Đọc các file mẫu khuyến nghị
                    ptkt_examples = load_ptkt_examples()
                    
                    # Tạo prompt chi tiết với các file mẫu
                    auto_prompt = f"""Phân tích TOÀN DIỆN và CHI TIẾT cổ phiếu {symbol} theo phương pháp Chim Cút.

YÊU CẦU QUAN TRỌNG:
1. Phải phân tích ĐẦY ĐỦ TẤT CẢ các phần như trong mẫu
2. Sử dụng CHÍNH XÁC format và emoji như mẫu (✨ ━ ▸ • →)
3. Đưa ra con số cụ thể, không được nói chung chung
4. Phải tính toán và đưa ra các mức giá cụ thể

CÁC PHẦN BẮT BUỘC PHẢI CÓ:
▸ Xu Hướng Giá (ngắn hạn, trung hạn, dài hạn với MA5, MA10, MA20, MA50, MA100, MA200)
▸ Xu Hướng Khối Lượng (so sánh VMA5, VMA20, VMA50, VMA100, VMA200)
▸ Kết Hợp Giá & Khối Lượng (phân tích 3 khung thời gian)
▸ Phân Tích Cung - Cầu (POC, vùng khối lượng cao, VWAP)
▸ Mức Giá Quan Trọng (kháng cự, hỗ trợ, breakout, breakdown)
▸ Biến Động Giá (ATR5, ATR20, so sánh biến động)
▸ Mô Hình Giá & Nến (pattern, độ tin cậy, ADX)
⚠ Rủi Ro & Tương Quan Thị Trường (tương quan VNINDEX)
▸ Khuyến Nghị Vị Thế (MUA/BÁN/QUAN SÁT với lý do cụ thể)
▸ Giá Mục Tiêu (kịch bản tăng và giảm với Fibonacci)

Dưới đây là 3 ví dụ mẫu HOÀN CHỈNH. Hãy làm theo CHÍNH XÁC format và mức độ chi tiết này:

━━━━━━━━━━━━━━━━━━━━━━━━━
{ptkt_examples}
━━━━━━━━━━━━━━━━━━━━━━━━━

BÂY GIỜ hãy phân tích cổ phiếu {symbol} với:
- ĐẦY ĐỦ TẤT CẢ các phần như mẫu trên
- Format CHÍNH XÁC như mẫu (emoji, gạch đầu dòng, cấu trúc)
- Con số CỤ THỂ cho tất cả các chỉ số
- Khuyến nghị RÕ RÀNG (MUA/BÁN/QUAN SÁT)
- Giá mục tiêu CỤ THỂ

KHÔNG được bỏ qua bất kỳ phần nào!"""
                    
                    st.session_state.messages.append({
                        "role": "user",
                        "content": auto_prompt,
                        "symbol": symbol
                    })
                    st.rerun()
            
            with col2:
                if st.button("🔄 Xóa lịch sử", use_container_width=True, key="clear_button"):
                    st.session_state.messages = [m for m in st.session_state.messages if m["symbol"] != symbol]
                    st.rerun()
        
        # Hiển thị lịch sử chat
        for message in st.session_state.messages:
            if message["symbol"] == symbol:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Input chat (chỉ hiện khi không đang xử lý)
        if not is_processing:
            if prompt := st.chat_input("Hỏi AI về cổ phiếu này...", key="chat_input"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt,
                    "symbol": symbol
                })
                st.rerun()

# Xử lý AI response (chạy sau khi có user message)
if st.session_state.current_symbol and st.session_state.openai_api_key:
    symbol = st.session_state.current_symbol
    price_data = st.session_state.price_data if st.session_state.price_data is not None else pd.DataFrame()
    
    # Kiểm tra xem có message của user chưa được AI trả lời không
    user_messages = [m for m in st.session_state.messages if m["symbol"] == symbol and m["role"] == "user"]
    assistant_messages = [m for m in st.session_state.messages if m["symbol"] == symbol and m["role"] == "assistant"]
    
    # Nếu số message user > assistant, nghĩa là có câu hỏi chưa trả lời
    if len(user_messages) > len(assistant_messages):
        # Lấy câu hỏi cuối cùng chưa được trả lời
        prompt = user_messages[-1]["content"]
        
        # Hiển thị trong một container
        with st.container():
            st.info(f"🤖 Đang xử lý câu hỏi cho {symbol}...")
            
            with st.spinner("AI đang phân tích, vui lòng đợi..."):
                try:
                    # Khởi tạo OpenAI client
                    client = OpenAI(api_key=st.session_state.openai_api_key)
                    
                    # Đọc kiến thức Chim Cút
                    import os
                    knowledge_base = ""
                    
                    if "chim cút" in prompt.lower() or "ptkt" in prompt.lower() or "phương pháp chim cút" in prompt.lower():
                        # Đọc file kienthucchimcut.txt
                        kb_file = "knowledge/kienthucchimcut.txt"
                        if os.path.exists(kb_file):
                            with open(kb_file, "r", encoding="utf-8") as f:
                                knowledge_base = f.read()
                    else:
                        # Đọc file kiến thức chung
                        if os.path.exists("ai_knowledge.txt"):
                            with open("ai_knowledge.txt", "r", encoding="utf-8") as f:
                                knowledge_base = f.read()
                    
                    # Chuẩn bị dữ liệu chi tiết từ vnstock
                    stock_info = ""
                    
                    if not price_data.empty:
                        # Lấy 30 ngày gần nhất
                        recent_data = price_data.tail(30)
                        
                        # Tính các chỉ số kỹ thuật cơ bản
                        latest = price_data.iloc[-1]
                        prev_close = price_data.iloc[-2]['close'] if len(price_data) > 1 else latest['close']
                        change = latest['close'] - prev_close
                        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
                        
                        # Tính MA
                        ma5 = recent_data['close'].tail(5).mean() if len(recent_data) >= 5 else None
                        ma10 = recent_data['close'].tail(10).mean() if len(recent_data) >= 10 else None
                        ma20 = recent_data['close'].tail(20).mean() if len(recent_data) >= 20 else None
                        ma50 = price_data['close'].tail(50).mean() if len(price_data) >= 50 else None
                        ma100 = price_data['close'].tail(100).mean() if len(price_data) >= 100 else None
                        ma200 = price_data['close'].tail(200).mean() if len(price_data) >= 200 else None
                        
                        # Volume trung bình
                        avg_volume_20 = recent_data['volume'].tail(20).mean() if len(recent_data) >= 20 else None
                        volume_ratio = (latest['volume'] / avg_volume_20 * 100) if avg_volume_20 and avg_volume_20 > 0 else 0
                        
                        # Tính ADX đơn giản (chỉ số xu hướng)
                        # ADX đo lường sức mạnh xu hướng (0-100)
                        def calculate_adx(df, period=14):
                            if len(df) < period + 1:
                                return None
                            
                            # Tính True Range
                            high_low = df['high'] - df['low']
                            high_close = abs(df['high'] - df['close'].shift(1))
                            low_close = abs(df['low'] - df['close'].shift(1))
                            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                            
                            # Tính +DM và -DM
                            high_diff = df['high'].diff()
                            low_diff = -df['low'].diff()
                            
                            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
                            minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
                            
                            # Smooth
                            atr = tr.rolling(window=period).mean()
                            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
                            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
                            
                            # ADX
                            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
                            adx = dx.rolling(window=period).mean()
                            
                            return adx.iloc[-1] if not adx.empty else None
                        
                        adx = calculate_adx(price_data, 14)
                        
                        # Lịch sử giá 365 ngày gần nhất (1 năm)
                        history_365d = price_data.tail(365)[['close', 'volume']].copy()
                        
                        # Tóm tắt theo tháng để không quá dài
                        if len(history_365d) > 30:
                            # Lấy 30 ngày gần nhất hiển thị chi tiết
                            recent_30 = history_365d.tail(30)
                            history_str = "30 NGÀY GẦN NHẤT:\n" + "\n".join([
                                f"  {idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else idx}: "
                                f"Giá {row['close']:,.2f} VND, KL {row['volume']:,.0f}"
                                for idx, row in recent_30.iterrows()
                            ])
                            
                            # Thêm thống kê 365 ngày
                            history_str += f"\n\nTHỐNG KÊ 365 NGÀY (1 NĂM):\n"
                            history_str += f"  - Giá cao nhất: {history_365d['close'].max():,.2f} VND\n"
                            history_str += f"  - Giá thấp nhất: {history_365d['close'].min():,.2f} VND\n"
                            history_str += f"  - Giá trung bình: {history_365d['close'].mean():,.2f} VND\n"
                            history_str += f"  - Biên độ dao động: {((history_365d['close'].max() - history_365d['close'].min()) / history_365d['close'].min() * 100):.2f}%\n"
                            history_str += f"  - KL trung bình: {history_365d['volume'].mean():,.0f}\n"
                            history_str += f"  - Tổng số ngày giao dịch: {len(history_365d)}"
                        else:
                            history_str = "\n".join([
                                f"  {idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else idx}: "
                                f"Giá {row['close']:,.2f} VND, KL {row['volume']:,.0f}"
                                for idx, row in history_365d.iterrows()
                            ])
                        
                        stock_info = f"""
📊 DỮ LIỆU CỔ PHIẾU {symbol} (Cập nhật: {latest.name.strftime('%Y-%m-%d') if hasattr(latest.name, 'strftime') else 'N/A'}):

GIÁ HIỆN TẠI:
- Giá đóng cửa: {latest['close']:,.2f} VND
- Thay đổi: {change:,.2f} VND ({change_pct:+.2f}%)
- Giá mở cửa: {latest['open']:,.2f} VND
- Cao nhất trong ngày: {latest['high']:,.2f} VND
- Thấp nhất trong ngày: {latest['low']:,.2f} VND

KHỐI LƯỢNG:
- KL hôm nay: {latest['volume']:,.0f}
- KL TB 20 ngày: {avg_volume_20:,.0f}
- Tỷ lệ KL/TB: {volume_ratio:.1f}% {'(CAO)' if volume_ratio > 150 else '(THẤP)' if volume_ratio < 50 else '(BÌNH THƯỜNG)'}

ĐƯỜNG TRUNG BÌNH (MA):
- MA5: {ma5:,.2f} VND → Giá {'TRÊN' if latest['close'] > ma5 else 'DƯỚI'} MA5 ({(latest['close']/ma5*100-100):+.2f}%)
- MA10: {ma10:,.2f} VND → Giá {'TRÊN' if latest['close'] > ma10 else 'DƯỚI'} MA10 ({(latest['close']/ma10*100-100):+.2f}%)
- MA20: {ma20:,.2f} VND → Giá {'TRÊN' if latest['close'] > ma20 else 'DƯỚI'} MA20 ({(latest['close']/ma20*100-100):+.2f}%)
- MA50: {ma50:,.2f} VND → Giá {'TRÊN' if latest['close'] > ma50 else 'DƯỚI'} MA50 ({(latest['close']/ma50*100-100):+.2f}%)
- MA100: {f"{ma100:,.2f} VND" if ma100 else 'N/A (cần >100 ngày dữ liệu)'}
- MA200: {f"{ma200:,.2f} VND" if ma200 else 'N/A (cần >200 ngày dữ liệu)'}

CHỈ SỐ XU HƯỚNG:
- ADX(14): {f"{adx:.1f}" if adx else 'N/A'} {('(XU HƯỚNG MẠNH)' if adx > 30 else '(XU HƯỚNG YẾU)' if adx < 20 else '(XU HƯỚNG VỪA)') if adx else ''}

XU HƯỚNG 30 NGÀY GẦN ĐÂY:
- Giá cao nhất: {recent_data['high'].max():,.2f} VND
- Giá thấp nhất: {recent_data['low'].min():,.2f} VND
- Biên độ dao động: {((recent_data['high'].max() - recent_data['low'].min()) / recent_data['low'].min() * 100):.2f}%

LỊCH SỬ GIÁ & KHỐI LƯỢNG:
{history_str}
"""
                    
                    analysis_data = {
                        "symbol": symbol,
                        "latest_price": price_data.iloc[-1].to_dict() if not price_data.empty else {},
                    }
                    
                    # Tạo system prompt với dữ liệu chi tiết
                    system_prompt = f"""Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam theo phương pháp Chim Cút.

═══════════════════════════════════════════════════════
📚 KIẾN THỨC CỦA BẠN:
═══════════════════════════════════════════════════════
{knowledge_base}

═══════════════════════════════════════════════════════
{stock_info}
═══════════════════════════════════════════════════════
{stock_info}
═══════════════════════════════════════════════════════

🎯 NHIỆM VỤ PHÂN TÍCH:
BẮT BUỘC áp dụng CHÍNH XÁC kiến thức Chim Cút đã học:

1. **Xác định xu hướng** dựa vào vị trí giá so với MA5/10/20/50
   - Giá > MA5 và MA10 → xu hướng tăng ngắn hạn
   - Giá > MA20 và MA50 → xu hướng tăng trung/dài hạn
   - Phân tích xem đang uptrend, downtrend hay sideway

2. **Phân tích khối lượng** theo bảng trong kiến thức:
   - So sánh KL hôm nay với TB 20 ngày
   - Giá tăng + Volume tăng → xác nhận xu hướng
   - Giá tăng + Volume giảm → cảnh báo

3. **Vùng cung cầu**:
   - Xác định hỗ trợ (gần với MA20/MA50 hoặc đáy 30 ngày)
   - Xác định kháng cự (đỉnh 30 ngày)

4. **Khuyến nghị** theo bảng "Quy tắc tổng hợp" trong kiến thức

CẤU TRÚC TRẢ LỜI:
• **I. Tình hình xu hướng** (ngắn/trung/dài hạn với số liệu cụ thể)
• **II. Phân tích Volume & Momentum** (so sánh với kiến thức)
• **III. Vùng hỗ trợ & kháng cự** (giá cụ thể)
• **IV. Khuyến nghị** (MUA/BÁN/GOM/QUAN SÁT theo bảng quy tắc)
• **V. Quản trị lệnh** (Nếu mua: T0/T2/T5, mức cắt lỗ)
• **VI. Cảnh báo rủi ro**

⚠️ LƯU Ý QUAN TRỌNG:
- Trích dẫn CỤ THỂ các ngưỡng từ kiến thức (ADX>30, Vol>150%TB...)
- So sánh số liệu thực tế với quy tắc trong kiến thức
- Đưa ra mức giá CỤ THỂ cho hỗ trợ/kháng cự/cắt lỗ
- Luôn nhắc: "Đây chỉ là tham khảo, NĐT tự chịu trách nhiệm quyết định"

Hãy phân tích CHUYÊN NGHIỆP theo phương pháp Chim Cút!"""
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    # Lưu response
                    ai_response = response.choices[0].message.content
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ai_response,
                        "symbol": symbol
                    })
                    
                    # Rerun để hiển thị
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"❌ Lỗi: {str(e)}"
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "symbol": symbol
                    })
                    st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.info("💡 Dữ liệu từ vnstock API")
