import streamlit as st
import yt_dlp
import re
import os
import time
from PIL import Image

# ==========================================
# 1. CẤU HÌNH GIAO DIỆN & STYLE (CSS)
# ==========================================
st.set_page_config(page_title="XHS Collector - Author Lập", layout="wide")

st.markdown("""
    <style>
    /* NỀN CARO SỌC ĐỎ ĐẶC TRƯNG */
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), 
                          linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }

    /* TIÊU ĐỀ GÓC TRÁI TINH GỌN */
    .brand-tag {
        position: fixed;
        top: 15px;
        left: 15px;
        font-size: 14px;
        font-weight: 800;
        color: #ff2442;
        background: rgba(255, 255, 255, 0.9);
        padding: 6px 15px;
        border-radius: 8px;
        border-left: 4px solid #ff2442;
        z-index: 1000;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.05);
    }

    /* NÚT CHẤT LƯỢNG (QUALITY): TRẮNG - CHỮ ĐỎ 900 - BÓNG HỒNG 30% */
    .q-btn div.stButton > button {
        background-color: #ffffff !important;
        color: #ff2442 !important;
        border: 2px solid #ff2442 !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 55px !important;
        font-size: 17px !important;
        font-weight: 900 !important; /* SIÊU DẦY */
        box-shadow: 6px 6px 0px rgba(255, 36, 66, 0.3) !important; /* BÓNG LỆCH 6PX */
        transition: all 0.2s ease;
    }
    .q-btn div.stButton > button:hover {
        transform: translate(-2px, -2px);
        box-shadow: 8px 8px 0px rgba(255, 36, 66, 0.4) !important;
    }
    .q-btn div.stButton > button:disabled {
        opacity: 0.3;
        border: 2px solid #ccc !important;
        color: #999 !important;
        box-shadow: none !important;
    }

    /* NÚT HÀNH ĐỘNG (ACTION): HỒNG - CHỮ TRẮNG - BÓNG ĐEN */
    .a-btn div.stButton > button, .a-btn div.stDownloadButton > button {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 60px !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.5) !important; /* BÓNG ĐEN RÕ NÉT */
        transition: all 0.3s ease;
    }
    .a-btn div.stButton > button:hover {
        background-color: #e61e3a !important;
        transform: scale(1.02);
    }

    /* PROGRESS BAR & TRẠNG THÁI */
    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    .status-card {
        text-align: center;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 25px;
        font-weight: 700;
        border: 1px dashed #ff2442;
    }

    /* CĂN CHỈNH LAYOUT */
    .main-container { max-width: 900px; margin: 0 auto; }
    .footer-text {
        text-align: center;
        padding: 50px;
        color: #888 !important;
        font-size: 14px;
        margin-top: 80px;
        border-top: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. HIỂN THỊ BRAND TAG
st.markdown("<div class='brand-tag'>XHS Collector | Author Lập</div>", unsafe_allow_html=True)

# ==========================================
# 3. LOGIC HẬU TRƯỜNG (BACKEND)
# ==========================================
def extract_link(text):
    """Tự động quét link từ văn bản hỗn hợp"""
    pattern = r'https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def process_metadata(url, quality):
    """Gom luồng dữ liệu sạch qua yt-dlp"""
    mapping = {
        "Origin": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best"
    }
    ydl_opts = {
        'format': mapping.get(quality, 'best'),
        'quiet': True, 'no_warnings': True,
        'extract_flat': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# ==========================================
# 4. GIAO DIỆN TƯƠNG TÁC (FRONTEND)
# ==========================================
st.write("") # Padding cho header fixed
st.write("")

# Căn giữa khu vực nhập liệu
_, input_col, _ = st.columns([1, 3, 1])
with input_col:
    raw_content = st.text_area("✍️ Dán nội dung Xiaohongshu tại đây:", 
                               height=120, 
                               placeholder="Hệ thống tự động bắt link, anh không cần nhấn Enter...")

# TỰ ĐỘNG BẮT LINK
final_url = extract_link(raw_content)

# HIỂN THỊ TRẠNG THÁI
if not final_url:
    st.markdown("<div class='status-card' style='background-color: #fcfcfc; color: #999;'>⚪ Đang đợi anh dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-card' style='background-color: #fff5f6; color: #ff2442;'>🔴 Đã tìm thấy link! Mời anh chọn chất lượng tải.</div>", unsafe_allow_html=True)

# KHU VỰC NÚT CHẤT LƯỢNG (LUÔN HIỂN THỊ)
st.markdown("<div class='q-btn'>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

selected_q = None
locked = not bool(final_url)

if b1.button("ORIGIN", disabled=locked): selected_q = "Origin"
if b2.button("1080P", disabled=locked): selected_q = "1080p"
if b3.button("720P", disabled=locked): selected_q = "720p"
if b4.button("480P", disabled=locked): selected_q = "480p"
st.markdown("</div>", unsafe_allow_html=True)

# XỬ LÝ SAU KHI CHỌN CHẤT LƯỢNG
if selected_q and final_url:
    # Progress Bar thẩm mỹ
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        progress = st.progress(0)
        status_text = st.empty()
        for percent in range(1, 101):
            time.sleep(0.005)
            progress.progress(percent)
            status_text.markdown(f"<p style='text-align:center;'>Đang gom luồng {selected_q}... {percent}%</p>", unsafe_allow_html=True)

    try:
        # Lấy dữ liệu
        info = process_metadata(final_url, selected_q)
        st.divider()

        # HIỂN THỊ KẾT QUẢ
        res_left, res_right = st.columns([1, 1.3])
        
        with res_left:
            st.image(info.get('thumbnail'), caption="Ảnh bìa tư liệu", use_container_width=True)
        
        with res_right:
            st.markdown(f"### 📋 Chi tiết bản ghi")
            st.write(f"**Tác giả:** {info.get('uploader')}")
            st.write(f"**Tiêu đề:** {info.get('title')}")
            
            # NÚT TẢI VIDEO (BÓNG ĐEN)
            st.markdown("<div class='a-btn'>", unsafe_allow_html=True)
            st.link_button("📥 TẢI XUỐNG VIDEO NGAY", info.get('url'), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # PHẦN VĂN BẢN
        st.markdown("### 🖋️ Nội dung mô tả")
        st.info(info.get('description', 'Không có nội dung chữ.'))
        
        # NÚT LƯU VĂN BẢN (BÓNG ĐEN)
        st.markdown("<div class='a-btn'>", unsafe_allow_html=True)
        txt_out = f"NGUỒN: Xiaohongshu\nTÁC GIẢ: {info.get('uploader')}\n\nNỘI DUNG:\n{info.get('description')}"
        st.download_button("💾 LƯU FILE VĂN BẢN (.TXT)", txt_out, file_name=f"TuLieu_Lap_{info.get('id')}.txt")
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Có lỗi xảy ra trong quá trình gom luồng: {e}")

# CHÂN TRANG
st.markdown("<div class='footer-text'>Thiết kế riêng cho Nhà văn Lập | 2026 Edition<br>Dữ liệu được xử lý từ Rednote/Xiaohongshu</div>", unsafe_allow_html=True)
