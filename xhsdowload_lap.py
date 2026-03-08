import streamlit as st
import yt_dlp
import re
import os
import time

# --- CẤU HÌNH GIAO DIỆN HỆ THỐNG ---
st.set_page_config(page_title="XHS Collector - Author Lập", layout="wide")

# CSS: Khôi phục nền caro, Title góc trái, Font dầy 900, Bóng đổ đa lớp
st.markdown("""
    <style>
    /* Nền caro sọc đỏ nhạt đặc trưng */
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }

    /* Tên ứng dụng thu nhỏ góc trái */
    .brand-tag {
        position: fixed;
        top: 10px;
        left: 10px;
        font-size: 13px;
        font-weight: 800;
        color: #ff2442;
        background: rgba(255, 255, 255, 0.9);
        padding: 4px 10px;
        border-radius: 4px;
        border-left: 3px solid #ff2442;
        z-index: 9999;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }

    /* Nút Chất lượng (Quality): Thân trắng, Chữ đỏ, Font 900, Bóng hồng 30% lệch 6px */
    .q-btn div.stButton > button {
        background-color: #ffffff !important;
        color: #ff2442 !important;
        border: 2px solid #ff2442 !important;
        border-radius: 10px !important;
        width: 100% !important;
        height: 52px !important;
        font-size: 16px !important;
        font-weight: 900 !important; /* Font chữ siêu dầy */
        box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important;
        transition: 0.2s ease;
    }
    .q-btn div.stButton > button:hover {
        transform: translate(-2px, -2px);
        box-shadow: 8px 8px 20px rgba(255, 36, 66, 0.4) !important;
    }

    /* Nút Hành động (Action): Thân hồng, Chữ trắng, Bóng đen */
    .a-btn div.stButton > button, .a-btn div.stDownloadButton > button {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        width: 100% !important;
        height: 55px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.5) !important;
        transition: 0.2s ease;
    }
    .a-btn div.stButton > button:hover, .a-btn div.stDownloadButton > button:hover {
        background-color: #e61e3a !important;
        box-shadow: 8px 8px 20px rgba(0, 0, 0, 0.6) !important;
        transform: scale(1.02);
    }

    /* Tinh chỉnh Progress Bar */
    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    
    .status-msg {
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# Tên ứng dụng cố định ở góc trái
st.markdown("<div class='brand-tag'>XHS Collector | Author Lập</div>", unsafe_allow_html=True)

# --- HÀM HỖ TRỢ ---
def extract_url(text):
    pattern = r'https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def get_data(url, q_key):
    q_map = {
        "Origin": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best"
    }
    ydl_opts = {'format': q_map.get(q_key, 'best'), 'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# --- GIAO DIỆN CHÍNH ---
st.write("") # Padding cho header

_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung từ App Xiaohongshu vào đây:", 
                            height=100, 
                            placeholder="Hệ thống tự động quét link tư liệu...")

target_link = extract_url(raw_input)

# Hiển thị tình trạng nhận diện link
if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Hãy chọn chất lượng để Nhà văn Lập xử lý.</div>", unsafe_allow_html=True)

# Căn giữa hàng 4 nút chất lượng
st.markdown("<p style='text-align:center; font-weight:bold;'>CHỌN CHẤT LƯỢNG:</p>", unsafe_allow_html=True)
st.markdown("<div class='q-btn'>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

selected_q = None
is_locked = not bool(target_link)

if b1.button("ORIGIN", disabled=is_locked): selected_q = "Origin"
if b2.button("1080P", disabled=is_locked): selected_q = "1080p"
if b3.button("720P", disabled=is_locked): selected_q = "720p"
if b4.button("480P", disabled=is_locked): selected_q = "480p"
st.markdown("</div>", unsafe_allow_html=True)

# Xử lý khi nhấn nút
if selected_q and target_link:
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        bar = st.progress(0)
        for i in range(1, 101):
            time.sleep(0.01)
            bar.progress(i)

    try:
        data = get_data(target_link, selected_q)
        st.divider()
        
        c1, c2 = st.columns([1, 1.4])
        with c1:
            st.image(data.get('thumbnail'), use_container_width=True)
        with c2:
            st.subheader("📋 Chi tiết bản ghi")
            st.write(f"**Tác giả:** {data.get('uploader')}")
            st.write(f"**Tiêu đề:** {data.get('title')}")
            
            # Nút Tải Video (Hành động: Hồng, Chữ trắng, Bóng đen)
            st.markdown("<div class='a-btn'>", unsafe_allow_html=True)
            st.link_button("📥 TẢI XUỐNG VIDEO NGAY", data.get('url'), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📝 Nội dung mô tả")
        st.info(data.get('description', 'Trống'))
        
        # Nút Lưu Văn Bản (Hành động: Hồng, Chữ trắng, Bóng đen)
        st.markdown("<div class='a-btn'>", unsafe_allow_html=True)
        txt_meta = f"TÁC GIẢ: {data.get('uploader')}\nNỘI DUNG:\n{data.get('description')}"
        st.download_button("💾 LƯU FILE VĂN BẢN (.TXT)", txt_meta, file_name=f"TuLieu_Lap_{data.get('id')}.txt")
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Lỗi: {e}")

st.markdown("<div style='text-align: center; color: #999; margin-top: 50px; font-size: 13px;'>2026 Edition | Thiết kế riêng cho Nhà văn Lập</div>", unsafe_allow_html=True)
