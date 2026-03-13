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

# CSS Tùy chỉnh (TỐI GIẢN HÓA TOÀN BỘ)
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
        font-size: 14px !important; font-weight: 900 !important; letter-spacing: 0.5px !important;
    }
    div.stDownloadButton > button { box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important; width: 100% !important; }
    div.stDownloadButton > button:hover { background-color: #e61e3a !important; }

    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    .centered-text { text-align: center; }
    img { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .footer { text-align: center; padding: 40px; color: #999 !important; font-size: 14px; border-top: 1px solid #f0f0f0; margin-top: 60px; background-color: rgba(255, 255, 255, 0.8); }
    
    /* HACK CSS 2.0: HIỆU ỨNG HOVER & CLICK ĐA ĐIỂM (KHÔNG ICON) */
    [data-testid="stImage"] {
        position: relative !important;
        border-radius: 12px;
        overflow: hidden;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }
    [data-testid="stImage"]:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2) !important;
        z-index: 2;
    }
    
    /* Tàng hình nút Fullscreen mặc định để hứng sự kiện click */
    [data-testid="stImage"] [data-testid="StyledFullScreenButton"],
    [data-testid="stImage"] button {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        visibility: visible !important;
        display: block !important;
        cursor: pointer !important;
        z-index: 10 !important;
        background: transparent !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI ---
if 'playlist_data' not in st.session_state: st.session_state.playlist_data = None
if 'general_info' not in st.session_state: st.session_state.general_info = None
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

# --- LUỒNG XỬ LÝ CHÍNH ---
def download_video_to_temp(url, progress_bar, status_text):
    nuke_cache()
    temp_dir = APP_TEMP_DIR
    
    http_headers = {'User-Agent': st.session_state.user_agent, 'Referer': 'https://www.xiaohongshu.com/'}
    ffmpeg_args = ['-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5']

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0.0%')
            clean_percent = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).replace('%', '').strip()
            try:
                progress_bar.progress(int(float(clean_percent)))
                status_text.markdown(f"<p style='text-align:center; color: #ff2442; font-weight: 700;'>Đang xử lý dữ liệu: {clean_percent}%</p>", unsafe_allow_html=True)
            except ValueError: pass

    base_opts = {
        'format': 'best[height<=1080]/best',
        'outtmpl': os.path.join(temp_dir, '%(id)s_std.%(ext)s'),
        'quiet': True, 
        'no_warnings': True, 
        'nocache': True, 
        'rm_cachedir': True, 
        'http_headers': http_headers,
        'external_downloader_args': {'ffmpeg': ffmpeg_args},
        'progress_hooks': [progress_hook]
    }

    with yt_dlp.YoutubeDL(base_opts) as ydl:
        ydl.cache.remove()
        info_raw = ydl.extract_info(url, download=True)
        
        results = []
        if 'entries' in info_raw:
            for entry in info_raw['entries']:
                if entry:
                    file_path = ydl.prepare_filename(entry)
                    if not file_path.endswith('.mp4'):
                        new_path = file_path.rsplit('.', 1)[0] + '.mp4'
                        if os.path.exists(file_path):
                            os.rename(file_path, new_path)
                            file_path = new_path
                    results.append({'data': entry, 'path': file_path})
        else:
            file_path = ydl.prepare_filename(info_raw)
            if not file_path.endswith('.mp4'):
                new_path = file_path.rsplit('.', 1)[0] + '.mp4'
                if os.path.exists(file_path):
                    os.rename(file_path, new_path)
                    file_path = new_path
            results.append({'data': info_raw, 'path': file_path})
            
        return results, info_raw

# --- KHU VỰC NHẬP LIỆU ---
_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc link XHS vào đây:", height=100)

target_link = extract_url(raw_input)

if target_link != st.session_state.current_link:
    st.session_state.playlist_data = None
    st.session_state.general_info = None
    st.session_state.thumbnail_bytes = None
    st.session_state.author_name = "Chưa xác định"
    st.session_state.current_link = target_link
    nuke_cache() 

is_disabled = False if target_link else True

def process_and_download():
    st.session_state.thumbnail_bytes = None 
    st.session_state.playlist_data = None
    st.session_state.general_info = None
    
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            results, info = download_video_to_temp(target_link, progress_bar, status_text)
            st.session_state.playlist_data = results
            st.session_state.general_info = info
            
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

# --- NÚT BẤM KÍCH HOẠT ---
st.markdown("<br>", unsafe_allow_html=True)
_, center_btn, _ = st.columns([1, 2, 1])
with center_btn:
    if st.button("Phân tích", disabled=is_disabled):
        process_and_download()

# --- HIỂN THỊ KẾT QUẢ ---
if st.session_state.general_info and st.session_state.playlist_data:
    info = st.session_state.general_info
    playlist = st.session_state.playlist_data
    
    st.divider()
    
    raw_title = info.get('title', 'Tu_Lieu_XHS')
    safe_author = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.author_name).strip()
    safe_title = re.sub(r'[\\/*?:"<>|\n\r]', "", raw_title).strip()
    if len(safe_title) > 60: safe_title = safe_title[:60] + "..."
    export_filename_base = f"@{safe_author}_{safe_title}"
    
    res_c1, res_c2 = st.columns([1, 1.4])
    with res_c1:
        if st.session_state.thumbnail_bytes:
            st.image(st.session_state.thumbnail_bytes, use_container_width=True)
        else:
            fallback_url = info.get('thumbnail')
            if fallback_url: 
                anti_cache_fallback = f"{fallback_url}&_t={int(time.time())}" if "?" in fallback_url else f"{fallback_url}?_t={int(time.time())}"
                st.image(anti_cache_fallback, use_container_width=True)
            else: 
                st.info("Không có ảnh bìa chung")

    with res_c2:
        st.subheader("Chi tiết bài viết")
        st.write(f"**Tác giả:** {st.session_state.author_name}")
        st.write(f"**Tiêu đề:** {info.get('title', 'N/A')}")
        st.write(f"**Tổng số video quét được:** {len(playlist)} video")

        description = info.get('description') or 'Không có mô tả chữ.'
        safe_desc = html.escape(description)
        st.markdown(f"""
            <div style="background-color: #f8f9fa; border-left: 4px solid #ff2442; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; white-space: pre-wrap; color: #333; margin-top: 10px; max-height: 200px; overflow-y: auto;">
                {safe_desc}
            </div>
        """, unsafe_allow_html=True)
        
        meta_txt = f"TÁC GIẢ: {st.session_state.author_name}\nTIÊU ĐỀ: {info.get('title')}\n\nNỘI DUNG:\n{description}"
        safe_txt = json.dumps(meta_txt) 
        copy_html = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
        body {{ margin: 0; padding: 0; background-color: transparent; }}
        button {{
            background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
            border-radius: 8px !important; width: 100% !important; height: 40px !important; 
            font-size: 14px !important; font-weight: 900 !important; letter-spacing: 0.5px !important;
            font-family: 'Inter', 'Segoe UI', sans-serif !important; cursor: pointer;
            box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.2) !important; transition: all 0.2s ease !important;
            display: flex; align-items: center; justify-content: center; margin-top: 15px;
        }}
        button:hover {{ background-color: #e61e3a !important; }}
        button:active {{ transform: translate(2px, 2px) !important; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3) !important; }}
        </style>
        <button id="cpy-btn" onclick='copyToClipboard()'>COPY NỘI DUNG VĂN BẢN</button>
        <script>
        function copyToClipboard() {{
            navigator.clipboard.writeText({safe_txt}).then(function() {{
                const btn = document.getElementById('cpy-btn');
                btn.innerText = 'ĐÃ COPY THÀNH CÔNG';
                setTimeout(() => btn.innerText = 'COPY NỘI DUNG VĂN BẢN', 2000);
            }});
        }}
        </script>
        """
        components.html(copy_html, height=70)

    # 2. KHU VỰC PLAYLIST
    st.divider()
    st.markdown(f"### PLAYLIST TƯ LIỆU ({len(playlist)} Video)")
    
    cols = st.columns(3)
    
    for idx, item in enumerate(playlist):
        vid_data = item['data']
        vid_path = item['path']
        
        with cols[idx % 3]:
            st.markdown(f"""
                <div style="background-color: #fafafa; padding: 15px; border-radius: 12px; border: 1px solid #eaeaea; margin-bottom: 20px;">
                    <p style="margin: 0 0 10px 0; font-weight: 800; color: #ff2442;">Video phần {idx + 1}</p>
                </div>
            """, unsafe_allow_html=True)
            
            vid_thumb = vid_data.get('thumbnail')
            if vid_thumb:
                anti_cache_thumb = f"{vid_thumb}&_t={int(time.time())}" if "?" in vid_thumb else f"{vid_thumb}?_t={int(time.time())}"
                st.image(anti_cache_thumb, use_container_width=True)
            else:
                st.info("Video không có hình demo.")
            
            actual_res = f"{vid_data.get('width', 'N/A')}x{vid_data.get('height', 'N/A')}"
            st.write(f"**Chất lượng thu được:** {actual_res} *(Tốt nhất hiện có)*")
            
            if os.path.exists(vid_path):
                file_size_mb = round(os.path.getsize(vid_path) / (1024 * 1024), 2)
                st.write(f"**Dung lượng:** {file_size_mb} MB")
                
                download_name = f"{export_filename_base}_Phan_{idx+1}.mp4"
                with open(vid_path, "rb") as video_file:
                    st.download_button(
                        label=f"TẢI VIDEO SỐ {idx + 1}", 
                        data=video_file, 
                        file_name=download_name, 
                        mime="video/mp4", 
                        use_container_width=True,
                        key=f"dl_btn_{idx}"
                    )
            else:
                st.error("Lỗi file tạm. Hãy tải lại.")

st.markdown("""
    <div class='footer'>
        Thiết kế riêng cho mục đích nghiên cứu văn học của <b>Tác giả Lập</b>.<br>
        2026 Edition | Xiaohongshu Collector
    </div>
    """, unsafe_allow_html=True)
