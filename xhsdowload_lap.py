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
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide", initial_sidebar_state="collapsed")

APP_TEMP_DIR = os.path.join(tempfile.gettempdir(), 'XHS_Collector_Workspace')
if not os.path.exists(APP_TEMP_DIR):
    os.makedirs(APP_TEMP_DIR)

# --- CSS TỐI ƯU HÓA BỐ CỤC: TRẮNG VIỀN HỒNG XHS ---
st.markdown("""
    <style>
    /* Nền trang nhã, font chữ hiện đại */
    .stApp {
        background-color: #fcfcfc;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    h1, h2, h3, p, span, label, .stMarkdown { color: #1a1a1a !important; }
    
    /* 1. KHUNG NHẬP LIỆU: Nền trắng, viền hồng XHS */
    .stTextArea textarea {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        border: 2px solid #ff2442 !important;
        padding: 15px !important;
        font-size: 15px !important;
        color: #1a1a1a !important;
        box-shadow: 0 4px 10px rgba(255, 36, 66, 0.05) !important;
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus {
        box-shadow: 0 0 0 4px rgba(255, 36, 66, 0.15) !important;
        outline: none !important;
    }

    /* 2. CÁC NÚT BẤM (Phân tích): Nền trắng, viền hồng, chữ hồng */
    div.stButton > button {
        background-color: #ffffff !important; 
        color: #ff2442 !important; 
        border: 2px solid #ff2442 !important;
        border-radius: 12px !important; 
        font-size: 16px !important; 
        font-weight: 800 !important;
        letter-spacing: 1px !important; 
        height: 55px !important;
        width: 100% !important;
        transition: all 0.2s ease;
    }
    /* Hiệu ứng đảo màu khi lướt chuột */
    div.stButton > button:hover { 
        transform: translateY(-2px); 
        background-color: #ff2442 !important; 
        color: #ffffff !important;
        box-shadow: 0 8px 20px rgba(255, 36, 66, 0.25) !important; 
    }
    div.stButton > button:active { transform: translateY(1px); }

    /* 3. NÚT TẢI XUỐNG: Cùng phong cách trắng viền hồng */
    div.stDownloadButton > button {
        background-color: #ffffff !important; 
        color: #ff2442 !important; 
        border: 2px solid #ff2442 !important;
        border-radius: 8px !important;
        font-size: 14px !important; 
        font-weight: 800 !important; 
        width: 100% !important;
        transition: all 0.2s ease;
    }
    div.stDownloadButton > button:hover { 
        background-color: #ff2442 !important; 
        color: #ffffff !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 15px rgba(255, 36, 66, 0.2) !important;
    }

    /* Hack CSS: Chữ "Xem ảnh lớn" NẰM NGOÀI ẢNH (Góc trên trái) & Fullscreen Click */
    [data-testid="stImage"] {
        position: relative !important;
        padding-top: 32px !important; 
        border-radius: 12px;
        transition: transform 0.3s ease !important;
    }
    [data-testid="stImage"]::before {
        content: "🔍 Xem ảnh lớn"; 
        position: absolute;
        top: 4px;
        left: 0;
        color: #888;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: color 0.2s ease;
        z-index: 5;
    }
    [data-testid="stImage"]:hover::before { color: #ff2442; }
    [data-testid="stImage"]:hover { transform: scale(1.01); }
    
    [data-testid="stImage"] img {
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        pointer-events: none;
    }
    
    /* Nút tàng hình bao phủ toàn bộ vùng đệm để kích hoạt Fullscreen */
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
    }

    /* Thanh tiến trình đồng bộ màu hồng XHS */
    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    .footer { text-align: center; padding: 40px; color: #aaa !important; font-size: 13px; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI ---
if 'playlist_data' not in st.session_state: st.session_state.playlist_data = None
if 'general_info' not in st.session_state: st.session_state.general_info = None
if 'current_link' not in st.session_state: st.session_state.current_link = None
if 'thumbnail_bytes' not in st.session_state: st.session_state.thumbnail_bytes = None
if 'author_name' not in st.session_state: st.session_state.author_name = "Chưa xác định"
if 'user_agent' not in st.session_state: st.session_state.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- HÀM HỖ TRỢ ---
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

# --- LUỒNG TẢI DỮ LIỆU ---
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
                status_text.markdown(f"<p style='text-align:center; color: #ff2442; font-weight: 600; font-size: 14px;'>Đang xử lý phân tích: {clean_percent}%</p>", unsafe_allow_html=True)
            except ValueError: pass

    base_opts = {
        'format': 'best[height<=1080]/best',
        'outtmpl': os.path.join(temp_dir, '%(id)s_std.%(ext)s'),
        'quiet': True, 'no_warnings': True, 'nocache': True, 'rm_cachedir': True, 
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
                            os.rename(file_path, new_path); file_path = new_path
                    results.append({'data': entry, 'path': file_path})
        else:
            file_path = ydl.prepare_filename(info_raw)
            if not file_path.endswith('.mp4'):
                new_path = file_path.rsplit('.', 1)[0] + '.mp4'
                if os.path.exists(file_path):
                    os.rename(file_path, new_path); file_path = new_path
            results.append({'data': info_raw, 'path': file_path})
        return results, info_raw

def process_and_download():
    st.session_state.thumbnail_bytes = None 
    st.session_state.playlist_data = None
    st.session_state.general_info = None
    
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
            headers = {'User-Agent': st.session_state.user_agent, 'Cache-Control': 'no-cache, no-store', 'Pragma': 'no-cache'}
            anti_cache = f"{scrape_url}&_t={int(time.time())}" if "?" in scrape_url else f"{scrape_url}?_t={int(time.time())}"
            resp = requests.get(anti_cache, headers=headers, timeout=10)
            if resp.status_code == 200:
                if not found_author:
                    match = re.search(r'"nickname"\s*:\s*"([^"]+)"', resp.text)
                    if match: found_author = json.loads('"' + match.group(1) + '"')
                img_match = re.search(r'<meta name="og:image" content="([^"]+)"', resp.text)
                if img_match: fresh_thumb_url = img_match.group(1).replace('\\u002F', '/')
        except: pass
        
        st.session_state.author_name = found_author if found_author else "Chưa xác định"
        
        thumb_url = fresh_thumb_url
        if not thumb_url:
            thumbnails = info.get('thumbnails', [])
            if thumbnails:
                valid_thumbs = [t for t in thumbnails if t.get('url')]
                if valid_thumbs:
                    try: thumb_url = max(valid_thumbs, key=lambda x: (x.get('width') or 0) * (x.get('height') or 0)).get('url')
                    except: thumb_url = valid_thumbs[-1].get('url') 
            if not thumb_url: thumb_url = info.get('thumbnail') 

        if thumb_url:
            try:
                anti_cache_img = f"{thumb_url}&_t={int(time.time())}" if "?" in thumb_url else f"{thumb_url}?_t={int(time.time())}"
                img_headers = {'User-Agent': st.session_state.user_agent, 'Referer': 'https://www.xiaohongshu.com/'}
                resp = requests.get(anti_cache_img, headers=img_headers, timeout=15)
                if resp.status_code == 200: st.session_state.thumbnail_bytes = resp.content
            except: pass
        
        progress_bar.empty()
        status_text.empty()
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error("Rất tiếc, đã xảy ra lỗi trong quá trình phân tích. Vui lòng kiểm tra lại liên kết.")

# ==========================================
# KHU VỰC GIAO DIỆN CHÍNH (UI LAYOUT)
# ==========================================

# 1. Header tinh giản
st.markdown("""
    <div style="text-align: center; margin-top: 30px; margin-bottom: 40px;">
        <h1 style='color: #ff2442; font-weight: 900; font-size: 32px; letter-spacing: -0.5px; margin-bottom: 5px;'>XHS REDNOTE</h1>
        <p style='font-size: 15px; color: #888;'>Hệ thống Phân tích & Lưu trữ Tư liệu Văn học — <b>Tác giả Lập</b></p>
    </div>
""", unsafe_allow_html=True)

# 2. Vùng Nhập liệu Trung tâm
_, col_input, _ = st.columns([1.5, 4, 1.5])
with col_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc liên kết vào đây:", height=68, label_visibility="collapsed", placeholder="Dán nội dung bài viết hoặc liên kết XHS vào đây...")
    target_link = extract_url(raw_input)
    
    if target_link != st.session_state.current_link:
        st.session_state.playlist_data = None; st.session_state.general_info = None
        st.session_state.thumbnail_bytes = None; st.session_state.author_name = "Chưa xác định"
        st.session_state.current_link = target_link
        nuke_cache() 

    is_disabled = False if target_link else True
    
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    if st.button("Phân tích", disabled=is_disabled):
        process_and_download()

st.markdown("<br><br>", unsafe_allow_html=True)

# 3. Khu vực Hiển thị Kết quả
if st.session_state.general_info and st.session_state.playlist_data:
    info = st.session_state.general_info
    playlist = st.session_state.playlist_data
    
    raw_title = info.get('title', 'Tu_Lieu_XHS')
    safe_author = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.author_name).strip()
    safe_title = re.sub(r'[\\/*?:"<>|\n\r]', "", raw_title).strip()
    if len(safe_title) > 60: safe_title = safe_title[:60] + "..."
    export_filename_base = f"@{safe_author}_{safe_title}"
    
    # Khối Thông tin chung
    st.markdown("<h3 style='border-bottom: 1px solid #eaeaea; padding-bottom: 10px; margin-bottom: 25px; color: #1a1a1a;'>Tổng quan bài viết</h3>", unsafe_allow_html=True)
    
    res_c1, res_c2 = st.columns([1.2, 2])
    with res_c1:
        if st.session_state.thumbnail_bytes:
            st.image(st.session_state.thumbnail_bytes, use_container_width=True)
        else:
            fallback_url = info.get('thumbnail')
            if fallback_url: 
                anti_cache_fallback = f"{fallback_url}&_t={int(time.time())}" if "?" in fallback_url else f"{fallback_url}?_t={int(time.time())}"
                st.image(anti_cache_fallback, use_container_width=True)
            else: 
                st.info("Bài viết không có ảnh bìa.")

    with res_c2:
        st.write(f"**Tác giả:** {st.session_state.author_name}")
        st.write(f"**Tiêu đề:** {info.get('title', 'N/A')}")
        st.write(f"**Số lượng tệp đính kèm:** {len(playlist)} video")

        description = info.get('description') or 'Không có nội dung văn bản.'
        safe_desc = html.escape(description)
        st.markdown(f"""
            <div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #ff244220; font-size: 15px; line-height: 1.7; white-space: pre-wrap; color: #333; margin-top: 15px; max-height: 250px; overflow-y: auto; box-shadow: 0 4px 10px rgba(255,36,66,0.03);">
                {safe_desc}
            </div>
        """, unsafe_allow_html=True)
        
        meta_txt = f"TÁC GIẢ: {st.session_state.author_name}\nTIÊU ĐỀ: {info.get('title')}\n\nNỘI DUNG:\n{description}"
        safe_txt = json.dumps(meta_txt) 
        copy_html = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@700&display=swap');
        body {{ margin: 0; padding: 0; background-color: transparent; }}
        button {{
            background-color: #ffffff !important; color: #ff2442 !important; border: 2px solid #ff2442 !important;
            border-radius: 8px !important; width: 100% !important; height: 45px !important; 
            font-size: 14px !important; font-weight: 700 !important;
            font-family: 'Inter', sans-serif !important; cursor: pointer;
            transition: all 0.2s ease !important; margin-top: 15px;
        }}
        button:hover {{ background-color: #ff2442 !important; color: #ffffff !important; box-shadow: 0 4px 12px rgba(255, 36, 66, 0.2) !important; }}
        button:active {{ transform: translateY(1px) !important; }}
        </style>
        <button id="cpy-btn" onclick='copyToClipboard()'>SAO CHÉP VĂN BẢN</button>
        <script>
        function copyToClipboard() {{
            navigator.clipboard.writeText({safe_txt}).then(function() {{
                const btn = document.getElementById('cpy-btn');
                btn.innerText = 'ĐÃ SAO CHÉP';
                btn.style.backgroundColor = '#ff2442';
                btn.style.color = '#fff';
                setTimeout(() => {{
                    btn.innerText = 'SAO CHÉP VĂN BẢN';
                    btn.style.backgroundColor = '#ffffff';
                    btn.style.color = '#ff2442';
                }}, 2000);
            }});
        }}
        </script>
        """
        components.html(copy_html, height=75)

    # Khối Danh sách Tư liệu (Playlist)
    st.markdown("<br><h3 style='border-bottom: 1px solid #eaeaea; padding-bottom: 10px; margin-bottom: 25px; color: #1a1a1a;'>Danh sách Tư liệu</h3>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    for idx, item in enumerate(playlist):
        vid_data = item['data']
        vid_path = item['path']
        
        with cols[idx % 3]:
            # Bọc từng item trong một khối hộp (Card)
            st.markdown("""<div style="background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #f0f0f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); margin-bottom: 25px;">""", unsafe_allow_html=True)
            
            st.markdown(f"<p style='margin: 0 0 10px 0; font-weight: 700; color: #555; font-size: 14px;'>Phần {idx + 1}</p>", unsafe_allow_html=True)
            
            vid_thumb = vid_data.get('thumbnail')
            if vid_thumb:
                anti_cache_thumb = f"{vid_thumb}&_t={int(time.time())}" if "?" in vid_thumb else f"{vid_thumb}?_t={int(time.time())}"
                st.image(anti_cache_thumb, use_container_width=True)
            else:
                st.markdown("<div style='height: 150px; background-color: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 13px;'>Không có bản xem trước</div>", unsafe_allow_html=True)
            
            actual_res = f"{vid_data.get('width', 'N/A')}x{vid_data.get('height', 'N/A')}"
            st.markdown(f"<p style='margin-top: 15px; margin-bottom: 5px; font-size: 13px; color: #666;'>Chất lượng: <b>{actual_res}</b></p>", unsafe_allow_html=True)
            
            if os.path.exists(vid_path):
                file_size_mb = round(os.path.getsize(vid_path) / (1024 * 1024), 2)
                st.markdown(f"<p style='margin-bottom: 15px; font-size: 13px; color: #666;'>Dung lượng: <b>{file_size_mb} MB</b></p>", unsafe_allow_html=True)
                
                download_name = f"{export_filename_base}_Phan_{idx+1}.mp4"
                with open(vid_path, "rb") as video_file:
                    st.download_button(
                        label="TẢI XUỐNG", 
                        data=video_file, 
                        file_name=download_name, 
                        mime="video/mp4", 
                        use_container_width=True,
                        key=f"dl_btn_{idx}"
                    )
            else:
                st.error("Lỗi trích xuất file.")
                
            st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class='footer'>
        Phát triển riêng biệt cho mục đích nghiên cứu văn học.<br>
        2026 Edition | <b>Tác giả Lập</b>
    </div>
    """, unsafe_allow_html=True)
