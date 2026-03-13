import streamlit as st
import yt_dlp
import re
import os
import tempfile
import requests
import json
import html
import time
import shutil
import streamlit.components.v1 as components

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide")

APP_TEMP_DIR = os.path.join(tempfile.gettempdir(), 'XHS_Collector_Workspace')
if not os.path.exists(APP_TEMP_DIR):
    os.makedirs(APP_TEMP_DIR)

# CSS Tùy chỉnh
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }
    h1, h2, h3, p, span, label, .stMarkdown { color: #1a1a1a !important; font-family: 'Inter', 'Segoe UI', sans-serif; }
    
    div.stButton > button, div.stButton > button p, div.stButton > button span {
        background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
        border-radius: 12px !important; font-size: 16px !important; font-weight: 900 !important;
        letter-spacing: 0.5px !important; transition: all 0.2s ease;
    }
    div.stButton > button { width: 100% !important; height: 52px !important; box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important; }
    div.stButton > button:hover { transform: translate(-2px, -2px); box-shadow: 8px 8px 20px rgba(255, 36, 66, 0.4) !important; background-color: #e61e3a !important; }
    div.stButton > button:active { transform: translate(2px, 2px); box-shadow: 2px 2px 5px rgba(255, 36, 66, 0.3) !important; }
    div.stButton > button:disabled, div.stButton > button:disabled p { background-color: #cccccc !important; color: #ffffff !important; opacity: 0.8 !important; box-shadow: none !important; }

    div.stDownloadButton > button, div.stDownloadButton > button p, div.stDownloadButton > button span {
        background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
        font-size: 16px !important; font-weight: 900 !important; letter-spacing: 0.5px !important;
    }
    div.stDownloadButton > button { box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important; width: 100% !important; }
    div.stDownloadButton > button:hover { background-color: #e61e3a !important; }

    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    .centered-text { text-align: center; }
    .status-msg { text-align: center; padding: 12px; border-radius: 10px; margin-bottom: 25px; font-weight: 600; }
    img { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .footer { text-align: center; padding: 40px; color: #999 !important; font-size: 14px; border-top: 1px solid #f0f0f0; margin-top: 60px; background-color: rgba(255, 255, 255, 0.8); }
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI ---
if 'video_data' not in st.session_state: st.session_state.video_data = None
if 'video_file_path' not in st.session_state: st.session_state.video_file_path = None
if 'current_link' not in st.session_state: st.session_state.current_link = None
if 'thumbnail_bytes' not in st.session_state: st.session_state.thumbnail_bytes = None
if 'author_name' not in st.session_state: st.session_state.author_name = "Chưa xác định"
if 'user_agent' not in st.session_state: st.session_state.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- TIÊU ĐỀ ---
st.markdown("""
    <div style="text-align: left; margin-bottom: 20px; padding-top: 10px;">
        <h2 style='color: #ff2442; margin-bottom: 0px; padding-bottom: 0px; font-weight: 900; font-size: 26px;'>Xiaohongshu - Rednote Collector</h2>
        <p style='font-size: 15px; color: #666 !important; margin-top: 2px;'>Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>
    </div>
""", unsafe_allow_html=True)
st.divider()

def nuke_cache():
    """Hàm hủy diệt file tạm - Xóa sạch không thương tiếc"""
    try:
        for filename in os.listdir(APP_TEMP_DIR):
            file_path = os.path.join(APP_TEMP_DIR, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path): os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
    except: pass

def extract_url(text):
    pattern = r'(?:https?://(?:www\.xiaohongshu\.com/(?:discovery/item/|explore/)|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+|https?://[^\s]+\.m3u8[^\s]*)'
    match = re.search(pattern, text)
    return match.group(0) if match else None

# --- LUỒNG XỬ LÝ CHÍNH (VIDEO) ---
def download_video_to_temp(url, q_key, progress_bar, status_text):
    nuke_cache()
    temp_dir = APP_TEMP_DIR
    
    http_headers = {'User-Agent': st.session_state.user_agent, 'Referer': 'https://www.xiaohongshu.com/'}

    ffmpeg_args = [
        '-reconnect', '1', 
        '-reconnect_streamed', '1', 
        '-reconnect_delay_max', '5'
    ]

    base_opts = {
        'quiet': True, 
        'no_warnings': True, 
        'nocache': True, 
        'rm_cachedir': True, 
        'http_headers': http_headers,
        'external_downloader_args': {'ffmpeg': ffmpeg_args}
    }

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0.0%')
            clean_percent = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).replace('%', '').strip()
            try:
                progress_bar.progress(int(float(clean_percent)))
                status_text.markdown(f"<p style='text-align:center; color: #ff2442; font-weight: 700;'>Đang kéo dữ liệu: {clean_percent}%</p>", unsafe_allow_html=True)
            except ValueError: pass

    standard_q_map = {"1080p": "best[height<=1080]", "720p": "best[height<=720]", "480p": "best[height<=480]"}
    std_opts = base_opts.copy()
    std_opts['format'] = standard_q_map.get(q_key, 'best')
    std_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s_std.%(ext)s')
    std_opts['progress_hooks'] = [progress_hook]

    with yt_dlp.YoutubeDL(std_opts) as ydl:
        ydl.cache.remove()
        info_std = ydl.extract_info(url, download=True)
        expected_ext = 'mp4' if info_std.get('ext') != 'mp4' else info_std.get('ext', 'mp4')
        file_path = os.path.join(temp_dir, f"{info_std['id']}_std.{expected_ext}")
        if not os.path.exists(file_path):
            file_path = ydl.prepare_filename(info_std)
        return info_std, file_path

# --- KHU VỰC NHẬP LIỆU ---
_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc link XHS vào đây:", height=100)

target_link = extract_url(raw_input)

# Xóa State nếu dán link MỚI
if target_link != st.session_state.current_link:
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    st.session_state.thumbnail_bytes = None
    st.session_state.author_name = "Chưa xác định"
    st.session_state.current_link = target_link
    nuke_cache() 

if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Sẵn sàng tải xuống.</div>", unsafe_allow_html=True)

st.markdown("<p class='centered-text' style='margin-bottom: 10px;'><b>Chọn phương thức gom luồng:</b></p>", unsafe_allow_html=True)

# Bố cục nút bấm tinh gọn
_, b1, b2, b3, _ = st.columns([1, 2, 2, 2, 1])

is_disabled = False if target_link else True

def process_and_download(quality):
    st.session_state.thumbnail_bytes = None 
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            info, path = download_video_to_temp(target_link, quality, progress_bar, status_text)
            st.session_state.video_data = info
            st.session_state.video_file_path = path
            
            # --- QUÉT ẢNH TƯƠI TỪ LÕI HTML ---
            found_author = info.get('uploader') or info.get('creator') or info.get('channel') or info.get('user')
            fresh_thumb_url = None
            
            try:
                scrape_url = info.get('webpage_url') or target_link
                headers = {
                    'User-Agent': st.session_state.user_agent, 
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
                
                anti_cache_scrape_url = f"{scrape_url}&_t={int(time.time())}" if "?" in scrape_url else f"{scrape_url}?_t={int(time.time())}"
                resp = requests.get(anti_cache_scrape_url, headers=headers, timeout=10, allow_redirects=True)
                
                if resp.status_code == 200:
                    if not found_author:
                        match = re.search(r'"nickname"\s*:\s*"([^"]+)"', resp.text)
                        if match: found_author = json.loads('"' + match.group(1) + '"')
                    
                    img_match = re.search(r'<meta name="og:image" content="([^"]+)"', resp.text)
                    if img_match:
                        fresh_thumb_url = img_match.group(1).replace('\\u002F', '/')
            except: pass
            
            st.session_state.author_name = found_author if found_author else "Chưa xác định"
            
            thumb_url = fresh_thumb_url
            if not thumb_url:
                thumbnails = info.get('thumbnails', [])
                if thumbnails:
                    valid_thumbs = [t for t in thumbnails if t.get('url')]
                    if valid_thumbs:
                        try: best_thumb = max(valid_thumbs, key=lambda x: (x.get('width') or 0) * (x.get('height') or 0)); thumb_url = best_thumb.get('url')
                        except: thumb_url = valid_thumbs[-1].get('url') 
                if not thumb_url: thumb_url = info.get('thumbnail') 

            if thumb_url:
                try:
                    anti_cache_img_url = f"{thumb_url}&_t={int(time.time())}" if "?" in thumb_url else f"{thumb_url}?_t={int(time.time())}"
                    img_headers = {
                        'User-Agent': st.session_state.user_agent, 
                        'Referer': 'https://www.xiaohongshu.com/', 
                        'Cache-Control': 'no-cache, no-store, must-revalidate'
                    }
                    resp = requests.get(anti_cache_img_url, headers=img_headers, timeout=15)
                    if resp.status_code == 200: 
                        st.session_state.thumbnail_bytes = resp.content
                except: pass
            
            progress_bar.empty()
            status_text.empty()
        except Exception as e:
            st.error(f"Đã xảy ra lỗi hệ thống: {e}")

if b1.button("BẢN 1080P", disabled=is_disabled): process_and_download("1080p")
if b2.button("BẢN 720P", disabled=is_disabled): process_and_download("720p")
if b3.button("BẢN 480P", disabled=is_disabled): process_and_download("480p")

# --- HIỂN THỊ KẾT QUẢ ---
if st.session_state.video_data and st.session_state.video_file_path:
    data = st.session_state.video_data
    file_path = st.session_state.video_file_path
    
    st.divider()
    
    raw_title = data.get('title', 'Tu_Lieu_XHS')
    safe_author = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.author_name).strip()
    safe_title = re.sub(r'[\\/*?:"<>|\n\r]', "", raw_title).strip()
    if len(safe_title) > 60: safe_title = safe_title[:60] + "..."
    export_filename = f"@{safe_author}_{safe_title}"
    
    res_c1, res_c2 = st.columns([1, 1.4])
    with res_c1:
        if st.session_state.thumbnail_bytes:
            st.image(st.session_state.thumbnail_bytes, caption="Ảnh xem trước", use_container_width=True)
            st.download_button(label="🖼️ TẢI ẢNH BÌA", data=st.session_state.thumbnail_bytes, file_name=f"{export_filename}.jpg", mime="image/jpeg", use_container_width=True)
        else:
            fallback_url = data.get('thumbnail')
            if fallback_url: 
                anti_cache_fallback = f"{fallback_url}&_t={int(time.time())}" if "?" in fallback_url else f"{fallback_url}?_t={int(time.time())}"
                st.image(anti_cache_fallback, caption="Ảnh xem trước tư liệu", use_container_width=True)
            else: 
                st.info("Không có ảnh xem trước")

    with res_c2:
        st.subheader("📌 Chi tiết bản ghi")
        st.write(f"**Tác giả:** {st.session_state.author_name}")
        st.write(f"**Tiêu đề:** {data.get('title', 'N/A')}")
        st.write(f"**Độ phân giải:** {data.get('width', 'N/A')}x{data.get('height', 'N/A')} | **FPS:** {data.get('fps', 'N/A')}")
        
        if os.path.exists(file_path):
            file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            st.write(f"**Dung lượng tải về:** {file_size_mb} MB")
            
            with open(file_path, "rb") as video_file:
                st.download_button(label="📥 TẢI XUỐNG VIDEO HOÀN CHỈNH", data=video_file, file_name=f"{export_filename}.mp4", mime="video/mp4", use_container_width=True)
        else:
            st.error("Không tìm thấy file video trong bộ nhớ tạm. Hãy thử tải lại.")

    st.markdown("### 📝 Nội dung mô tả bài viết")
    description = data.get('description') or 'Không có mô tả chữ.'
    safe_desc = html.escape(description)
    st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #ff2442; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; white-space: pre-wrap; color: #333; margin-bottom: 20px;">
            {safe_desc}
        </div>
    """, unsafe_allow_html=True)
    
    meta_txt = f"TÁC GIẢ: {st.session_state.author_name}\nTIÊU ĐỀ: {data.get('title')}\n\nNỘI DUNG:\n{description}"
    safe_txt = json.dumps(meta_txt) 
    copy_html = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    body {{ margin: 0; padding: 0; background-color: transparent; }}
    button {{
        background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
        border-radius: 8px !important; width: 100% !important; height: 48px !important; 
        font-size: 16px !important; font-weight: 900 !important; letter-spacing: 0.5px !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important; cursor: pointer;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important; transition: all 0.2s ease !important;
        display: flex; align-items: center; justify-content: center;
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

st.markdown("""
    <div class='footer'>
        Thiết kế riêng cho mục đích nghiên cứu văn học của <b>Tác giả Lập</b>.<br>
        2026 Edition | Xiaohongshu Collector
    </div>
    """, unsafe_allow_html=True)
