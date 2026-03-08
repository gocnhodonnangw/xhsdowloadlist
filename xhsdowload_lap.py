import streamlit as st
import yt_dlp
import re
import os
import time

# --- CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide")

# CSS Tùy chỉnh: Nền caro đỏ, nút trắng bóng hồng, nút hồng bóng đen
st.markdown("""
    <style>
    /* Nền caro sọc đỏ rực rỡ */
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #1a1a1a !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Thiết kế 4 nút bấm chất lượng: Thân trắng, chữ đỏ, bóng hồng 30% */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #ff2442 !important;
        border: 2px solid #ff2442 !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 52px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease;
        box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important;
    }
    
    div.stButton > button:hover {
        transform: translate(-2px, -2px);
        box-shadow: 8px 8px 20px rgba(255, 36, 66, 0.4) !important;
        background-color: #fff5f6 !important;
    }

    div.stButton > button:active {
        transform: translate(2px, 2px);
        box-shadow: 2px 2px 5px rgba(255, 36, 66, 0.3) !important;
    }

    /* Trạng thái nút bị vô hiệu hóa */
    div.stButton > button:disabled {
        opacity: 0.4;
        border: 2px solid #dddddd !important;
        color: #999999 !important;
        box-shadow: none !important;
    }

    /* Thiết kế nút hành động: Nền hồng, chữ trắng, bóng đen */
    div.stButton > button[data-baseweb="button"] {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.5) !important;
    }

    div.stButton > button[data-baseweb="button"]:hover {
        background-color: #e61e3a !important;
        color: #ffffff !important;
    }

    /* Thanh tiến trình màu đỏ Xiaohongshu */
    .stProgress > div > div > div > div {
        background-color: #ff2442 !important;
    }

    /* Căn giữa các thành phần văn bản */
    .centered-text {
        text-align: center;
    }
    
    .status-msg {
        text-align: center;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 25px;
        font-weight: 500;
    }
    
    .footer {
        text-align: center;
        padding: 40px;
        color: #999 !important;
        font-size: 14px;
        border-top: 1px solid #f0f0f0;
        margin-top: 60px;
        background-color: rgba(255, 255, 255, 0.8);
    }
    </style>
    """, unsafe_allow_html=True)

# Tiêu đề khẳng định tác quyền
st.markdown("<h1 class='centered-text' style='color: #ff2442; margin-bottom: 0;'>Xiaohongshu - Rednote Collector</h1>", unsafe_allow_html=True)
st.markdown("<p class='centered-text' style='font-size: 1.1em; color: #666 !important;'>Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>", unsafe_allow_html=True)

# --- HÀM XỬ LÝ DỮ LIỆU ---
def extract_url(text):
    """Lọc link sạch từ nội dung dán vào"""
    pattern = r'https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def get_video_data(url, q_key):
    """Gom luồng dữ liệu thông qua yt-dlp"""
    q_map = {
        "Origin": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best"
    }
    ydl_opts = {
        'format': q_map.get(q_key, 'best'),
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# --- GIAO DIỆN TƯƠNG TÁC ---
st.divider()

# Căn giữa khu vực nhập liệu
_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc link vào đây:", 
                            height=100, 
                            placeholder="Anh chỉ cần dán, tôi sẽ làm phần còn lại...")

target_link = extract_url(raw_input)

# Hiển thị tình trạng link hiện tại
if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ anh dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Anh hãy chọn chất lượng để tải về.</div>", unsafe_allow_html=True)

# 4 Nút chất lượng luôn hiển thị
st.markdown("<p class='centered-text' style='margin-bottom: 10px;'><b>Chọn chất lượng để gom luồng:</b></p>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

selected_quality = None
# Vô hiệu hóa nút nếu chưa tìm thấy link
is_disabled = False if target_link else True

if b1.button("CHẤT LƯỢNG GỐC", disabled=is_disabled): selected_quality = "Origin"
if b2.button("BẢN 1080P", disabled=is_disabled): selected_quality = "1080p"
if b3.button("BẢN 720P", disabled=is_disabled): selected_quality = "720p"
if b4.button("BẢN 480P", disabled=is_disabled): selected_quality = "480p"

# Xử lý sau khi nhấn nút
if selected_quality and target_link:
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        bar = st.progress(0)
        status = st.empty()
        for i in range(1, 101):
            time.sleep(0.01)
            bar.progress(i)
            status.markdown(f"<p style='text-align:center;'>Đang gom luồng {selected_quality}: {i}%</p>", unsafe_allow_html=True)

    try:
        data = get_video_data(target_link, selected_quality)
        st.divider()
        
        # Kết quả hiển thị (Preview & Metadata)
        res_c1, res_c2 = st.columns([1, 1.4])
        with res_c1:
            st.image(data.get('thumbnail'), caption="Ảnh xem trước tư liệu", use_container_width=True)
        with res_c2:
            st.subheader("📌 Chi tiết bản ghi")
            st.write(f"**Tác giả:** {data.get('uploader', 'N/A')}")
            st.write(f"**Tiêu đề:** {data.get('title', 'N/A')}")
            
            # NÚT TẢI VIDEO XUỐNG - Giao diện mới (Hồng, chữ trắng, bóng đen)
            st.link_button("📥 TẢI XUỐNG VIDEO NGAY", data.get('url'), use_container_width=True)

        # Nội dung văn bản
        st.markdown("### 📝 Nội dung mô tả bài viết")
        st.info(data.get('description', 'Không có mô tả chữ.'))
        
        # NÚT LƯU VĂN BẢN - Giao diện mới (Hồng, chữ trắng, bóng đen)
        meta_txt = f"TÁC GIẢ: {data.get('uploader')}\nTIÊU ĐỀ: {data.get('title')}\n\nNỘI DUNG:\n{data.get('description')}"
        st.download_button("💾 LƯU FILE VĂN BẢN (.TXT)", meta_txt, file_name=f"TuLieu_Lap_{data.get('id')}.txt")

    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}")

# Chân trang khẳng định tác giả
st.markdown("""
    <div class='footer'>
        Thiết kế riêng cho mục đích nghiên cứu văn học của <b>Tác giả Lập</b>.<br>
        2026 Edition | Xiaohongshu-Rednote Collector
    </div>
    """, unsafe_allow_html=True)
