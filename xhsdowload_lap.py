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
    
    div.stButton > button {
        background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
        border-radius: 12px !important; font-size: 15px !important; font-weight: 900 !important;
        letter-spacing: 0.5px !important; transition: all 0.2s ease; width: 100% !important; 
        height: 52px !important; box-shadow: 6px 6px 15px rgba(255, 36, 66, 0.3) !important;
    }
    div.stButton > button:hover { transform: translate(-2px, -2px); box-shadow: 8px 8px 20px rgba(255, 36, 66, 0.4) !important; background-color: #e61e3a !important; }
    div.stButton > button:active { transform: translate(2px, 2px); box-shadow: 2px 2px 5px rgba(255, 36, 66, 0.3) !important; }
    div.stButton > button:disabled { background-color: #cccccc !important; color: #ffffff !important; opacity: 0.8 !important; box-shadow: none !important; }

    div.stDownloadButton > button {
        background-color: #ff2442 !important; color: #ffffff !important; border: none !important;
        font-size: 15px !important; font-weight: 900 !important; letter-spacing: 0.5px !important;
        box-shadow: 6px 6px 15px rgba(0, 0, 0, 0.4) !important; width: 100% !important; border-radius: 8px !important;
    }
    div.stDownloadButton > button:hover { background-color: #e61e3a !important; }

    /* Nút download riêng cho khung ảnh Gallery (nhỏ gọn hơn) */
    .gallery-download > div > div > button {
        height: 40px !important; font-size: 13px !important; margin-top: 10px !important;
    }

    .stProgress > div > div > div > div { background-color: #ff2442 !important; }
    .centered-text { text-align: center; }
    .status-msg { text-align: center; padding: 12px; border-radius: 10px; margin-bottom: 25px; font-weight: 600; }
    img { border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); object-fit: cover; }
    .footer { text-align: center; padding: 40px; color: #999 !important; font-size: 14px; border-top: 1px solid #f0f0f0; margin-top: 60px; background-color: rgba(255, 255, 255, 0.8); }
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI ---
if 'video_data' not in st.session_state: st.session_state.video_data = None
if 'video_file_path' not in st.session_state: st.session_state.video_file_path = None
if 'image_gallery' not in st.session_state: st.session_state.image_gallery = None # State lưu trữ danh sách ảnh
if 'current_link' not in st.session_state: st.session_state.current_link = None
if 'thumbnail_bytes' not in st.session_state: st.session_state.thumbnail_bytes = None
if 'author_name' not in st.session_state: st.session_state.author_name = "Chưa xác định"
if 'post_title' not in st.session_state: st.session_state.post_title = "TuLieu"
if 'post_desc' not in st.session_state: st.session_state.post_desc = ""
if 'user_cookie' not in st.session_state: st.session_state.user_cookie = ""
if 'user_agent' not in st.session_state: st.session_state.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- CỬA SỔ CÀI ĐẶT BẢO MẬT ---
@st.dialog("⚙️ CÀI ĐẶT BẢO MẬT TÀI KHOẢN")
def settings_dialog():
    st.markdown("""
        <div style="background-color: #fdfdfd; padding: 18px; border-radius: 12px; border: 1px solid #eaeaea; margin-bottom: 20px;">
            <h4 style="color: #ff2442; margin-top: 0px; margin-bottom: 12px; font-weight: 800;">🔑 Mở khóa luồng VIP 4K</h4>
            <p style="color: #666; font-size: 14px; margin-bottom: 8px; line-height: 1.5;">
                Hệ thống cần Cookie để giả lập người dùng thật và quét ảnh nét nhất.
            </p>
        </div>
    """, unsafe_allow_html=True)
    cookie_input = st.text_input("Chuỗi Cookie:", value=st.session_state.user_cookie, type="password", placeholder="Dán mã Cookie web_session=...", label_visibility="collapsed")
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    if st.button("💾 LƯU BẢO MẬT & ÁP DỤNG"):
        st.session_state.user_cookie = cookie_input.strip()
        st.success("✅ Đã lưu! Cửa sổ sẽ tự đóng...")
        time.sleep(1)
        st.rerun()

# --- TIÊU ĐỀ & NÚT CÀI ĐẶT ---
header_col1, header_col2 = st.columns([11, 1])
with header_col1:
    st.markdown("""
        <div style="text-align: left; margin-bottom: 20px; padding-top: 10px;">
            <h2 style='color: #ff2442; margin-bottom: 0px; padding-bottom: 0px; font-weight: 900; font-size: 26px;'>Xiaohongshu - Rednote Collector</h2>
            <p style='font-size: 15px; color: #666 !important; margin-top: 2px;'>Hệ thống lưu trữ tư liệu Đa phương tiện của <b>Tác giả Lập</b></p>
        </div>
    """, unsafe_allow_html=True)
with header_col2:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
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
# BỘ QUÉT ẢNH CHẤT LƯỢNG CAO TỪ HTML
# ==========================================
def extract_high_res_images(url, headers):
    """Lặn vào HTML, bóc link ảnh và ép bỏ chuẩn nén để lấy bản RAW 4K"""
    try:
        # Ép chống cache
        anti_cache_url = f"{url}&_t={int(time.time())}" if "?" in url else f"{url}?_t={int(time.time())}"
        resp = requests.get(anti_cache_url, headers=headers, timeout=15)
        html_text = resp.text

        # Bóc Tác giả, Tiêu đề, Nội dung dự phòng
        author = "Chưa xác định"
        title = "TuLieu"
        desc = ""
        
        match_author = re.search(r'"nickname"\s*:\s*"([^"]+)"', html_text)
        if match_author: author = json.loads('"' + match_author.group(1) + '"')
        
        match_title = re.search(r'<meta name="og:title" content="([^"]+)"', html_text)
        if match_title: title = html.unescape(match_title.group(1))
        
        match_desc = re.search(r'<meta name="description" content="([^"]+)"', html_text)
        if match_desc: desc = html.unescape(match_desc.group(1))

        # Quét lấy toàn bộ ảnh (Thường nằm trong 'urlDefault' hoặc 'traceId')
        urls = re.findall(r'"urlDefault":"(https?://[^"]+)"', html_text)
        if not urls:
            urls = re.findall(r'"masterUrl":"(https?://[^"]+)"', html_text)
            
        clean_urls = []
        for u in urls:
            u = u.replace('\\u002F', '/')
            # BÍ QUYẾT LẤY ẢNH GỐC: Cắt bỏ mọi query phía sau dấu ? (VD: ?imageView2/2/w/1080...)
            clean_u = u.split('?')[0] if '?' in u else u
            if clean_u not in clean_urls:
                clean_urls.append(clean_u)
                
        return clean_urls, author, title, desc
    except Exception as e:
        return [], "Lỗi", "", ""

# ==========================================
# ĐỘNG CƠ VIDEO (ĐÃ RÚT GỌN ĐỂ TẬP TRUNG)
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

    if st.session_state.user_cookie and q_key == "Origin":
        try:
            target_download_url = None
            if use_playwright and PLAYWRIGHT_AVAILABLE:
                status_text.markdown("<p class='status-msg' style='color: #ff2442;'>🤖 Đang mở luồng ẩn...</p>", unsafe_allow_html=True)
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

            status_text.markdown("<p class='status-msg' style='color: #ff2442;'>⏳ Đang hàn ghép...</p>", unsafe_allow_html=True)
            if subprocess.run(['ffmpeg', '-y', '-i', vid_path, '-i', aud_path, '-c:v', 'copy', '-c:a', 'aac', final_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                progress_bar.progress(100); return info, final_path
            else: raise Exception("Lỗi ghép nối")
        except: pass

    standard_q_map = {"Origin": "best", "1080p": "best[height<=1080]", "720p": "best[height<=720]", "480p": "best[height<=480]"}
    std_opts = base_opts.copy()
    std_opts['format'] = standard_q_map.get(q_key, 'best'); std_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s_std.%(ext)s'); std_opts['progress_hooks'] = [progress_hook]
    with yt_dlp.YoutubeDL(std_opts) as ydl:
        ydl.cache.remove(); info_std = ydl.extract_info(url, download=True)
        file_path = os.path.join(temp_dir, f"{info_std['id']}_std.{info_std.get('ext', 'mp4')}")
        if not os.path.exists(file_path): file_path = ydl.prepare_filename(info_std)
        return info_std, file_path

# --- KHU VỰC NHẬP LIỆU & LỰA CHỌN ---
_, mid_input, _ = st.columns([1, 3, 1])
with mid_input:
    raw_input = st.text_area("Dán nội dung bài viết hoặc link XHS vào đây:", height=100)
    if PLAYWRIGHT_AVAILABLE: use_playwright = st.checkbox("🔥 Bật Động cơ Playwright (Cho Video 4K)", value=False)
    else: use_playwright = False

target_link = extract_url(raw_input)

# Xóa State nếu dán link MỚI
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
    st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! Anh muốn gom Video hay gom toàn bộ Ảnh (Gallery)?</div>", unsafe_allow_html=True)

# THÊM NÚT SỐ 5 ĐỂ TẢI ẢNH GALLERY
st.markdown("<p class='centered-text' style='margin-bottom: 10px;'><b>Chọn phương thức gom luồng:</b></p>", unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)

is_disabled = False if target_link else True

def reset_ui_state():
    st.session_state.thumbnail_bytes = None 
    st.session_state.video_data = None
    st.session_state.video_file_path = None
    st.session_state.image_gallery = None

# XỬ LÝ KHI BẤM NÚT VIDEO
selected_video_quality = None
if c1.button("ORIGIN (VIDEO)", disabled=is_disabled): selected_video_quality = "Origin"
if c2.button("1080P (VIDEO)", disabled=is_disabled): selected_video_quality = "1080p"
if c3.button("720P (VIDEO)", disabled=is_disabled): selected_video_quality = "720p"
if c4.button("480P (VIDEO)", disabled=is_disabled): selected_video_quality = "480p"

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
            
            # Cập nhật thông tin cơ bản
            headers = {'User-Agent': st.session_state.user_agent, 'Cookie': st.session_state.user_cookie}
            _, author, title, desc = extract_high_res_images(target_link, headers)
            st.session_state.author_name = author
            st.session_state.post_title = title
            st.session_state.post_desc = info.get('description') or desc
            
            # Lấy ảnh bìa
            thumb_url = info.get('thumbnail')
            if thumb_url:
                try:
                    resp = requests.get(f"{thumb_url}&_t={time.time()}" if "?" in thumb_url else f"{thumb_url}?_t={time.time()}", headers=headers, timeout=10)
                    st.session_state.thumbnail_bytes = resp.content
                except: pass
            progress_bar.empty(); status_text.empty()
        except Exception as e: st.error(f"Lỗi: {e}")

# XỬ LÝ KHI BẤM NÚT TẢI LOẠT ẢNH
if c5.button("🖼️ BỘ SƯU TẬP ẢNH", disabled=is_disabled):
    reset_ui_state()
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        status_text = st.empty()
        status_text.markdown("<p class='status-msg' style='color: #ff2442;'>🔎 Đang quét kho ảnh chất lượng cao gốc...</p>", unsafe_allow_html=True)
        
        headers = {'User-Agent': st.session_state.user_agent, 'Cookie': st.session_state.user_cookie}
        img_urls, author, title, desc = extract_high_res_images(target_link, headers)
        
        st.session_state.author_name = author
        st.session_state.post_title = title
        st.session_state.post_desc = desc
        
        if img_urls:
            status_text.markdown(f"<p class='status-msg' style='color: #28a745;'>✅ Tìm thấy {len(img_urls)} tấm ảnh. Đang gom dữ liệu...</p>", unsafe_allow_html=True)
            downloaded_images = []
            for idx, img_u in enumerate(img_urls):
                try:
                    resp = requests.get(img_u, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        downloaded_images.append({
                            'name': f"Photo_{idx+1}.jpg",
                            'bytes': resp.content
                        })
                except: pass
            
            st.session_state.image_gallery = downloaded_images
            status_text.empty()
        else:
            status_text.empty()
            st.warning("⚠️ Không tìm thấy kho ảnh nào trong bài viết này. Có thể đây là bài chỉ chứa Video.")


# --- HIỂN THỊ KẾT QUẢ: CHẾ ĐỘ VIDEO ---
safe_author = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.author_name).strip()
safe_title = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.post_title).strip()
if len(safe_title) > 60: safe_title = safe_title[:60] + "..."
export_filename = f"@{safe_author}_{safe_title}"

if st.session_state.video_data and st.session_state.video_file_path:
    st.divider()
    res_c1, res_c2 = st.columns([1, 1.4])
    with res_c1:
        if st.session_state.thumbnail_bytes:
            st.image(st.session_state.thumbnail_bytes, caption="Ảnh bìa Video", use_container_width=True)
        else: st.info("Không có ảnh xem trước")

    with res_c2:
        st.subheader("📌 Chi tiết bản ghi Video")
        st.write(f"**Tác giả:** {st.session_state.author_name}")
        st.write(f"**Tiêu đề:** {st.session_state.post_title}")
        
        file_path = st.session_state.video_file_path
        if os.path.exists(file_path):
            file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            st.write(f"**Dung lượng tải về:** {file_size_mb} MB")
            with open(file_path, "rb") as video_file:
                st.download_button(label="📥 TẢI XUỐNG VIDEO HOÀN CHỈNH", data=video_file, file_name=f"{export_filename}.mp4", mime="video/mp4", use_container_width=True)
        else: st.error("Lỗi mất file tạm.")

# --- HIỂN THỊ KẾT QUẢ: CHẾ ĐỘ ẢNH (GALLERY) ---
if st.session_state.image_gallery:
    st.divider()
    st.subheader(f"📸 Trích xuất {len(st.session_state.image_gallery)} Ảnh chất lượng cao")
    st.write(f"**Tác giả:** {st.session_state.author_name} | **Tiêu đề:** {st.session_state.post_title}")
    
    # Tạo File ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for img in st.session_state.image_gallery:
            zip_file.writestr(f"{export_filename}_{img['name']}", img['bytes'])
    
    st.download_button(
        label="📦 TẢI XUỐNG TẤT CẢ ẢNH (.ZIP)",
        data=zip_buffer.getvalue(),
        file_name=f"{export_filename}_Photos.zip",
        mime="application/zip",
        use_container_width=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Hiển thị dạng lưới (Grid) 4 cột
    images = st.session_state.image_gallery
    cols = st.columns(4)
    for idx, img in enumerate(images):
        with cols[idx % 4]:
            st.image(img['bytes'], use_container_width=True)
            # Khung class CSS phụ để chỉnh nút download gọn hơn
            st.markdown("<div class='gallery-download'>", unsafe_allow_html=True)
            st.download_button(
                label=f"⬇️ {img['name']}",
                data=img['bytes'],
                file_name=f"{export_filename}_{img['name']}",
                mime="image/jpeg",
                key=f"dl_btn_{idx}"
            )
            st.markdown("</div>", unsafe_allow_html=True)

# --- KHU VỰC COPY VĂN BẢN (HIỂN THỊ CHUNG CHO CẢ 2 CHẾ ĐỘ) ---
if st.session_state.video_data or st.session_state.image_gallery:
    st.markdown("### 📝 Nội dung mô tả bài viết")
    desc_text = st.session_state.post_desc or 'Không có mô tả chữ.'
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
        2026 Edition | Xiaohongshu-Rednote Collector
    </div>
    """, unsafe_allow_html=True)
