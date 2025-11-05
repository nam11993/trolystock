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

# Sidebar
st.sidebar.header("⚙️ Cài đặt")

# API Key input
with st.sidebar.expander("🔑 Cấu hình OpenAI API", expanded=not st.session_state.openai_api_key):
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.openai_api_key,
        help="Nhập API key từ https://platform.openai.com/api-keys"
    )
    if api_key:
        st.session_state.openai_api_key = api_key
        st.success("✅ API Key đã được lưu!")

st.sidebar.markdown("---")

# Form để có thể nhấn Enter
with st.sidebar.form(key="search_form"):
    # Input mã chứng khoán
    symbol = st.text_input("Nhập mã chứng khoán", value="VNM").upper()

    # Chọn nguồn dữ liệu (mặc định TCBS)
    source = st.selectbox("Nguồn dữ liệu", ["TCBS", "VCI", "MSN"])

    # Mặc định 365 ngày lịch sử (1 năm)
    days = 365
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Button để lấy dữ liệu
    submit_button = st.form_submit_button("🔍 Tra cứu", type="primary", use_container_width=True)

# Xử lý khi nhấn button hoặc Enter
if submit_button:
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
                    
                    # Hiển thị lịch sử chat
                    for message in st.session_state.messages:
                        if message["symbol"] == symbol:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])
                    
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
                        
                    # Gọi AI
                    with st.chat_message("assistant"):
                        with st.spinner("AI đang phân tích..."):
                            try:
                                client = OpenAI(api_key=st.session_state.openai_api_key)
                                
                                # Đọc kiến thức từ file
                                try:
                                    with open("ai_knowledge.txt", "r", encoding="utf-8") as f:
                                        knowledge_base = f.read()
                                except:
                                    knowledge_base = ""
                                
                                # Tạo context cho AI với kiến thức đã học
                                system_prompt = f"""Bạn là chuyên gia phân tích chứng khoán Việt Nam chuyên nghiệp.

KIẾN THỨC CỦA BẠN:
{knowledge_base}

DỮ LIỆU CỔ PHIẾU {symbol} HIỆN TẠI:
- Giá gần nhất: {analysis_data['latest_price']}
- Xu hướng 30 ngày gần đây có sẵn

NHIỆM VỤ:
1. Phân tích dựa trên kiến thức đã học và dữ liệu thực tế
2. Trả lời theo cấu trúc: Tình hình → Phân tích → Cơ hội & Rủi ro → Khuyến nghị → Lưu ý
3. Giải thích rõ ràng, dễ hiểu, có số liệu cụ thể
4. Luôn cảnh báo rủi ro và nhắc nhở đây chỉ là tham khảo

Hãy trả lời câu hỏi của nhà đầu tư một cách chuyên nghiệp."""                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": prompt}
                                        ],
                                        temperature=0.7,
                                        max_tokens=1000
                                    )
                                    
                                    ai_response = response.choices[0].message.content
                                    st.markdown(ai_response)
                                    
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": ai_response,
                                        "symbol": symbol
                                    })
                                    
                                except Exception as e:
                                    st.error(f"Lỗi khi gọi AI: {str(e)}")
                                    st.info("💡 Kiểm tra API key hoặc kết nối internet")
                    
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

# Footer
st.sidebar.markdown("---")
st.sidebar.info("💡 Dữ liệu từ vnstock API")
