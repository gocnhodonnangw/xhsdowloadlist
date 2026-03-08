import streamlit as st
import yt_dlp
import re
import os
import time

# --- CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide")

# CSS Tùy chỉnh: Giao diện sáng, Nút đỏ Xiaohongshu, Progress Bar
st.markdown("""
    <style>
    /* Nền trắng và chữ đen rõ nét */
    .stApp {
        background-color: #ffffff;
    }
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #1a1a1a !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    /* Thiết kế 4 nút bấm chất lượng dàn hàng ngang */
    div.stButton > button {
        background-color: #ff2442 !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        width: 100% !important;
        height: 52px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(255, 36, 66, 0.15);
    }
    div.stButton > button:hover {
        background-color: #e61e3a !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 36, 66, 0.25);
        color: white !important;
    }
    /* Thanh tiến trình màu đỏ Xiaohongshu */
    .stProgress > div > div > div > div {
        background-color: #ff2442 !important;
    }
    /* Khung nhập liệu vát tròn */
    .stTextArea textarea {
        background-color: #f9f9f9 !important;
        border: 2px solid #eeeeee !important;
        border-radius: 12px !important;
        color: #1a1a1a !important;
    }
    /* Chân trang cá nhân hóa */
    .footer {
        text-align: center;
        padding: 40px;
        color: #999 !important;
        font-size: 14px;
        border-top: 1px solid #f0f0f0;
        margin-top: 60px;
    }
    </style>
    """, unsafe_allow_html=True)

# Tiêu đề khẳng định tác giả
st.markdown("<h1 style='text-align: center; color: #ff2442; margin-bottom: 0;'>Xiaohongshu - Rednote Collector</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1em; color: #555 !important;'>Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>", unsafe_allow_html=True)

# --- HÀM XỬ LÝ DỮ LIỆU ---
def extract_url(text):
    # Hỗ trợ cả link rút gọn và link đầy đủ
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
    ydl_opts = {
        'format': q_map.get(q_key, 'best'),
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# --- GIAO DIỆN TƯƠNG TÁC ---
st.divider()
raw_text = st.text_area("Dán nội dung bài viết hoặc link từ App Xiaohongshu vào đây:", 
                        height=130, 
                        placeholder="Hệ thống sẽ tự động lọc link cho anh...")

target_url = extract_url(raw_text)

if target_url:
    st.markdown("### 🛠️ Chọn chất lượng để bắt đầu thu thập:")
    
    # 4 Nút bấm dàn hàng ngang
    col1, col2, col3, col4 = st.columns(4)
    selected_q = None
    
    if col1.button("💎 CHẤT LƯỢNG GỐC"): selected_q = "Origin"
    if col2.button("✨ BẢN 1080P"): selected_q = "1080p"
    if col3.button("🎬 BẢN 720P"): selected_q = "720p"
    if col4.button("📱 BẢN 480P"): selected_q = "480p"

    if selected_q:
        # THANH TIẾN TRÌNH
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(1, 101):
            time.sleep(0.01) # Hiệu ứng chạy thanh tiến trình
            progress_bar.progress(i)
            status_text.text(f"Đang xử lý dữ liệu {selected_q}: {i}%")
            if i == 100:
                status_text.text("✅ Đã hoàn tất gom luồng!")

        try:
            info = get_data(target_url, selected_q)
            st.divider()
            
            # Hiển thị Preview
            c1, c2 = st.columns([1, 1.4])
            
            with c1:
                st.image(info.get('thumbnail'), caption="Ảnh bìa tư liệu", use_container_width=True)
            
            with c2:
                st.subheader("📋 Chi tiết bản ghi")
                st.write(f"**Tác giả:** {info.get('uploader', 'N/A')}")
                st.write(f"**Tiêu đề:** {info.get('title', 'N/A')}")
                
                # NÚT TẢI XUỐNG VIDEO
                st.link_button("📥 TẢI XUỐNG VIDEO NGAY", info.get('url'), use_container_width=True)
                st.caption("*(Lưu ý: Nếu video tự mở, hãy nhấn chuột phải chọn 'Lưu video thành...')*")

            # Phần nội dung mô tả cho nhà văn
            st.markdown("### 📝 Nội dung mô tả")
            st.info(info.get('description', 'Không có mô tả chữ.'))
            
            # Nút tải file Text
            txt_data = f"TÁC GIẢ: {info.get('uploader')}\nTIÊU ĐỀ: {info.get('title')}\n\nNỘI DUNG:\n{info.get('description')}"
            st.download_button("💾 LƯU FILE VĂN BẢN (.TXT)", txt_data, file_name=f"TuLieu_Lap_{info.get('id')}.txt")

        except Exception as e:
            st.error(f"Lỗi kỹ thuật: {e}")
else:
    if raw_text:
        st.warning("⚠️ Không tìm thấy đường dẫn. Anh vui lòng kiểm tra lại nội dung dán.")

# Chân trang khẳng định tác quyền
st.markdown("""
    <div class='footer'>
        Dự án thiết kế riêng cho mục đích nghiên cứu văn học của <b>Tác giả Lập</b>.<br>
        Bản quyền dữ liệu thuộc về Xiaohongshu-Rednote | 2026 Edition
    </div>
    """, unsafe_allow_html=True)
