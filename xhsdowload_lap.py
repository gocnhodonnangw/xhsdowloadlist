import streamlit as st
import yt_dlp
import re
import os
import time
import tempfile

# --- CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide")

# CSS Tùy chỉnh
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #1a1a1a !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
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

    div.stButton > button:disabled {
        opacity: 0.4;
        border: 2px solid #dddddd !important;
        color: #999999 !important;
        box-shadow: none !important;
    }

    div.stDownloadButton > button {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.5) !important;
    }

    div.stDownloadButton > button:hover {
        background-color: #e61e3a !important;
        color: #ffffff !important;
        border: none !important;
    }

    .stProgress > div > div > div > div {
        background-color: #ff2442 !important;
    }

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

# Tiêu đề
st.markdown("<h1 class='centered-text' style='color: #ff2442; margin-bottom: 0;'>Xiaohongshu - Rednote Collector</h1>", unsafe_allow_html=True)
st.markdown("<p class='centered-text' style='font-size: 1.1em; color: #666 !important;'>Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>", unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'video_data' not in st.session_state:
    st.session_state.video_data = None
if 'video_file_path' not in st.session_state:
    st.session_state.video_file_path = None
if 'current_link' not in st.session_state:
    st.session_state.current_link = None

# --- HÀM XỬ LÝ DỮ LIỆU ---
def extract_url(text):
    pattern = r'https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def download_video_to_temp(url, q_key):
    """Gom luồng và tải trực tiếp video về bộ nhớ tạm"""
    temp_dir = tempfile.gettempdir()
    outtmpl = os.path.join(temp_dir, '%(id)s.%(ext)s')
    
    q_map = {
        "Origin": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best"
    }
    
    ydl_opts = {
        'format': q_map.get(q_key, 'best'),
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4', # Đảm bảo xuất ra định dạng MP4 thân thiện
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Tải video thật về máy chủ (download=True) thay vì chỉ lấy link
        info = ydl.extract_info(url, download=True)
        
        # Xác định đường dẫn file đã tải
        expected_ext = 'mp4' if info.get('ext') != 'mp4' else info.get('ext', 'mp4')
        file_path = os.path.join(temp_dir, f"{info['id']}.{expected_ext}")
        
        # Dự phòng trường hợp yt-dlp không đổi tên file thành công
        if not os.path.exists(file_path):
            file_path = ydl.prepare_filename(info)
            
        return info, file_path

# --- GIAO DIỆN TƯƠNG TÁC ---
st.divider()

_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc link vào đây:", 
                             height=100, 
                             placeholder="Anh chỉ cần dán, tôi sẽ làm phần còn lại...")

target_link = extract_url(raw_input)

# Nếu dán link mới, reset lại dữ liệu cũ trên màn hình
if target_link != st.session_state.current_link:
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    st.session_state.current_link = target_link

if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ anh dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Anh hãy chọn chất lượng để hệ thống bắt đầu kéo dữ liệu.</div>", unsafe_allow_html=True)

st.markdown("<p class='centered-text' style='margin-bottom: 10px;'><b>Chọn chất lượng để gom luồng:</b></p>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

is_disabled = False if target_link else True

# Xử lý khi nhấn nút tải
def process_and_download(quality):
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        with st.spinner(f"Đang kéo luồng {quality} về kho lưu trữ, anh Lập đợi một chút nhé..."):
            try:
                info, path = download_video_to_temp(target_link, quality)
                st.session_state.video_data = info
                st.session_state.video_file_path = path
            except Exception as e:
                st.error(f"Đã xảy ra lỗi trong quá trình kéo luồng: {e}")

if b1.button("CHẤT LƯỢNG GỐC", disabled=is_disabled): process_and_download("Origin")
if b2.button("BẢN 1080P", disabled=is_disabled): process_and_download("1080p")
if b3.button("BẢN 720P", disabled=is_disabled): process_and_download("720p")
if b4.button("BẢN 480P", disabled=is_disabled): process_and_download("480p")

# --- HIỂN THỊ KẾT QUẢ TỪ SESSION STATE ---
if st.session_state.video_data and st.session_state.video_file_path:
    data = st.session_state.video_data
    file_path = st.session_state.video_file_path
    
    st.divider()
    
    # Kết quả hiển thị
    res_c1, res_c2 = st.columns([1, 1.4])
    with res_c1:
        st.image(data.get('thumbnail'), caption="Ảnh xem trước tư liệu", use_container_width=True)
    with res_c2:
        st.subheader("📌 Chi tiết bản ghi")
        st.write(f"**Tác giả:** {data.get('uploader', 'N/A')}")
        st.write(f"**Tiêu đề:** {data.get('title', 'N/A')}")
        
        # NÚT TẢI VIDEO XUỐNG MÁY TÍNH
        if os.path.exists(file_path):
            with open(file_path, "rb") as video_file:
                st.download_button(
                    label="📥 TẢI XUỐNG VIDEO (.MP4)",
                    data=video_file,
                    file_name=f"TuLieu_Lap_{data.get('id', 'video')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
        else:
            st.error("Không tìm thấy file video trong bộ nhớ tạm. Hãy thử tải lại.")

    # Nội dung văn bản
    st.markdown("### 📝 Nội dung mô tả bài viết")
    description = data.get('description') or 'Không có mô tả chữ.'
    st.info(description)
    
    # NÚT LƯU VĂN BẢN
    meta_txt = f"TÁC GIẢ: {data.get('uploader')}\nTIÊU ĐỀ: {data.get('title')}\n\nNỘI DUNG:\n{description}"
    st.download_button(
        label="💾 LƯU FILE VĂN BẢN (.TXT)", 
        data=meta_txt, 
        file_name=f"TuLieu_Lap_{data.get('id', 'xhs')}.txt",
        use_container_width=True
    )

# Chân trang
st.markdown("""
    <div class='footer'>
        Thiết kế riêng cho mục đích nghiên cứu văn học của <b>Tác giả Lập</b>.<br>
        2026 Edition | Xiaohongshu-Rednote Collector
    </div>
    """, unsafe_allow_html=True)
