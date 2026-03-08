import streamlit as st
import yt_dlp
import re
import os
import time

# --- CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="XHS Collector - Author Lập", layout="wide")

# CSS Tùy chỉnh: Nền caro đỏ, Title góc trái, Nút dầy 900, Bóng đổ đa lớp
st.markdown("""
    <style>
    /* Nền caro sọc đỏ đặc trưng */
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #1a1a1a !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Thu nhỏ tên ứng dụng vào góc trái */
    .brand-tag {
        position: fixed;
        top: 10px;
        left: 10px;
        font-size: 14px;
        font-weight: 800;
        color: #ff2442;
        background: rgba(255, 255, 255, 0.9);
        padding: 5px 12px;
        border-radius: 6px;
        border-left: 4px solid #ff2442;
        z-index: 1000;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Thiết kế 4 nút bấm chất lượng: Thân trắng, chữ đỏ, bóng hồng 30%, FONT DẦY 900 */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #ff2442 !important;
        border: 2px solid #ff2442 !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 52px !important;
        font-size: 16px !important;
        font-weight: 900 !important; /* Độ dầy tối đa cho font chữ */
        transition: all 0.2s ease;
        box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important;
    }
    
    div.stButton > button:hover {
        transform: translate(-2px, -2px);
        box-shadow: 8px 8px 20px rgba(255, 36, 66, 0.4) !important;
        background-color: #fff5f6 !important;
    }

    /* Thiết kế nút hành động: Nền hồng, chữ trắng, bóng đen */
    div.stButton > button[data-baseweb="button"], .stDownloadButton > button {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.5) !important;
        font-weight: 800 !important;
    }

    div.stButton > button[data-baseweb="button"]:hover, .stDownloadButton > button:hover {
        background-color: #e61e3a !important;
        color: #ffffff !important;
    }

    /* Trạng thái nút bị vô hiệu hóa */
    div.stButton > button:disabled {
        opacity: 0.4;
        border: 2px solid #dddddd !important;
        color: #999999 !important;
        box-shadow: none !important;
    }

    .stProgress > div > div > div > div {
        background-color: #ff2442 !important;
    }

    .centered-text { text-align: center; }
    
    .status-msg {
        text-align: center;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 25px;
        font-weight: 600;
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

# Tên ứng dụng ở góc trái (Brand Tag)
st.markdown("<div class='brand-tag'>XHS Collector | Tác giả Lập</div>", unsafe_allow_html=True)

# --- HÀM XỬ LÝ DỮ LIỆU ---
def extract_url(text):
    pattern = r'https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def get_video_data(url, q_key):
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
st.write("") # Tạo khoảng trống cho brand tag

# Căn giữa khu vực nhập liệu
_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc link vào đây:", 
                            height=100, 
                            placeholder="Hệ thống tự động nhận diện link...")

target_link = extract_url(raw_input)

# Hiển thị tình trạng link
if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Hãy chọn chất lượng để tải về.</div>", unsafe_allow_html=True)

# 4 Nút chất lượng luôn hiển thị
st.markdown("<p class='centered-text' style='margin-bottom: 10px; font-weight: bold;'>CHỌN CHẤT LƯỢNG:</p>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

selected_quality = None
is_disabled = not bool(target_link)

if b1.button("ORIGIN", disabled=is_disabled): selected_quality = "Origin"
if b2.button("1080P", disabled=is_disabled): selected_quality = "1080p"
if b3.button("720P", disabled=is_disabled): selected_quality = "720p"
if b4.button("480P", disabled=is_disabled): selected_quality = "480p"

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
            
            # NÚT TẢI VIDEO XUỐNG
            st.link_button("📥 TẢI XUỐNG VIDEO NGAY", data.get('url'), use_container_width=True)

        st.markdown("### 📝 Nội dung mô tả bài viết")
        st.info(data.get('description', 'Không có mô tả chữ.'))
        
        # NÚT LƯU VĂN BẢN
        meta_txt = f"TÁC GIẢ: {data.get('uploader')}\nTIÊU ĐỀ: {data.get('title')}\n\nNỘI DUNG:\n{data.get('description')}"
        st.download_button("💾 LƯU FILE VĂN BẢN (.TXT)", meta_txt, file_name=f"TuLieu_Lap_{data.get('id')}.txt")

    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}")

# Chân trang khẳng định tác giả
st.markdown("""
    <div class='footer'>
        Hệ thống được thiết kế riêng cho mục đích nghiên cứu văn học của <b>Tác giả Lập</b>.<br>
        2026 Edition | Xiaohongshu-Rednote Collector
    </div>
    """, unsafe_allow_html=True)
