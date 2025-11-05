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

# Cấu hình trang
st.set_page_config(
    page_title="Tra cứu chứng khoán VN",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Tra cứu Chứng khoán Việt Nam")
st.markdown("---")

# Khởi tạo session state cho lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""
if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = None
if "price_data" not in st.session_state:
    st.session_state.price_data = None

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
    
    if st.button("✅ Lưu & Kiểm tra kết nối"):
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
                st.success("✅ Kết nối OpenAI API thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi kết nối: {str(e)}")
                st.info("💡 Kiểm tra lại API key hoặc kết nối internet")
        else:
            st.error("❌ API key không hợp lệ! (phải bắt đầu với sk-)")
    
    if st.session_state.openai_api_key:
        st.info("🟢 API Key đã được lưu")

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
            
            # TAB 5: AI Phân tích
            with tab5:
                st.subheader(f"🤖 AI Phân tích cổ phiếu {symbol}")
                
                if not st.session_state.openai_api_key:
                    st.warning("⚠️ Vui lòng nhập OpenAI API Key ở sidebar để sử dụng tính năng AI")
                else:
                    # Chuẩn bị dữ liệu để gửi cho AI
                    analysis_data = {
                        "symbol": symbol,
                        "latest_price": price_data.iloc[-1].to_dict() if not price_data.empty else {},
                        "price_trend": price_data.tail(30).to_dict() if not price_data.empty else {}
                    }
                    
                    # Nút phân tích nhanh theo Chim Cút
                    col1, col2, col3 = st.columns([1, 1, 4])
                    with col1:
                        if st.button("🎯 PTKT Chim Cút", use_container_width=True, type="primary", key=f"ptkt_{symbol}"):
                            # Tự động gửi lệnh phân tích
                            auto_prompt = f"Phân tích kỹ thuật cổ phiếu {symbol} theo phương pháp Chim Cút. Hãy áp dụng CHÍNH XÁC các quy tắc về MA, ADX, Volume và đưa ra khuyến nghị cụ thể."
                            
                            # Thêm vào messages
                            st.session_state.messages.append({
                                "role": "user",
                                "content": auto_prompt,
                                "symbol": symbol
                            })
                            st.rerun()
                    
                    with col2:
                        if st.button("🔄 Xóa lịch sử", use_container_width=True, key=f"clear_{symbol}"):
                            st.session_state.messages = [m for m in st.session_state.messages if m["symbol"] != symbol]
                            st.rerun()
                    
                    # Debug info
                    with col3:
                        user_count = len([m for m in st.session_state.messages if m["symbol"] == symbol and m["role"] == "user"])
                        ai_count = len([m for m in st.session_state.messages if m["symbol"] == symbol and m["role"] == "assistant"])
                        if user_count > 0 or ai_count > 0:
                            st.caption(f"💬 User: {user_count} | AI: {ai_count}")
                    
                    # Hiển thị lịch sử chat
                    for message in st.session_state.messages:
                        if message["symbol"] == symbol:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])
                    
                    # Kiểm tra xem có message của user chưa được AI trả lời không
                    user_messages = [m for m in st.session_state.messages if m["symbol"] == symbol and m["role"] == "user"]
                    assistant_messages = [m for m in st.session_state.messages if m["symbol"] == symbol and m["role"] == "assistant"]
                    
                    # Nếu số message user > assistant, nghĩa là có câu hỏi chưa trả lời
                    if len(user_messages) > len(assistant_messages):
                        # Lấy câu hỏi cuối cùng chưa được trả lời
                        prompt = user_messages[-1]["content"]
                        
                        # Gọi AI để trả lời
                        with st.chat_message("assistant"):
                            with st.spinner("🤖 AI đang phân tích, vui lòng đợi..."):
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
                                    
                                    # Tạo context cho AI với kiến thức đã học
                                    system_prompt = f"""Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam theo phương pháp Chim Cút.

═══════════════════════════════════════════════════════
📚 KIẾN THỨC CỐT LÕI CỦA BẠN:
═══════════════════════════════════════════════════════
{knowledge_base}

═══════════════════════════════════════════════════════
📊 DỮ LIỆU CỔ PHIẾU {symbol} HIỆN TẠI:
═══════════════════════════════════════════════════════
- Giá gần nhất: {analysis_data['latest_price']}
- Dữ liệu 30 ngày gần đây đã có trong biểu đồ
- User có thể cung cấp thêm thông tin về MA, Volume, ADX

═══════════════════════════════════════════════════════
🎯 NHIỆM VỤ PHÂN TÍCH:
═══════════════════════════════════════════════════════
BẮT BUỘC tuân thủ CHÍNH XÁC các quy tắc trong kiến thức đã học, đặc biệt:

1. **Xác định xu hướng** theo MA5/10/20/50/100/200 và ADX
2. **Phân tích khối lượng** theo bảng đặc điểm (Vol ↑/↓ vs Giá ↑/↓)
3. **Vùng cung cầu** - xác định hỗ trợ/kháng cự
4. **Breakout/Bẫy giá** - phân biệt break thật vs bulltrap/beartrap
5. **Momentum** - đánh giá ADX và CMF
6. **Khuyến nghị** theo ĐÚNG bảng "Quy tắc tổng hợp" mục VIII

CẤU TRÚC TRẢ LỜI:
• **I. Tình hình xu hướng** (ngắn/trung/dài hạn)
• **II. Phân tích Volume & Momentum** (đối chiếu bảng kiến thức)
• **III. Vùng cung cầu** (support/resistance)
• **IV. Điều kiện & Khuyến nghị** (theo bảng quy tắc tổng hợp)
• **V. Quản trị lệnh** (T0/T2/T5 nếu mua, cắt lỗ ở đâu)
• **VI. Cảnh báo rủi ro**

⚠️ LƯU Ý:
- SỬ DỤNG CHÍNH XÁC các ngưỡng số trong kiến thức (ADX>30, Vol>150%TB, etc.)
- KHÔNG tự ý thêm chỉ báo khác ngoài kiến thức đã học
- CÓ SỐ LIỆU cụ thể, trích dẫn quy tắc từ kiến thức
- Luôn nhắc "Đây chỉ là tham khảo, nhà đầu tư tự chịu trách nhiệm quyết định"

Hãy phân tích theo ĐÚNG phương pháp Chim Cút đã học!"""
                                    
                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": prompt}
                                        ],
                                        temperature=0.7,
                                        max_tokens=2000
                                    )
                                    
                                    # Hiển thị kết quả
                                    ai_response = response.choices[0].message.content
                                    st.markdown(ai_response)
                                    
                                    # Lưu vào lịch sử
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": ai_response,
                                        "symbol": symbol
                                    })
                                    
                                except Exception as e:
                                    error_msg = f"❌ **Lỗi khi gọi OpenAI API:**\n\n```\n{str(e)}\n```\n\n"
                                    error_msg += "**Có thể do:**\n"
                                    error_msg += "- API key không đúng hoặc hết hạn\n"
                                    error_msg += "- Không có kết nối internet\n"
                                    error_msg += "- Tài khoản OpenAI hết credit\n\n"
                                    error_msg += "💡 Vui lòng kiểm tra lại API key ở sidebar"
                                    
                                    st.error(error_msg)
                                    
                                    # Lưu error vào lịch sử
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": error_msg,
                                        "symbol": symbol
                                    })
                    
                    # Input từ user
                    if prompt := st.chat_input("Hỏi AI về cổ phiếu này..."):
                        # Hiển thị câu hỏi của user
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        
                        st.session_state.messages.append({
                            "role": "user",
                            "content": prompt,
                            "symbol": symbol
                        })
                        
                        # Rerun để xử lý message mới
                        st.rerun()
                    
                    # Các câu hỏi gợi ý
                    st.markdown("---")
                    st.markdown("**💡 Câu hỏi gợi ý:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📊 Phân tích kỹ thuật {symbol}", use_container_width=True):
                            st.rerun()
                        if st.button(f"💰 Đánh giá định giá {symbol}", use_container_width=True):
                            st.rerun()
                    with col2:
                        if st.button(f"⚠️ Rủi ro khi đầu tư {symbol}", use_container_width=True):
                            st.rerun()
                        if st.button(f"🎯 Mục tiêu giá {symbol}", use_container_width=True):
                            st.rerun()
        
        st.success(f"✅ Đã tải xong dữ liệu cho {symbol}!")
        
    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")
        st.info("Vui lòng kiểm tra lại mã chứng khoán hoặc kết nối internet.")

# Phần AI Chat - hiển thị độc lập
if st.session_state.current_symbol:
    st.markdown("---")
    st.header(f"🤖 AI Phân tích - {st.session_state.current_symbol}")
    
    if not st.session_state.openai_api_key:
        st.warning("⚠️ Vui lòng nhập OpenAI API Key ở sidebar để sử dụng tính năng AI")
    else:
        # Nút phân tích
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🎯 PTKT Chim Cút", use_container_width=True, type="primary"):
                auto_prompt = f"Phân tích kỹ thuật cổ phiếu {st.session_state.current_symbol} theo phương pháp Chim Cút. Hãy áp dụng CHÍNH XÁC các quy tắc về MA, ADX, Volume và đưa ra khuyến nghị cụ thể."
                st.session_state.messages.append({
                    "role": "user",
                    "content": auto_prompt,
                    "symbol": st.session_state.current_symbol
                })
                st.rerun()
        
        with col2:
            if st.button("🔄 Xóa lịch sử", use_container_width=True):
                st.session_state.messages = [m for m in st.session_state.messages if m["symbol"] != st.session_state.current_symbol]
                st.rerun()
        
        # Hiển thị lịch sử chat
        for message in st.session_state.messages:
            if message["symbol"] == st.session_state.current_symbol:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Input chat
        if prompt := st.chat_input("Hỏi AI về cổ phiếu này..."):
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "symbol": st.session_state.current_symbol
            })
            st.rerun()

# Xử lý AI chat (chạy ngoài submit_button để xử lý rerun)
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
                                f"Giá {row['close']:,.0f} VND, KL {row['volume']:,.0f}"
                                for idx, row in recent_30.iterrows()
                            ])
                            
                            # Thêm thống kê 365 ngày
                            history_str += f"\n\nTHỐNG KÊ 365 NGÀY (1 NĂM):\n"
                            history_str += f"  - Giá cao nhất: {history_365d['close'].max():,.0f} VND\n"
                            history_str += f"  - Giá thấp nhất: {history_365d['close'].min():,.0f} VND\n"
                            history_str += f"  - Giá trung bình: {history_365d['close'].mean():,.0f} VND\n"
                            history_str += f"  - Biên độ dao động: {((history_365d['close'].max() - history_365d['close'].min()) / history_365d['close'].min() * 100):.2f}%\n"
                            history_str += f"  - KL trung bình: {history_365d['volume'].mean():,.0f}\n"
                            history_str += f"  - Tổng số ngày giao dịch: {len(history_365d)}"
                        else:
                            history_str = "\n".join([
                                f"  {idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else idx}: "
                                f"Giá {row['close']:,.0f} VND, KL {row['volume']:,.0f}"
                                for idx, row in history_365d.iterrows()
                            ])
                        
                        stock_info = f"""
📊 DỮ LIỆU CỔ PHIẾU {symbol} (Cập nhật: {latest.name.strftime('%Y-%m-%d') if hasattr(latest.name, 'strftime') else 'N/A'}):

GIÁ HIỆN TẠI:
- Giá đóng cửa: {latest['close']:,.0f} VND
- Thay đổi: {change:,.0f} VND ({change_pct:+.2f}%)
- Giá mở cửa: {latest['open']:,.0f} VND
- Cao nhất trong ngày: {latest['high']:,.0f} VND
- Thấp nhất trong ngày: {latest['low']:,.0f} VND

KHỐI LƯỢNG:
- KL hôm nay: {latest['volume']:,.0f}
- KL TB 20 ngày: {avg_volume_20:,.0f}
- Tỷ lệ KL/TB: {volume_ratio:.1f}% {'(CAO)' if volume_ratio > 150 else '(THẤP)' if volume_ratio < 50 else '(BÌNH THƯỜNG)'}

ĐƯỜNG TRUNG BÌNH (MA):
- MA5: {ma5:,.0f} VND → Giá {'TRÊN' if latest['close'] > ma5 else 'DƯỚI'} MA5 ({(latest['close']/ma5*100-100):+.2f}%)
- MA10: {ma10:,.0f} VND → Giá {'TRÊN' if latest['close'] > ma10 else 'DƯỚI'} MA10 ({(latest['close']/ma10*100-100):+.2f}%)
- MA20: {ma20:,.0f} VND → Giá {'TRÊN' if latest['close'] > ma20 else 'DƯỚI'} MA20 ({(latest['close']/ma20*100-100):+.2f}%)
- MA50: {ma50:,.0f} VND → Giá {'TRÊN' if latest['close'] > ma50 else 'DƯỚI'} MA50 ({(latest['close']/ma50*100-100):+.2f}%)
- MA100: {f"{ma100:,.0f} VND" if ma100 else 'N/A (cần >100 ngày dữ liệu)'}
- MA200: {f"{ma200:,.0f} VND" if ma200 else 'N/A (cần >200 ngày dữ liệu)'}

CHỈ SỐ XU HƯỚNG:
- ADX(14): {f"{adx:.1f}" if adx else 'N/A'} {('(XU HƯỚNG MẠNH)' if adx > 30 else '(XU HƯỚNG YẾU)' if adx < 20 else '(XU HƯỚNG VỪA)') if adx else ''}

XU HƯỚNG 30 NGÀY GẦN ĐÂY:
- Giá cao nhất: {recent_data['high'].max():,.0f} VND
- Giá thấp nhất: {recent_data['low'].min():,.0f} VND
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
