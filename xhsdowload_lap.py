import streamlit as st
import yt_dlp
import re
import os

# --- CẤU HÌNH GIAO DIỆN SÁNG ---
st.set_page_config(page_title="XHS Downloader - Author Lập", page_icon="📖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, p, span, label { color: #1a1a1a !important; font-family: 'Segoe UI', sans-serif; }
    
    div.stButton > button {
        background-color: #ff2442 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100% !important;
        height: 55px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #d11d35 !important;
        transform: translateY(-2px);
    }
    
    .stTextArea textarea {
        background-color: #f8f9fa !important;
        border: 2px solid #eeeeee !important;
        border-radius: 10px !important;
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #ff2442;'>📕 Xiaohongshu - Rednote Collector</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em;'>Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>", unsafe_allow_html=True)

# --- HÀM XỬ LÝ (BACK-END) ---
def fetch_data(url, quality_key):
    quality_map = {
        "Origin": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best"
    }
    ydl_opts = {
        'format': quality_map.get(quality_key, 'best'),
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# --- GIAO DIỆN NGƯỜI DÙNG ---
st.divider()
raw_input = st.text_area("Dán nội dung hoặc link rút gọn Xiaohongshu vào đây:", 
                         height=120, 
                         placeholder="Hệ thống đã hỗ trợ link rút gọn xhslink.com...")

# BỘ LỌC NÂNG CẤP: Hỗ trợ cả link đầy đủ và link rút gọn (xhslink.com)
url_pattern = r'https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+'
url_match = re.search(url_pattern, raw_input)
target_url = url_match.group(0) if url_match else None

if target_url:
    st.markdown("### 🛠️ Bước 1: Chọn chất lượng để bắt đầu lấy tư liệu")
    
    col1, col2, col3, col4 = st.columns(4)
    q_selected = None
    
    if col1.button("💎 Chất lượng GỐC"): q_selected = "Origin"
    if col2.button("✨ Bản 1080p"): q_selected = "1080p"
    if col3.button("🎬 Bản 720p"): q_selected = "720p"
    if col4.button("📱 Bản 480p"): q_selected = "480p"

    if q_selected:
        with st.spinner(f"Đang xử lý dữ liệu từ {target_url}..."):
            try:
                data = fetch_data(target_url, q_selected)
                st.divider()
                
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    st.image(data.get('thumbnail'), caption="Ảnh xem trước tư liệu", use_container_width=True)
                with c2:
                    st.subheader("📌 Chi tiết bản ghi")
                    st.write(f"**Người đăng:** {data.get('uploader')}")
                    st.write(f"**Tiêu đề:** {data.get('title')}")
                    st.link_button("📥 TẢI VIDEO XUỐNG", data.get('url'), use_container_width=True)

                st.markdown("### 🖋️ Nội dung mô tả")
                st.info(data.get('description', 'Không có mô tả chữ.'))
                
                meta_content = f"TÁC GIẢ: {data.get('uploader')}\nTIÊU ĐỀ: {data.get('title')}\n\nNỘI DUNG:\n{data.get('description')}"
                st.download_button("💾 Lưu file Text (.txt)", meta_content, file_name=f"TuLieu_Lap_{data.get('id')}.txt")

            except Exception as e:
                st.error(f"Lỗi: {e}")
else:
    if raw_input:
        st.warning("⚠️ Hệ thống không tìm thấy đường dẫn hợp lệ. Anh vui lòng kiểm tra lại nội dung đã dán.")

st.markdown(f"<div style='text-align: center; padding: 40px; color: #888; border-top: 1px solid #eee; margin-top: 50px;'>Dự án thiết kế riêng cho kho lưu trữ của <b>Tác giả Lập</b><br>Cập nhật lần cuối: 08/03/2026 | 2026 Edition</div>", unsafe_allow_html=True)
