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
    except:
        pass

install_playwright_browsers()

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="XHS Collector - Tác giả Lập", layout="wide")

APP_TEMP_DIR = os.path.join(tempfile.gettempdir(), 'XHS_Collector_Workspace')
if not os.path.exists(APP_TEMP_DIR):
    os.makedirs(APP_TEMP_DIR)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    
    .stApp {
        background-image: linear-gradient(0deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(255, 36, 66, .05) 25%, rgba(255, 36, 66, .05) 26%, transparent 27%, transparent 74%, rgba(255, 36, 66, .05) 75%, rgba(255, 36, 66, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        background-color: #ffffff;
    }
    h1, h2, h3, p, span, label, .stMarkdown { color: #1a1a1a !important; font-family: 'Inter', 'Segoe UI', sans-serif; }
    
    div.stButton > button {
        background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
        border-radius: 12px !important; font-size: 16px !important; font-weight: 900 !important;
        height: 52px !important; box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover { transform: translate(-2px, -2px); background-color: #e61e3a !important; }
    div.stDownloadButton > button {
        background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
        font-weight: 900 !important; box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important; width: 100% !important;
    }
    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    .status-msg { text-align: center; padding: 12px; border-radius: 10px; margin-bottom: 25px; font-weight: 600; }
    .log-box { background-color: #1e1e1e; color: #00ff00; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 13px; height: 100px; overflow-y: auto; margin-bottom: 15px;}
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI ---
if 'video_data' not in st.session_state: st.session_state.video_data = None
if 'video_file_path' not in st.session_state: st.session_state.video_file_path = None
if 'current_link' not in st.session_state: st.session_state.current_link = None
if 'thumbnail_bytes' not in st.session_state: st.session_state.thumbnail_bytes = None
if 'author_name' not in st.session_state: st.session_state.author_name = "Chưa xác định"
if 'user_cookie' not in st.session_state: st.session_state.user_cookie = ""
if 'user_agent' not in st.session_state: st.session_state.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
if 'log_messages' not in st.session_state: st.session_state.log_messages = []

def add_log(msg):
    st.session_state.log_messages.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.log_messages) > 10: st.session_state.log_messages.pop(0)

@st.dialog("⚙️ CÀI ĐẶT BẢO MẬT TÀI KHOẢN")
def settings_dialog():
    cookie_input = st.text_input("Chuỗi Cookie:", value=st.session_state.user_cookie, type="password")
    if st.button("💾 LƯU BẢO MẬT & ÁP DỤNG"):
        st.session_state.user_cookie = cookie_input.strip()
        st.success("✅ Đã lưu!")
        time.sleep(1)
        st.rerun()

header_col1, header_col2 = st.columns([11, 1])
with header_col1:
    st.markdown("<h2>Xiaohongshu - Rednote Collector</h2><p>Hệ thống lưu trữ tư liệu Dual-Engine của <b>Tác giả Lập</b></p>", unsafe_allow_html=True)
with header_col2:
    if st.button("⚙️"): settings_dialog()

st.divider()

def nuke_cache():
    try:
        for filename in os.listdir(APP_TEMP_DIR):
            file_path = os.path.join(APP_TEMP_DIR, filename)
            if os.path.isfile(file_path): os.unlink(file_path)
    except: pass

def extract_url(text):
    match = re.search(r'(?:https?://(?:www\.xiaohongshu\.com/|xhslink\.com/)[a-zA-Z0-9?=&_%/-]+)', text)
    return match.group(0) if match else None

# ==========================================
# ĐỘNG CƠ LẮNG NGHE SÂU (DEEP SNIFFER)
# ==========================================
def playwright_deep_sniff(url, cookie_str, ua):
    if not PLAYWRIGHT_AVAILABLE: return None, {}
    
    stream_data = {"url": None, "headers": {}}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=ua)
            
            if cookie_str:
                cookies_list = [{'name': k.strip(), 'value': v.strip(), 'domain': '.xiaohongshu.com', 'path': '/'} for item in cookie_str.split(';') if '=' in item for k, v in [item.strip().split('=', 1)]]
                context.add_cookies(cookies_list)
                    
            page = context.new_page()
            
            def intercept_request(request):
                r_url = request.url
                # Lắng nghe chính xác luồng m3u8 hoặc mp4 gốc
                if ('.m3u8' in r_url or ('.mp4' in r_url and 'sns-video' in r_url)) and not stream_data["url"]:
                    stream_data["url"] = r_url
                    stream_data["headers"] = request.headers # BẮT TRỌN HEADERS BẢO MẬT
            
            page.on("request", intercept_request)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(4000)
            except: pass
            finally:
                browser.close()
    except Exception as e: pass
    return stream_data["url"], stream_data["headers"]

# --- LUỒNG XỬ LÝ CHÍNH ĐA TẦNG ---
def download_video_to_temp(url, q_key, progress_bar, status_text, log_container, use_playwright=False):
    nuke_cache()
    temp_dir = APP_TEMP_DIR
    st.session_state.log_messages = []
    
    http_headers = {'User-Agent': st.session_state.user_agent}
    if st.session_state.user_cookie: http_headers['Cookie'] = st.session_state.user_cookie

    base_opts = {'quiet': True, 'no_warnings': True, 'nocache': True, 'http_headers': http_headers}

    def update_log_ui():
        log_html = "<br>".join(st.session_state.log_messages)
        log_container.markdown(f"<div class='log-box'>{log_html}</div>", unsafe_allow_html=True)

    def progress_hook(d):
        if d['status'] == 'downloading':
            clean_percent = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0.0%')).replace('%', '').strip()
            speed = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_speed_str', 'N/A')).strip()
            try:
                progress_bar.progress(int(float(clean_percent)))
                status_text.markdown(f"<p style='text-align:center; color: #ff2442; font-weight: 700;'>Đang truyền dữ liệu: {clean_percent}% | Tốc độ: {speed}</p>", unsafe_allow_html=True)
            except: pass

    add_log("Khởi tạo bộ phân tích yt-dlp...")
    update_log_ui()
    
    with yt_dlp.YoutubeDL(base_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        vid_id = info.get('id', str(int(time.time())))

    # TẦNG 1: ORIGIN 4K VỚI TRÌNH LẮNG NGHE
    if st.session_state.user_cookie and q_key == "Origin":
        try:
            target_url = None
            sniffed_headers = {}
            
            if use_playwright and PLAYWRIGHT_AVAILABLE:
                add_log("Kích hoạt Playwright Deep Sniffer...")
                status_text.markdown("<p style='text-align:center; color: #ff2442; font-weight: 700;'>🤖 Đang lắng nghe luồng Stream trực tiếp từ máy chủ...</p>", unsafe_allow_html=True)
                update_log_ui()
                target_url, sniffed_headers = playwright_deep_sniff(url, st.session_state.user_cookie, st.session_state.user_agent)
            
            if not target_url:
                add_log("Fallback sang link gốc.")
                target_url = url
            else:
                add_log(f"Bắt được luồng dữ liệu: {target_url[:50]}...")
                add_log(f"Sao chép thành công {len(sniffed_headers)} headers bảo mật.")
            update_log_ui()

            vid_path = os.path.join(temp_dir, f"{vid_id}_video_only.mp4")
            aud_path = os.path.join(temp_dir, f"{vid_id}_audio_only.m4a")
            final_path = os.path.join(temp_dir, f"{vid_id}_final_4k.mp4")

            # CẤU HÌNH TRÌNH TẢI ÉP BUỘC FF-MPEG LẮNG NGHE LIÊN TỤC
            v_opts = base_opts.copy()
            v_opts['format'] = 'bestvideo'
            v_opts['outtmpl'] = vid_path
            v_opts['progress_hooks'] = [progress_hook]
            if sniffed_headers: v_opts['http_headers'].update(sniffed_headers)
            
            # Khởi động Trình lắng nghe chống đứt gãy
            v_opts['external_downloader'] = 'ffmpeg'
            v_opts['external_downloader_args'] = ['-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5']

            add_log("Bắt đầu kéo lõi Hình Ảnh với FFmpeg Reconnect...")
            update_log_ui()
            with yt_dlp.YoutubeDL(v_opts) as ydl: ydl.download([target_url])
            progress_bar.progress(40)

            add_log("Bắt đầu kéo lõi Âm Thanh...")
            update_log_ui()
            a_opts = v_opts.copy()
            a_opts['format'] = 'bestaudio'
            a_opts['outtmpl'] = aud_path
            with yt_dlp.YoutubeDL(a_opts) as ydl: ydl.download([target_url])
            progress_bar.progress(80)

            add_log("Đang hàn ghép tín hiệu...")
            update_log_ui()
            status_text.markdown("<p style='text-align:center; color: #ff2442; font-weight: 700;'>⏳ BƯỚC 3: Đang tự động hàn ghép...</p>", unsafe_allow_html=True)
            subprocess.run(['ffmpeg', '-y', '-i', vid_path, '-i', aud_path, '-c:v', 'copy', '-c:a', 'aac', final_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(final_path):
                progress_bar.progress(100)
                add_log("Hợp nhất thành công bản Origin!")
                update_log_ui()
                status_text.markdown("<p style='text-align:center; color: #28a745; font-weight: 700;'>✅ Hoàn tất! Tư liệu 4K đã được hợp nhất.</p>", unsafe_allow_html=True)
                return info, final_path

        except Exception as e:
            add_log(f"Lỗi luồng Origin: {str(e)[:50]}. Lùi về bản liền khối...")
            update_log_ui()
            time.sleep(1.5)

    # TẦNG 2: HẠ CÁNH AN TOÀN
    standard_q_map = {"Origin": "best", "1080p": "best[height<=1080]", "720p": "best[height<=720]", "480p": "best[height<=480]"}
    std_opts = base_opts.copy()
    std_opts['format'] = standard_q_map.get(q_key, 'best')
    std_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s_std.%(ext)s')
    std_opts['progress_hooks'] = [progress_hook]

    add_log(f"Khởi chạy luồng khối: {q_key}")
    update_log_ui()
    with yt_dlp.YoutubeDL(std_opts) as ydl:
        info_std = ydl.extract_info(url, download=True)
        expected_ext = 'mp4' if info_std.get('ext') != 'mp4' else info_std.get('ext', 'mp4')
        file_path = os.path.join(temp_dir, f"{info_std['id']}_std.{expected_ext}")
        if not os.path.exists(file_path): file_path = ydl.prepare_filename(info_std)
        add_log("Hoàn thành quá trình tải.")
        update_log_ui()
        return info_std, file_path

# --- KHU VỰC NHẬP LIỆU ---
_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc link XHS vào đây:", height=100)
    use_playwright = st.checkbox("🔥 Bật Trình Lắng Nghe Deep Sniffer (Túm luồng & chống rớt gói tin)", value=True) if PLAYWRIGHT_AVAILABLE else False

target_link = extract_url(raw_input)

if target_link != st.session_state.current_link:
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    st.session_state.thumbnail_bytes = None
    st.session_state.current_link = target_link
    nuke_cache() 

if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ anh dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Sẵn sàng đánh chặn luồng.</div>", unsafe_allow_html=True)

_, b1, b2, b3, b4, _ = st.columns([0.5, 1.5, 1.5, 1.5, 1.5, 0.5])
is_disabled = False if target_link else True

def process_and_download(quality):
    st.session_state.thumbnail_bytes = None 
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        log_container = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            info, path = download_video_to_temp(target_link, quality, progress_bar, status_text, log_container, use_playwright)
            st.session_state.video_data = info
            st.session_state.video_file_path = path
            
            # Logic tải ảnh bìa (giữ nguyên cờ chống cache)
            found_author = info.get('uploader') or info.get('creator') or info.get('user')
            st.session_state.author_name = found_author if found_author else "Chưa xác định"
            
            thumb_url = info.get('thumbnail') 
            if thumb_url:
                try:
                    anti_cache_img = f"{thumb_url}&_t={int(time.time())}" if "?" in thumb_url else f"{thumb_url}?_t={int(time.time())}"
                    resp = requests.get(anti_cache_img, headers={'User-Agent': st.session_state.user_agent, 'Cache-Control': 'no-cache'}, timeout=10)
                    if resp.status_code == 200: st.session_state.thumbnail_bytes = resp.content
                except: pass
            
        except Exception as e:
            st.error(f"Lỗi: {e}")

if b1.button("ORIGIN 4K", disabled=is_disabled): process_and_download("Origin")
if b2.button("BẢN 1080P", disabled=is_disabled): process_and_download("1080p")
if b3.button("BẢN 720P", disabled=is_disabled): process_and_download("720p")
if b4.button("BẢN 480P", disabled=is_disabled): process_and_download("480p")

# --- HIỂN THỊ KẾT QUẢ ---
if st.session_state.video_data and st.session_state.video_file_path:
    data = st.session_state.video_data
    file_path = st.session_state.video_file_path
    
    st.divider()
    safe_author = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.author_name).strip()
    export_filename = f"@{safe_author}_XHS_Video"
    
    res_c1, res_c2 = st.columns([1, 1.4])
    with res_c1:
        if st.session_state.thumbnail_bytes:
            st.image(st.session_state.thumbnail_bytes, caption="Ảnh xem trước", use_container_width=True)
    with res_c2:
        st.subheader("📌 Chi tiết bản ghi")
        st.write(f"**Tác giả:** {st.session_state.author_name}")
        st.write(f"**Tiêu đề:** {data.get('title', 'N/A')}")
        if os.path.exists(file_path):
            with open(file_path, "rb") as video_file:
                st.download_button(label="📥 TẢI XUỐNG VIDEO", data=video_file, file_name=f"{export_filename}.mp4", mime="video/mp4", use_container_width=True)
