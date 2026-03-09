import streamlit as st
import yt_dlp
import re
import os
import tempfile
import requests
import json
import html
import time
import subprocess
import shutil
import zipfile
import io
import streamlit.components.v1 as components

# --- CƠ CHẾ TỰ ĐỘNG CÀI ĐẶT TRÌNH DUYỆT ẢO TRÊN CLOUD ---
@st.cache_resource
def install_playwright_browsers():
    try:
        os.system("playwright install chromium")
    except: pass
install_playwright_browsers()
# --------------------------------------------------------

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# --- CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide")

APP_TEMP_DIR = os.path.join(tempfile.gettempdir(), 'XHS_Collector_Workspace')
if not os.path.exists(APP_TEMP_DIR):
    os.makedirs(APP_TEMP_DIR)

# --- CSS KHÔI PHỤC THEO ĐÚNG BẢN GỐC CỦA TÁC GIẢ LẬP ---
st.markdown("""
    <style>
    /* Nền caro sọc đỏ */
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }
    h1, h2, h3, p, span, label, .stMarkdown { color: #1a1a1a !important; font-family: 'Inter', 'Segoe UI', sans-serif; }
    
    /* Thiết kế nút bấm chuẩn: Thân đỏ, chữ trắng, font siêu dày */
    div.stButton > button {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 52px !important;
        font-size: 16px !important;
        font-weight: 900 !important;
        transition: all 0.2s ease;
        box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important;
    }
    div.stButton > button:hover { transform: translate(-2px, -2px); box-shadow: 8px 8px 20px rgba(255, 36, 66, 0.4) !important; background-color: #e61e3a !important; }
    div.stButton > button:active { transform: translate(2px, 2px); box-shadow: 2px 2px 5px rgba(255, 36, 66, 0.3) !important; }
    div.stButton > button:disabled, div.stButton > button:disabled p { background-color: #cccccc !important; color: #ffffff !important; opacity: 0.8 !important; box-shadow: none !important; }

    /* Nút Download hành động chính */
    div.stDownloadButton > button {
        background-color: #ff2442 !important;
        color: #ffffff !important;
        border: none !important;
        font-size: 16px !important;
        font-weight: 900 !important;
        border-radius: 12px !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important;
        width: 100% !important;
    }
    div.stDownloadButton > button:hover { background-color: #e61e3a !important; }

    /* Nút download nhỏ cho lưới ảnh Gallery */
    .gallery-download > div > div > button { height: 40px !important; font-size: 13px !important; margin-top: 10px !important; }

    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    .centered-text { text-align: center; }
    .status-msg { text-align: center; padding: 12px; border-radius: 10px; margin-bottom: 25px; font-weight: 600; }
    img { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); object-fit: cover; }
    
    /* Thu nhỏ Title góc trái */
    .app-title { color: #1a1a1a; font-size: 26px; font-weight: 900; margin: 0; padding: 0; }
    .app-subtitle { font-size: 14px; color: #666 !important; margin: 2px 0 0 0; }
    .footer { text-align: center; padding: 40px; color: #999 !important; font-size: 14px; border-top: 1px solid #f0f0f0; margin-top: 60px; background-color: rgba(255, 255, 255, 0.8); }
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI ---
if 'video_data' not in st.session_state: st.session_state.video_data = None
if 'video_file_path' not in st.session_state: st.session_state.video_file_path = None
if 'image_gallery' not in st.session_state: st.session_state.image_gallery = None
if 'current_link' not in st.session_state: st.session_state.current_link = None
if 'thumbnail_bytes' not in st.session_state: st.session_state.thumbnail_bytes = None
if 'author_name' not in st.session_state: st.session_state.author_name = "Chưa xác định"
if 'post_title' not in st.session_state: st.session_state.post_title = "TuLieu"
if 'user_cookie' not in st.session_state: st.session_state.user_cookie = ""
if 'user_agent' not in st.session_state: st.session_state.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- CỬA SỔ CÀI ĐẶT BẢO MẬT ---
@st.dialog("⚙️ CÀI ĐẶT BẢO MẬT TÀI KHOẢN")
def settings_dialog():
    st.markdown("<p style='color: #666; font-size: 14px;'>Nhập Cookie để quét luồng VIP 4K.</p>", unsafe_allow_html=True)
    cookie_input = st.text_input("Chuỗi Cookie:", value=st.session_state.user_cookie, type="password", placeholder="web_session=...", label_visibility="collapsed")
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    if st.button("💾 LƯU BẢO MẬT & ÁP DỤNG"):
        st.session_state.user_cookie = cookie_input.strip()
        st.success("✅ Đã lưu! Cửa sổ sẽ tự đóng...")
        time.sleep(1)
        st.rerun()

# --- TIÊU ĐỀ THU GỌN GÓC TRÁI ---
header_col1, header_col2 = st.columns([11, 1])
with header_col1:
    st.markdown("""
        <div style="text-align: left; margin-bottom: 20px; padding-top: 10px;">
            <h1 class="app-title">Xiaohongshu - Rednote Collector</h1>
            <p class="app-subtitle">Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>
        </div>
    """, unsafe_allow_html=True)
with header_col2:
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    if st.button("⚙️", help="Nhập Cookie"): settings_dialog()

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

# ==========================================
# LUỒNG LOGIC: QUÉT BỘ SƯU TẬP ẢNH
# ==========================================
def extract_gallery_images(url, headers):
    """Bộ quét độc lập chỉ dùng cho nút BỘ SƯU TẬP ẢNH"""
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        html_text = resp.text
        
        urls = re.findall(r'"urlDefault":"(https?://[^"]+)"', html_text)
        if not urls: urls = re.findall(r'"masterUrl":"(https?://[^"]+)"', html_text)
            
        clean_urls = []
        for u in urls:
            u = u.replace('\\u002F', '/')
            clean_u = u.split('?')[0] if '?' in u else u
            if clean_u not in clean_urls: clean_urls.append(clean_u)
        return clean_urls
    except: return []

# ==========================================
# LUỒNG LOGIC: TẢI VIDEO YT-DLP / PLAYWRIGHT
# ==========================================
def playwright_sniff_stream(url, cookie_str, ua):
    if not PLAYWRIGHT_AVAILABLE: return None
    found_url = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=ua)
            if cookie_str:
                cookies_list = [{'name': k.strip(), 'value': v.strip(), 'domain': '.xiaohongshu.com', 'path': '/'} for item in cookie_str.split(';') if '=' in item for k, v in [item.strip().split('=', 1)]]
                if cookies_list: context.add_cookies(cookies_list)
            page = context.new_page()
            def intercept_request(request):
                nonlocal found_url
                if '.m3u8' in request.url: found_url = request.url 
                elif '.mp4' in request.url and 'sns-video' in request.url and not found_url: found_url = request.url 
            page.on("request", intercept_request)
            try: page.goto(url, wait_until="domcontentloaded", timeout=15000); page.wait_for_timeout(4000)
            except: pass
            finally: browser.close()
    except: pass
    return found_url

def old_regex_sniff_m3u8(original_url, headers):
    try:
        resp = requests.get(original_url, headers=headers, timeout=10)
        matches = re.findall(r'(https?://[^\s"\'\\]+\.m3u8[^\s"\'\\]*)', resp.text)
        if matches: return matches[0].replace('\\u002F', '/').replace('\\', '')
    except: pass
    return None

def download_video_to_temp(url, q_key, progress_bar, status_text, use_playwright=False):
    nuke_cache()
    temp_dir = APP_TEMP_DIR
    http_headers = {'User-Agent': st.session_state.user_agent}
    if st.session_state.user_cookie: http_headers['Cookie'] = st.session_state.user_cookie
    base_opts = {'quiet': True, 'no_warnings': True, 'nocache': True, 'rm_cachedir': True, 'http_headers': http_headers}

    def progress_hook(d):
        if d['status'] == 'downloading':
            try: progress_bar.progress(int(float(re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0.0%')).replace('%', '').strip())))
            except: pass

    with yt_dlp.YoutubeDL(base_opts) as ydl:
        ydl.cache.remove()
        info = ydl.extract_info(url, download=False)
        vid_id = info.get('id', str(int(time.time())))

    # TẦNG 1: ORIGIN 4K
    if st.session_state.user_cookie and q_key == "Origin":
        try:
            target_download_url = None
            if use_playwright and PLAYWRIGHT_AVAILABLE:
                status_text.markdown("<p class='status-msg' style='color: #ff2442;'>🤖 Đang dùng Playwright quét luồng ẩn...</p>", unsafe_allow_html=True)
                target_download_url = playwright_sniff_stream(url, st.session_state.user_cookie, st.session_state.user_agent)
            if not target_download_url: target_download_url = old_regex_sniff_m3u8(url, http_headers)
            if not target_download_url: target_download_url = url

            vid_path, aud_path, final_path = os.path.join(temp_dir, f"{vid_id}_v.mp4"), os.path.join(temp_dir, f"{vid_id}_a.m4a"), os.path.join(temp_dir, f"{vid_id}_4k.mp4")
            
            status_text.markdown("<p class='status-msg' style='color: #ff2442;'>⏳ Đang kéo Hình Ảnh...</p>", unsafe_allow_html=True)
            v_opts = base_opts.copy(); v_opts['format'] = 'bestvideo'; v_opts['outtmpl'] = vid_path
            with yt_dlp.YoutubeDL(v_opts) as ydl: ydl.download([target_download_url])
            progress_bar.progress(40)

            status_text.markdown("<p class='status-msg' style='color: #ff2442;'>⏳ Đang kéo Âm Thanh...</p>", unsafe_allow_html=True)
            a_opts = base_opts.copy(); a_opts['format'] = 'bestaudio'; a_opts['outtmpl'] = aud_path
            with yt_dlp.YoutubeDL(a_opts) as ydl: ydl.download([target_download_url])
            progress_bar.progress(80)

            status_text.markdown("<p class='status-msg' style='color: #ff2442;'>⏳ Đang hàn ghép FFmpeg...</p>", unsafe_allow_html=True)
            if subprocess.run(['ffmpeg', '-y', '-i', vid_path, '-i', aud_path, '-c:v', 'copy', '-c:a', 'aac', final_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                progress_bar.progress(100); return info, final_path
            else: raise Exception("Lỗi ghép nối")
        except: pass

    # TẦNG 2: TIÊU CHUẨN
    standard_q_map = {"Origin": "best", "1080p": "best[height<=1080]", "720p": "best[height<=720]", "480p": "best[height<=480]"}
    std_opts = base_opts.copy()
    std_opts['format'] = standard_q_map.get(q_key, 'best'); std_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s_std.%(ext)s'); std_opts['progress_hooks'] = [progress_hook]
    with yt_dlp.YoutubeDL(std_opts) as ydl:
        ydl.cache.remove()
        info_std = ydl.extract_info(url, download=True)
        file_path = os.path.join(temp_dir, f"{info_std['id']}_std.{info_std.get('ext', 'mp4')}")
        if not os.path.exists(file_path): file_path = ydl.prepare_filename(info_std)
        return info_std, file_path

# --- KHU VỰC NHẬP LIỆU ---
_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc link vào đây:", height=100)
    if PLAYWRIGHT_AVAILABLE: use_playwright = st.checkbox("🔥 Bật Động cơ Playwright (Cho Video 4K)", value=False)
    else: use_playwright = False

target_link = extract_url(raw_input)

# Xóa rác khi link mới
if target_link != st.session_state.current_link:
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    st.session_state.image_gallery = None
    st.session_state.thumbnail_bytes = None
    st.session_state.author_name = "Chưa xác định"
    st.session_state.current_link = target_link
    nuke_cache() 

if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ anh dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Anh hãy chọn chất lượng để hệ thống bắt đầu kéo dữ liệu.</div>", unsafe_allow_html=True)

def reset_ui_state():
    st.session_state.thumbnail_bytes = None 
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    st.session_state.image_gallery = None

# ==========================================
# KHÔI PHỤC BỐ CỤC 4 NÚT CHUẨN (Dành cho Video)
# ==========================================
st.markdown("<p class='centered-text' style='margin-bottom: 10px;'><b>Chọn chất lượng để gom luồng:</b></p>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

is_disabled = False if target_link else True
selected_video_quality = None

if b1.button("ORIGIN", disabled=is_disabled): selected_video_quality = "Origin"
if b2.button("BẢN 1080P", disabled=is_disabled): selected_video_quality = "1080p"
if b3.button("BẢN 720P", disabled=is_disabled): selected_video_quality = "720p"
if b4.button("BẢN 480P", disabled=is_disabled): selected_video_quality = "480p"

# NÚT GALLERY TÁCH RIÊNG (Không chèn ép 4 nút trên)
_, b_gal, _ = st.columns([1, 4, 1])
st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
click_gallery = b_gal.button("🖼️ TẢI BỘ SƯU TẬP ẢNH (GALLERY DÀNH CHO BÀI VIẾT ẢNH)", disabled=is_disabled)

# XỬ LÝ KHI BẤM NÚT VIDEO
if selected_video_quality:
    reset_ui_state()
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        progress_bar = st.progress(0)
        status_text = st.empty()
        try:
            info, path = download_video_to_temp(target_link, selected_video_quality, progress_bar, status_text, use_playwright)
            st.session_state.video_data = info
            st.session_state.video_file_path = path
            
            # KHÔI PHỤC LOGIC LẤY ẢNH CHUẨN YT-DLP (MƯỢT, KHÔNG VỠ HẠT)
            found_author = info.get('uploader') or info.get('creator') or info.get('user')
            st.session_state.author_name = found_author if found_author else "Chưa xác định"
            st.session_state.post_title = info.get('title', 'TuLieu')
            
            thumb_url = None
            thumbnails = info.get('thumbnails', [])
            if thumbnails:
                valid_thumbs = [t for t in thumbnails if t.get('url')]
                if valid_thumbs:
                    try: best_thumb = max(valid_thumbs, key=lambda x: (x.get('width') or 0) * (x.get('height') or 0)); thumb_url = best_thumb.get('url')
                    except Exception: thumb_url = valid_thumbs[-1].get('url') 
            if not thumb_url: thumb_url = info.get('thumbnail') 

            if thumb_url:
                try:
                    # Ép tải ảnh chuẩn, không cache
                    anti_cache_img = f"{thumb_url}&_t={int(time.time())}" if "?" in thumb_url else f"{thumb_url}?_t={int(time.time())}"
                    resp = requests.get(anti_cache_img, headers={'User-Agent': st.session_state.user_agent, 'Referer': 'https://www.xiaohongshu.com/'}, timeout=10)
                    if resp.status_code == 200: st.session_state.thumbnail_bytes = resp.content
                except: pass
                
            progress_bar.empty(); status_text.empty()
        except Exception as e: st.error(f"Lỗi hệ thống: {e}")

# XỬ LÝ KHI BẤM NÚT BỘ SƯU TẬP ẢNH
if click_gallery:
    reset_ui_state()
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        status_text = st.empty()
        status_text.markdown("<p class='status-msg' style='color: #ff2442;'>🔎 Đang quét kho ảnh RAW...</p>", unsafe_allow_html=True)
        
        http_headers = {'User-Agent': st.session_state.user_agent, 'Cookie': st.session_state.user_cookie}
        
        # Lấy metadata dự phòng bằng ytdlp
        with yt_dlp.YoutubeDL({'quiet': True, 'http_headers': http_headers}) as ydl:
            try: info = ydl.extract_info(target_link, download=False)
            except: info = {}
            
        found_author = info.get('uploader') or info.get('creator') or info.get('user')
        st.session_state.author_name = found_author if found_author else "Chưa xác định"
        st.session_state.post_title = info.get('title', 'TuLieu')

        # Quét Gallery HTML
        img_urls = extract_gallery_images(target_link, http_headers)
        
        # Nếu hụt HTML, fallback qua yt-dlp thumbnails (lấy mẻ ảnh to nhất)
        if not img_urls:
            thumbnails = info.get('thumbnails', [])
            if thumbnails:
                valid_thumbs = [t for t in thumbnails if t.get('url')]
                sorted_thumbs = sorted(valid_thumbs, key=lambda x: (x.get('width') or 0) * (x.get('height') or 0), reverse=True)
                if sorted_thumbs: img_urls = [sorted_thumbs[0].get('url')]
        
        if img_urls:
            status_text.markdown(f"<p class='status-msg' style='color: #28a745;'>✅ Tải về {len(img_urls)} tấm ảnh...</p>", unsafe_allow_html=True)
            downloaded_images = []
            for idx, img_u in enumerate(img_urls):
                try:
                    resp = requests.get(img_u, headers=http_headers, timeout=10)
                    if resp.status_code == 200: downloaded_images.append({'name': f"Photo_{idx+1}.jpg", 'bytes': resp.content})
                except: pass
            st.session_state.image_gallery = downloaded_images
            status_text.empty()
        else:
            status_text.empty(); st.warning("⚠️ Không tìm thấy ảnh. Có thể đây là bài chỉ chứa Video.")

# --- HIỂN THỊ KẾT QUẢ GIAO DIỆN (CHUẨN CŨ) ---
safe_author = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.author_name).strip()
safe_title = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.post_title).strip()
if len(safe_title) > 60: safe_title = safe_title[:60] + "..."
export_filename = f"@{safe_author}_{safe_title}"

# ================================
# 1. GIAO DIỆN KẾT QUẢ VIDEO
# ================================
if st.session_state.video_data and st.session_state.video_file_path:
    st.divider()
    res_c1, res_c2 = st.columns([1, 1.4])
    
    # Cột Trái: Ảnh Preview & Nút tải Ảnh Bìa
    with res_c1:
        if st.session_state.thumbnail_bytes:
            st.image(st.session_state.thumbnail_bytes, caption="Ảnh xem trước chất lượng cao", use_container_width=True)
            st.download_button(label="🖼️ TẢI ẢNH BÌA", data=st.session_state.thumbnail_bytes, file_name=f"{export_filename}.jpg", mime="image/jpeg", use_container_width=True)
        else: 
            st.info("Không có ảnh xem trước")

    # Cột Phải: Metadata & Nút tải Video
    with res_c2:
        st.markdown("<h3 style='margin-top:0;'>📌 Chi tiết bản ghi</h3>", unsafe_allow_html=True)
        st.write(f"**Tác giả:** {st.session_state.author_name}")
        st.write(f"**Tiêu đề:** {st.session_state.post_title}")
        
        data = st.session_state.video_data
        fps_str = data.get('fps', 'N/A')
        st.write(f"**Độ phân giải:** {data.get('width', 'N/A')}x{data.get('height', 'N/A')} | **FPS:** {fps_str}")
        
        file_path = st.session_state.video_file_path
        if os.path.exists(file_path):
            file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            st.markdown(f"<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            with open(file_path, "rb") as video_file:
                st.download_button(label="📥 TẢI XUỐNG VIDEO", data=video_file, file_name=f"{export_filename}.mp4", mime="video/mp4", use_container_width=True)
        else: st.error("Lỗi mất file tạm.")

# ================================
# 2. GIAO DIỆN KẾT QUẢ GALLERY
# ================================
if st.session_state.image_gallery:
    st.divider()
    st.markdown(f"<h3>📸 Trích xuất {len(st.session_state.image_gallery)} Ảnh chất lượng cao</h3>", unsafe_allow_html=True)
    st.write(f"**Tác giả:** {st.session_state.author_name} | **Tiêu đề:** {st.session_state.post_title}")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for img in st.session_state.image_gallery:
            zip_file.writestr(f"{export_filename}_{img['name']}", img['bytes'])
    
    st.download_button(label="📦 TẢI XUỐNG TẤT CẢ ẢNH (.ZIP)", data=zip_buffer.getvalue(), file_name=f"{export_filename}_Photos.zip", mime="application/zip", use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    images = st.session_state.image_gallery
    cols = st.columns(4)
    for idx, img in enumerate(images):
        with cols[idx % 4]:
            st.image(img['bytes'], use_container_width=True)
            st.markdown("<div class='gallery-download'>", unsafe_allow_html=True)
            st.download_button(label=f"Tải {img['name']}", data=img['bytes'], file_name=f"{export_filename}_{img['name']}", mime="image/jpeg", key=f"dl_btn_{idx}")
            st.markdown("</div>", unsafe_allow_html=True)

# ================================
# 3. MÔ TẢ & LƯU VĂN BẢN CHUNG
# ================================
if st.session_state.video_data or st.session_state.image_gallery:
    st.markdown("### 📝 Nội dung mô tả bài viết")
    data = st.session_state.video_data or {}
    desc_text = data.get('description') or 'Không có mô tả chữ.'
    safe_desc = html.escape(desc_text)
    st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #ff2442; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; white-space: pre-wrap; color: #333; margin-bottom: 20px;">
            {safe_desc}
        </div>
    """, unsafe_allow_html=True)
    
    meta_txt = f"TÁC GIẢ: {st.session_state.author_name}\nTIÊU ĐỀ: {st.session_state.post_title}\n\nNỘI DUNG:\n{desc_text}"
    safe_txt = json.dumps(meta_txt) 
    copy_html = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    body {{ margin: 0; padding: 0; background-color: transparent; }}
    button {{
        background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
        border-radius: 12px !important; width: 100% !important; height: 48px !important; 
        font-size: 15px !important; font-weight: 900 !important; letter-spacing: 0.5px !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important; cursor: pointer;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important; transition: all 0.2s ease !important;
    }}
    button:hover {{ background-color: #e61e3a !important; }}
    button:active {{ transform: translate(2px, 2px) !important; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3) !important; }}
    </style>
    <button id="cpy-btn" onclick='copyToClipboard()'>LƯU VĂN BẢN</button>
    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText({safe_txt}).then(function() {{
            const btn = document.getElementById('cpy-btn');
            btn.innerText = 'ĐÃ COPY THÀNH CÔNG';
            setTimeout(() => btn.innerText = 'LƯU VĂN BẢN', 2000);
        }});
    }}
    </script>
    """
    components.html(copy_html, height=60)

st.markdown("""
    <div class='footer'>
        Thiết kế riêng cho mục đích nghiên cứu văn học của <b>Tác giả Lập</b>.<br>
        2026 Edition | Xiaohongshu-Rednote Collector
    </div>
    """, unsafe_allow_html=True)
