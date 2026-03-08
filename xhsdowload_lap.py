import streamlit as st
import yt_dlp
import re
import os
import time

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="XHS Collector - Author Lập", layout="wide")

# CSS: Nền caro đỏ, Title góc trái, Nút dầy, Đổ bóng đa lớp
st.markdown("""
    <style>
    /* Nền caro sọc đỏ nhạt */
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }

    /* Tiêu đề nhỏ gọn ở góc trái */
    .brand-tag {
        position: fixed;
        top: 10px;
        left: 10px;
        font-size: 14px;
        font-weight: 800;
        color: #ff2442;
        background: rgba(255, 255, 255, 0.8);
        padding: 5px 12px;
        border-radius: 5px;
        border-left: 3px solid #ff2442;
        z-index: 1000;
    }

    /* Nút Chất lượng: Thân trắng, Chữ đỏ siêu dầy, Bóng hồng 30% */
    .quality-btn div.stButton > button {
        background-color: #ffffff !important;
        color: #ff2442 !important;
        border: 2px solid #ff2442 !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 52px !important;
        font-size: 16px !important;
        font-weight: 900 !important; /* Font chữ dầy nhất */
        box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important;
        transition: 0.2s ease;
    }
    .quality-btn div.stButton > button:hover {
        transform: translate(-2px, -2px);
        box-shadow: 8px 8px 20px rgba(255, 36, 66, 0.4) !important;
    }

    /* Nút Hành động: Thân hồng, Chữ trắng, Bóng đen */
    .action-btn div.stButton > button {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 55px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.5) !important;
        transition: 0.2s ease;
    }
    .action-btn div.stButton > button:hover {
        background-color: #e61e3a !important;
        box-shadow: 8px 8px 20px rgba(0, 0, 0, 0.6) !important;
        transform: scale(1.02);
    }

    /* Thanh tiến trình màu đỏ */
    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    
    .status-msg {
        text-align: center;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# Tên ứng dụng tinh gọn góc trái
st.markdown("<div class='brand-tag'>XHS Collector | Author Lập</div>", unsafe_allow_html=True)

# --- HÀM XỬ LÝ DỮ LIỆU ---
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
st.write("") # Tạo khoảng trống

# Khu vực nhập liệu tự động nhận link
_, mid_col, _ = st.columns([1, 3, 1])
with mid_col:
    raw_input = st.text_area("Dán nội dung từ App vào đây:", 
                            height=100, 
                            placeholder="Hệ thống sẽ tự động quét link tư liệu cho anh...")

target_url = extract_url(raw_input)

# Hiển thị tình trạng link
if not target_url:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ dán link...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Hãy chọn chất lượng để Nhà văn Lập xử lý.</div>", unsafe_allow_html=True)

# 4 Nút chất lượng luôn hiển thị, tập trung ở giữa
st.markdown("<p style='text-align:center; font-weight:bold;'>CHỌN CHẤT LƯỢNG TẢI XUỐNG:</p>", unsafe_allow_html=True)
st.markdown("<div class='quality-btn'>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

selected_q = None
is_off = not bool(target_url)

if b1.button("ORIGIN", disabled=is_off): selected_q = "Origin"
if b2.button("1080P", disabled=is_off): selected_q = "1080p"
if b3.button("720P", disabled=is_off): selected_q = "720p"
if b4.button("480P", disabled=is_off): selected_q = "480p"
st.markdown("</div>", unsafe_allow_html=True)

# Xử lý khi nhấn nút
if selected_q and target_url:
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        bar = st.progress(0)
        for i in range(1, 101):
            time.sleep(0.01)
            bar.progress(i)

    try:
        data = get_data(target_url, selected_q)
        st.divider()
        
        c1, c2 = st.columns([1, 1.4])
        with c1:
            st.image(data.get('thumbnail'), caption="Preview", use_container_width=True)
        with c2:
            st.subheader("📌 Chi tiết bản ghi")
            st.write(f"**Tác giả:** {data.get('uploader')}")
            st.write(f"**Tiêu đề:** {data.get('title')}")
            
            # Nút Tải Video (Hành động: Hồng, Chữ trắng, Bóng đen)
            st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
            st.link_button("📥 TẢI XUỐNG VIDEO NGAY", data.get('url'), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📝 Nội dung mô tả")
        st.info(data.get('description', 'Trống'))
        
        # Nút Lưu Văn Bản (Hành động: Hồng, Chữ trắng, Bóng đen)
        st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
        txt_meta = f"TÁC GIẢ: {data.get('uploader')}\nNỘI DUNG:\n{data.get('description')}"
        st.download_button("💾 LƯU FILE VĂN BẢN (.TXT)", txt_meta, file_name=f"Lap_Note_{data.get('id')}.txt")
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Lỗi kỹ thuật: {e}")

st.markdown("<div style='text-align: center; color: #999; margin-top: 50px; font-size: 13px;'>2026 Edition | Thiết kế riêng cho Tác giả Lập</div>", unsafe_allow_html=True)
