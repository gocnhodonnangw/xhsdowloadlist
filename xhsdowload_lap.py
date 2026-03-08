import streamlit as st
import yt_dlp
import re
import os
import tempfile
import requests
import json
import streamlit.components.v1 as components

# --- CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide")

# CSS Tùy chỉnh: Ép độ dày chữ tối đa (900) và màu trắng cho mọi lớp phần tử trong nút
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
    
    /* Thiết kế nút chọn chất lượng - Can thiệp sâu vào lớp chữ */
    div.stButton > button, div.stButton > button p, div.stButton > button span {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 16px !important; 
        font-weight: 900 !important;
        letter-spacing: 0.5px !important; 
        transition: all 0.2s ease;
    }
    
    div.stButton > button {
        width: 100% !important;
        height: 52px !important;
        box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important;
    }
    
    div.stButton > button:hover {
        transform: translate(-2px, -2px);
        box-shadow: 8px 8px 20px rgba(255, 36, 66, 0.4) !important;
        background-color: #e61e3a !important;
    }

    div.stButton > button:active {
        transform: translate(2px, 2px);
        box-shadow: 2px 2px 5px rgba(255, 36, 66, 0.3) !important;
    }

    div.stButton > button:disabled, div.stButton > button:disabled p {
        background-color: #cccccc !important;
        color: #ffffff !important;
        opacity: 0.8 !important;
        box-shadow: none !important;
    }

    /* Thiết kế nút tải xuống */
    div.stDownloadButton > button, div.stDownloadButton > button p, div.stDownloadButton > button span {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        font-size: 16px !important;
        font-weight: 900 !important;
        letter-spacing: 0.5px !important;
    }
    
    div.stDownloadButton > button {
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important;
    }

    div.stDownloadButton > button:hover {
        background-color: #e61e3a !important;
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
        font-weight: 600;
    }

    /* CSS làm mượt ảnh preview, chống bể viền */
    img {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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
st.markdown("""
    <div style="text-align: left; margin-bottom: 30px; padding-top: 10px;">
        <h2 style='color: #ff2442; margin-bottom: 0px; padding-bottom: 0px; font-weight: 900; font-size: 26px;'>Xiaohongshu - Rednote Collector</h2>
        <p style='font-size: 15px; color: #666 !important; margin-top: 2px;'>Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>
    </div>
""", unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'video_data' not in st.session_state:
    st.session_state.video_data = None
if 'video_file_path' not in st.session_state:
    st.session_state.video_file_path = None
if 'current_link' not in st.session_state:
    st.session_state.current_link = None
if 'thumbnail_bytes' not in st.session_state:
    st.session_state.thumbnail_bytes = None

# --- HÀM XỬ LÝ DỮ LIỆU ---
def extract_url(text):
    pattern = r'https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def download_video_to_temp(url, q_key, progress_bar, status_text):
    temp_dir = tempfile.gettempdir()
    outtmpl = os.path.join(temp_dir, '%(id)s.%(ext)s')
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0.0%')
            clean_percent = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).replace('%', '').strip()
            try:
                percent = float(clean_percent)
                progress_bar.progress(int(percent))
                status_text.markdown(f"<p style='text-align:center; color: #ff2442; font-weight: 700;'>Đang kéo luồng: {percent}%</p>", unsafe_allow_html=True)
            except ValueError:
                pass
        elif d['status'] == 'finished':
            progress_bar.progress(100)
            status_text.markdown("<p style='text-align:center; color: #ff2442; font-weight: 700;'>Đã tải xong, đang đóng gói file...</p>", unsafe_allow_html=True)

    q_map = {
        "Origin": "bestvideo[fps>30]+bestaudio/bestvideo+bestaudio/best", 
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best"
    }
    
    ydl_opts = {
        'format': q_map.get(q_key, 'best'),
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        expected_ext = 'mp4' if info.get('ext') != 'mp4' else info.get('ext', 'mp4')
        file_path = os.path.join(temp_dir, f"{info['id']}.{expected_ext}")
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

if target_link != st.session_state.current_link:
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    st.session_state.thumbnail_bytes = None
    st.session_state.current_link = target_link

if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ anh dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Anh hãy chọn chất lượng để hệ thống bắt đầu kéo dữ liệu.</div>", unsafe_allow_html=True)

st.markdown("<p class='centered-text' style='margin-bottom: 10px;'><b>Chọn chất lượng để gom luồng:</b></p>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

is_disabled = False if target_link else True

def process_and_download(quality):
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        progress_bar = st.progress(0)
        status_text = st.empty()
        try:
            info, path = download_video_to_temp(target_link, quality, progress_bar, status_text)
            st.session_state.video_data = info
            st.session_state.video_file_path = path
            
            # --- CƠ CHẾ LỌC ẢNH CHẤT LƯỢNG CAO NHẤT ---
            thumbnails = info.get('thumbnails', [])
            thumb_url = None
            if thumbnails:
                # Quét và tìm ảnh có diện tích (Dài x Rộng) lớn nhất
                try:
                    best_thumb = max(thumbnails, key=lambda x: (x.get('width') or 0) * (x.get('height') or 0))
                    thumb_url = best_thumb.get('url')
                except Exception:
                    thumb_url = thumbnails[-1].get('url') # Dự phòng lấy ảnh cuối cùng trong danh sách
            
            if not thumb_url:
                thumb_url = info.get('thumbnail') # Bước đường cùng mới dùng ảnh mặc định

            if thumb_url:
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    resp = requests.get(thumb_url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        st.session_state.thumbnail_bytes = resp.content
                except:
                    pass
            
            progress_bar.empty()
            status_text.empty()
        except Exception as e:
            st.error(f"Đã xảy ra lỗi trong quá trình kéo luồng: {e}")

if b1.button("ORIGIN", disabled=is_disabled): process_and_download("Origin")
if b2.button("BẢN 1080P", disabled=is_disabled): process_and_download("1080p")
if b3.button("BẢN 720P", disabled=is_disabled): process_and_download("720p")
if b4.button("BẢN 480P", disabled=is_disabled): process_and_download("480p")

# --- HIỂN THỊ KẾT QUẢ TỪ SESSION STATE ---
if st.session_state.video_data and st.session_state.video_file_path:
    data = st.session_state.video_data
    file_path = st.session_state.video_file_path
    
    st.divider()
    
    res_c1, res_c2 = st.columns([1, 1.4])
    with res_c1:
        if st.session_state.thumbnail_bytes:
            st.image(st.session_state.thumbnail_bytes, caption="Ảnh xem trước chất lượng cao", use_container_width=True)
            st.download_button(
                label="🖼️ TẢI ẢNH BÌA",
                data=st.session_state.thumbnail_bytes,
                file_name=f"Thumbnail_Lap_{data.get('id', 'xhs')}.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
        else:
            if data.get('thumbnail'):
                st.image(data.get('thumbnail'), caption="Ảnh xem trước tư liệu", use_container_width=True)
            else:
                st.info("Không có ảnh xem trước")

    with res_c2:
        st.subheader("📌 Chi tiết bản ghi")
        
        author_name = data.get('uploader') or data.get('creator') or data.get('channel') or data.get('user') or 'Chưa xác định'
        
        st.write(f"**Tác giả:** {author_name}")
        st.write(f"**Tiêu đề:** {data.get('title', 'N/A')}")
        st.write(f"**Độ phân giải:** {data.get('width', 'N/A')}x{data.get('height', 'N/A')} | **FPS:** {data.get('fps', 'N/A')}")
        
        if os.path.exists(file_path):
            with open(file_path, "rb") as video_file:
                st.download_button(
                    label="📥 TẢI XUỐNG VIDEO",
                    data=video_file,
                    file_name=f"TuLieu_Lap_{data.get('id', 'video')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
        else:
            st.error("Không tìm thấy file video trong bộ nhớ tạm. Hãy thử tải lại.")

    st.markdown("### 📝 Nội dung mô tả bài viết")
    description = data.get('description') or 'Không có mô tả chữ.'
    st.info(description)
    
    # Nút COPY VĂN BẢN (Sử dụng HTML/JS nhúng)
    meta_txt = f"TÁC GIẢ: {author_name}\nTIÊU ĐỀ: {data.get('title')}\n\nNỘI DUNG:\n{description}"
    safe_txt = json.dumps(meta_txt) 
    
    copy_html = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    body {{ margin: 0; padding: 0; background-color: transparent; }}
    button {{
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        width: 100% !important;
        height: 48px !important; 
        font-size: 16px !important;
        font-weight: 900 !important;
        letter-spacing: 0.5px !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
        cursor: pointer;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.2s ease !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    button:hover {{ background-color: #e61e3a !important; }}
    button:active {{ transform: translate(2px, 2px) !important; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3) !important; }}
    </style>
    <button id="cpy-btn" onclick='copyToClipboard()'>📋 COPY VĂN BẢN</button>
    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText({safe_txt}).then(function() {{
            const btn = document.getElementById('cpy-btn');
            btn.innerText = '✅ ĐÃ COPY THÀNH CÔNG';
            setTimeout(() => btn.innerText = '📋 COPY VĂN BẢN', 2000);
        }});
    }}
    </script>
    """
    components.html(copy_html, height=60)

# Chân trang
st.markdown("""
    <div class='footer'>
        Thiết kế riêng cho mục đích nghiên cứu văn học của <b>Tác giả Lập</b>.<br>
        2026 Edition | Xiaohongshu-Rednote Collector
    </div>
    """, unsafe_allow_html=True)
