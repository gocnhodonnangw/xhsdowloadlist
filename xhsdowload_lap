import streamlit as st
import yt_dlp
import re
import os
from PIL import Image

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="XHS Downloader - Author Lập", page_icon="📖", layout="wide")

# CSS Tùy chỉnh: Giao diện sáng, nút bấm đỏ Xiaohongshu, khẳng định tác giả
st.markdown("""
    <style>
    /* Nền trắng và chữ đen chuyên nghiệp */
    .stApp {
        background-color: #ffffff;
    }
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #1a1a1a !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Nút bấm chất lượng: Màu đỏ đặc trưng Xiaohongshu */
    div.stButton > button {
        background-color: #ff2442 !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        height: 50px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #d11d35 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        color: white !important;
    }
    /* Khung nhập liệu sáng sủa */
    .stTextArea textarea {
        background-color: #fcfcfc !important;
        color: #1a1a1a !important;
        border: 2px solid #eeeeee !important;
        border-radius: 10px !important;
    }
    /* Chân trang khẳng định tác quyền */
    .author-footer {
        text-align: center;
        padding: 30px;
        color: #888888 !important;
        font-size: 14px;
        border-top: 1px solid #f0f0f0;
        margin-top: 60px;
    }
    </style>
    """, unsafe_allow_html=True)

# Tiêu đề chính
st.markdown("<h1 style='text-align: center; color: #ff2442 !important;'>📕 Xiaohongshu - Rednote Collector</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em;'>Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>", unsafe_allow_html=True)

# --- HÀM XỬ LÝ KỸ THUẬT ---
def extract_clean_url(text):
    """Lọc link từ nội dung copy lộn xộn"""
    pattern = r'https://www\.xiaohongshu\.com/(?:discovery/item/|explore/)[a-zA-Z0-9?=&_%-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def fetch_data(url, quality_key):
    """Sử dụng yt-dlp để lấy luồng video sạch và metadata"""
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

# --- GIAO DIỆN TƯƠNG TÁC ---
st.divider()
raw_input = st.text_area("Dán link bài viết hoặc nội dung copy từ App Xiaohongshu vào đây:", 
                         height=130, 
                         placeholder="Ví dụ: 20 【开车返工新思路...】 https://www.xiaohongshu.com/...")

target_url = extract_clean_url(raw_input)

if target_url:
    st.markdown("### 🛠️ Bước 1: Chọn chất lượng tải xuống")
    st.caption("Mọi tùy chọn đều hỗ trợ lấy Thumbnail và Nội dung chữ đi kèm.")
    
    # Hàng nút bấm chất lượng riêng biệt
    col1, col2, col3, col4 = st.columns(4)
    q_selected = None
    
    if col1.button("💎 Chất lượng Gốc"): q_selected = "Origin"
    if col2.button("✨ Bản 1080p"): q_selected = "1080p"
    if col3.button("🎬 Bản 720p"): q_selected = "720p"
    if col4.button("📱 Bản 480p"): q_selected = "480p"

    if q_selected:
        with st.spinner(f"Nhà văn Lập đang trích xuất dữ liệu {q_selected}..."):
            try:
                data = fetch_data(target_url, q_selected)
                
                st.divider()
                # --- HIỂN THỊ KẾT QUẢ (PREVIEW) ---
                res_col1, res_col2 = st.columns([1, 1.3])
                
                with res_col1:
                    st.image(data.get('thumbnail'), caption="Ảnh bìa (Preview)", use_container_width=True)
                
                with res_col2:
                    st.subheader("📄 Thông tin tư liệu")
                    st.write(f"**Người đăng:** {data.get('uploader', 'N/A')}")
                    st.write(f"**Tiêu đề bài:** {data.get('title', 'N/A')}")
                    
                    # Nút tải Video
                    st.link_button("📥 TẢI VIDEO NGAY", data.get('url'), use_container_width=True)
                    st.caption("*(Lưu ý: Nếu video tự mở, hãy nhấn chuột phải và chọn 'Lưu video thành...')*")

                # --- NỘI DUNG VĂN BẢN ---
                st.markdown("### 🖋️ Nội dung mô tả chi tiết")
                content_box = f"""
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #ff2442; color: #333;">
                    {data.get('description', 'Không có nội dung văn bản.')}
                </div>
                """
                st.markdown(content_box, unsafe_allow_html=True)
                
                # Nút tải File Text
                full_text = f"NGUỒN: Xiaohongshu\nTÁC GIẢ: {data.get('uploader')}\nTIÊU ĐỀ: {data.get('title')}\n\nNỘI DUNG:\n{data.get('description')}"
                st.download_button(
                    label="💾 Lưu nội dung vào kho bản thảo (.txt)",
                    data=full_text,
                    file_name=f"TuLieu_Lap_{data.get('id')}.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"Đã xảy ra lỗi kỹ thuật: {e}")
else:
    if raw_input:
        st.warning("⚠️ Hệ thống không tìm thấy đường dẫn hợp lệ. Anh vui lòng kiểm tra lại nội dung đã dán.")

# Footer khẳng định thương hiệu
st.markdown(f"""
    <div class="author-footer">
        Dự án được phát triển riêng cho kho lưu trữ của <b>Nhà văn Lập</b>.<br>
        Cập nhật lần cuối: {os.popen('date +"%d/%m/%Y"').read().strip()} | 2026 Edition
    </div>
    """, unsafe_allow_html=True)
