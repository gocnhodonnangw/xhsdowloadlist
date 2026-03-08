import streamlit as st
import yt_dlp
import re
import os
import time

# --- CẤU HÌNH GIAO DIỆN HỆ THỐNG ---
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide")

# CSS: Nền caro đỏ, Title & Logo góc trái, Font dầy 950, Đổ bóng đa lớp
st.markdown("""
    <style>
    /* Nền caro sọc đỏ đặc trưng */
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }

    /* Khôi phục Logo và Tên ứng dụng ở góc trái */
    .brand-container {
        position: fixed;
        top: 15px;
        left: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(255, 255, 255, 0.9);
        padding: 8px 15px;
        border-radius: 8px;
        border-left: 5px solid #ff2442;
        z-index: 1000;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
    }
    .brand-logo { font-size: 20px; }
    .brand-name {
        font-size: 15px;
        font-weight: 900;
        color: #ff2442;
    }

    /* Nút Chất lượng: Thân trắng, Chữ đỏ, FONT SIÊU DẦY 950, Bóng hồng 30% */
    .q-btn-box div.stButton > button {
        background-color: #ffffff !important;
        color: #ff2442 !important;
        border: 2px solid #ff2442 !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 55px !important;
        font-size: 17px !important;
        font-weight: 950 !important; /* Độ dầy cực đại */
        box-shadow: 6px 6px 0px rgba(255, 36, 66, 0.3) !important;
        transition: all 0.2s ease;
    }
    .q-btn-box div.stButton > button:hover {
        transform: translate(-2px, -2px);
        box-shadow: 8px 8px 0px rgba(255, 36, 66, 0.4) !important;
        background-color: #fff5f6 !important;
    }

    /* Nút Hành động: Thân hồng, Chữ trắng, Bóng đen */
    .a-btn-box div.stButton > button, .a-btn-box div.stDownloadButton > button {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 60px !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.5) !important;
        transition: 0.3s ease;
    }
    .a-btn-box div.stButton > button:hover {
        background-color: #e61e3a !important;
        box-shadow: 8px 8px 20px rgba(0, 0, 0, 0.6) !important;
        transform: scale(1.02);
    }

    /* Trạng thái nút khi chưa có link */
    div.stButton > button:disabled {
        opacity: 0.3;
        border: 2px solid #ccc !important;
        color: #999 !important;
        box-shadow: none !important;
    }

    /* Progress Bar màu đỏ */
    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    
    .status-msg {
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 25px;
        font-weight: 700;
        border: 1px dashed #ff2442;
    }
    </style>
    """, unsafe_allow_html=True)

# Hiển thị Logo và Title tinh gọn ở góc trái
st.markdown("""
    <div class='brand-container'>
        <span class='brand-logo'>📕</span>
        <span class='brand-name'>XHS Collector | Tác giả Lập</span>
    </div>
    """, unsafe_allow_html=True)

# --- HÀM XỬ LÝ KỸ THUẬT ---
def extract_link(text):
    pattern = r'https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def fetch_data(url, quality):
    q_map = {
        "Origin": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best"
    }
    ydl_opts = {'format': q_map.get(quality, 'best'), 'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# --- GIAO DIỆN TƯƠNG TÁC ---
st.write("") # Padding cho header fixed
st.write("")

# Khu vực nhập liệu tự động
_, mid_col, _ = st.columns([1, 3, 1])
with mid_col:
    raw_text = st.text_area("✍️ Dán nội dung Xiaohongshu tại đây:", 
                            height=120, 
                            placeholder="Hệ thống tự động gom link tư liệu...")

target_url = extract_link(raw_text)

# Hiển thị tình trạng link
if not target_url:
    st.markdown("<div class='status-msg' style='background-color: #fcfcfc; color: #888 !important;'>⚪ Hệ thống đang chờ dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Hãy chọn chất lượng để tải về.</div>", unsafe_allow_html=True)

# 4 Nút chất lượng luôn hiển thị, căn giữa
st.markdown("<p style='text-align:center; font-weight:900; color:#ff2442;'>CHỌN CHẤT LƯỢNG:</p>", unsafe_allow_html=True)
st.markdown("<div class='q-btn-box'>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

selected_quality = None
is_locked = not bool(target_url)

if b1.button("ORIGIN", disabled=is_locked): selected_quality = "Origin"
if b2.button("1080P", disabled=is_locked): selected_quality = "1080p"
if b3.button("720P", disabled=is_locked): selected_quality = "720p"
if b4.button("480P", disabled=is_locked): selected_quality = "480p"
st.markdown("</div>", unsafe_allow_html=True)

# Xử lý khi nhấn nút
if selected_quality and target_url:
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        bar = st.progress(0)
        status = st.empty()
        for i in range(1, 101):
            time.sleep(0.005)
            bar.progress(i)
            status.markdown(f"<p style='text-align:center;'>Đang gom luồng {selected_quality}: {i}%</p>", unsafe_allow_html=True)

    try:
        data = fetch_data(target_url, selected_quality)
        st.divider()
        
        c1, c2 = st.columns([1, 1.3])
        with c1:
            st.image(data.get('thumbnail'), caption="Ảnh bìa tư liệu", use_container_width=True)
        with c2:
            st.subheader("📋 Chi tiết bản ghi")
            st.write(f"**Tác giả:** {data.get('uploader')}")
            st.write(f"**Tiêu đề:** {data.get('title')}")
            
            # Nút Tải Video (Hồng, Chữ trắng, Bóng đen)
            st.markdown("<div class='a-btn-box'>", unsafe_allow_html=True)
            st.link_button("📥 TẢI XUỐNG VIDEO NGAY", data.get('url'), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📝 Nội dung mô tả bài viết")
        st.info(data.get('description', 'Không có nội dung chữ.'))
        
        # Nút Lưu Văn Bản (Hồng, Chữ trắng, Bóng đen)
        st.markdown("<div class='a-btn-box'>", unsafe_allow_html=True)
        txt_meta = f"TÁC GIẢ: {data.get('uploader')}\n\nNỘI DUNG:\n{data.get('description')}"
        st.download_button("💾 LƯU FILE VĂN BẢN (.TXT)", txt_meta, file_name=f"TuLieu_Lap_{data.get('id')}.txt")
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")

st.markdown("<div style='text-align: center; color: #999; margin-top: 50px; font-size: 13px;'>2026 Edition | Thiết kế dành riêng cho Nhà văn Lập</div>", unsafe_allow_html=True)
