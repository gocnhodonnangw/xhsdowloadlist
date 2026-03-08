import streamlit as st
import yt_dlp
import re
import os
import tempfile
import requests
import json
import html
import time
import streamlit.components.v1 as components

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

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'video_data' not in st.session_state:
    st.session_state.video_data = None
if 'video_file_path' not in st.session_state:
    st.session_state.video_file_path = None
if 'current_link' not in st.session_state:
    st.session_state.current_link = None
if 'thumbnail_bytes' not in st.session_state:
    st.session_state.thumbnail_bytes = None
if 'author_name' not in st.session_state:
    st.session_state.author_name = "Chưa xác định"
if 'user_cookie' not in st.session_state:
    st.session_state.user_cookie = ""

# --- CỬA SỔ NỔI (DIALOG) CÀI ĐẶT BẢO MẬT ---
@st.dialog("⚙️ CÀI ĐẶT BẢO MẬT")
def settings_dialog():
    st.markdown("""
        <div style="background-color: #fdfdfd; padding: 18px; border-radius: 12px; border: 1px solid #eaeaea; margin-bottom: 20px;">
            <h4 style="color: #ff2442; margin-top: 0px; margin-bottom: 12px; font-weight: 800;">🔑 Cấp quyền luồng VIP (4K)</h4>
            <p style="color: #666; font-size: 14px; margin-bottom: 8px; line-height: 1.5;">
                Nhập chuỗi Cookie tài khoản Xiaohongshu của anh vào đây để hệ thống tự động tóm luồng chất lượng cao nhất.
            </p>
            <p style="color: #888; font-size: 13px; margin-bottom: 0px;">
                <i>*Nhấn vào biểu tượng <b>con mắt 👁️</b> bên phải khung nhập để xem/ẩn nội dung.</i>
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    cookie_input = st.text_input(
        "Chuỗi Cookie:", 
        value=st.session_state.user_cookie, 
        type="password", 
        placeholder="Dán mã Cookie bắt đầu bằng web_session=...",
        label_visibility="collapsed"
    )
    
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    if st.button("💾 LƯU BẢO MẬT & ÁP DỤNG"):
        st.session_state.user_cookie = cookie_input.strip()
        st.success("✅ Đã lưu an toàn! Cửa sổ sẽ tự đóng...")
        time.sleep(1)
        st.rerun()

# --- TIÊU ĐỀ & NÚT CÀI ĐẶT ---
header_col1, header_col2 = st.columns([11, 1])
with header_col1:
    st.markdown("""
        <div style="text-align: left; margin-bottom: 20px; padding-top: 10px;">
            <h2 style='color: #ff2442; margin-bottom: 0px; padding-bottom: 0px; font-weight: 900; font-size: 26px;'>Xiaohongshu - Rednote Collector</h2>
            <p style='font-size: 15px; color: #666 !important; margin-top: 2px;'>Hệ thống lưu trữ tư liệu của <b>Tác giả Lập</b></p>
        </div>
    """, unsafe_allow_html=True)
with header_col2:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    if st.button("⚙️", help="Nhập Cookie mở khóa 4K"):
        settings_dialog()

st.divider()

# --- HÀM XỬ LÝ DỮ LIỆU CHÍNH VỚI LOGIC DỰ PHÒNG KÉP ---
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

    # Hàm tải cốt lõi
    def attempt_download(opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            expected_ext = 'mp4' if info.get('ext') != 'mp4' else info.get('ext', 'mp4')
            file_path = os.path.join(temp_dir, f"{info['id']}.{expected_ext}")
            if not os.path.exists(file_path):
                file_path = ydl.prepare_filename(info)
            return info, file_path

    # Tùy chọn cơ bản (Base options)
    base_opts = {
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'nocache': True
    }
    
    # Kịch bản 1: CÓ COOKIE + CHỌN ORIGIN (Truy kích luồng 4K)
    if st.session_state.user_cookie and q_key == "Origin":
        status_text.markdown("<p style='text-align:center; color: #ff2442; font-weight: 700;'>🚀 Đang truy kích luồng VIP 4K...</p>", unsafe_allow_html=True)
        vip_opts = base_opts.copy()
        vip_opts['format'] = "bestvideo+bestaudio/best"
        vip_opts['format_sort'] = ['res', 'size', 'br', 'fps']
        vip_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': st.session_state.user_cookie
        }
        
        try:
            return attempt_download(vip_opts)
        except Exception as e:
            # NẾU LỖI -> Không sập app, chuyển sang Lớp Dự Phòng
            status_text.markdown("<p style='text-align:center; color: #ff8c00; font-weight: 700;'>⚠️ Lỗi Cookie/Luồng VIP. Tự động kích hoạt tải dự phòng...</p>", unsafe_allow_html=True)
            time.sleep(1.5) # Dừng 1.5s để anh Lập kịp nhìn thấy thông báo

    # Kịch bản 2: TẢI TIÊU CHUẨN / LỚP DỰ PHÒNG AN TOÀN
    standard_q_map = {
        "Origin": "bestvideo+bestaudio/best", 
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best"
    }
    
    std_opts = base_opts.copy()
    std_opts['format'] = standard_q_map.get(q_key, 'best')
    if st.session_state.user_cookie:
        std_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': st.session_state.user_cookie
        }
        
    return attempt_download(std_opts)

# --- GIAO DIỆN TƯƠNG TÁC ---
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
    st.session_state.author_name = "Chưa xác định"
    st.session_state.current_link = target_link

if not target_link:
    st.markdown("<div class='status-msg' style='background-color: #f8f9fa; color: #888 !important;'>⚪ Hệ thống đang chờ anh dán link tư liệu...</div>", unsafe_allow_html=True)
else:
    if st.session_state.user_cookie:
        st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! [ĐÃ BẬT COOKIE VIP] Sẵn sàng truy kích luồng Origin cao nhất.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-msg' style='background-color: #fff5f6; color: #ff2442 !important;'>🔴 Đã tìm thấy link! [CHƯA BẬT COOKIE] Khuyên dùng bản 1080p hoặc 720p.</div>", unsafe_allow_html=True)

st.markdown("<p class='centered-text' style='margin-bottom: 10px;'><b>Chọn chất lượng để gom luồng:</b></p>", unsafe_allow_html=True)
_, b1, b2, b3, b4, _ = st.columns([1, 2, 2, 2, 2, 1])

is_disabled = False if target_link else True

def process_and_download(quality):
    _, p_col, _ = st.columns([1, 4, 1])
    with p_col:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.session_state.thumbnail_bytes = None 
        
        try:
            info, path = download_video_to_temp(target_link, quality, progress_bar, status_text)
            st.session_state.video_data = info
            st.session_state.video_file_path = path
            
            found_author = info.get('uploader') or info.get('creator') or info.get('channel') or info.get('user')
            if not found_author:
                try:
                    scrape_url = info.get('webpage_url') or target_link
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Cookie': st.session_state.user_cookie if st.session_state.user_cookie else ''
                    }
                    resp = requests.get(scrape_url, headers=headers, timeout=10, allow_redirects=True)
                    if resp.status_code == 200:
                        match = re.search(r'"nickname"\s*:\s*"([^"]+)"', resp.text)
                        if match:
                            raw_name = match.group(1)
                            found_author = json.loads('"' + raw_name + '"')
                except Exception:
                    pass
            
            st.session_state.author_name = found_author if found_author else "Chưa xác định"
            
            thumbnails = info.get('thumbnails', [])
            thumb_url = None
            if thumbnails:
                valid_thumbs = [t for t in thumbnails if t.get('url')]
                if valid_thumbs:
                    try:
                        best_thumb = max(valid_thumbs, key=lambda x: (x.get('width') or 0) * (x.get('height') or 0))
                        thumb_url = best_thumb.get('url')
                    except Exception:
                        thumb_url = valid_thumbs[-1].get('url') 
            
            if not thumb_url:
                thumb_url = info.get('thumbnail') 

            if thumb_url:
                try:
                    img_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://www.xiaohongshu.com/',
                        'Cookie': st.session_state.user_cookie if st.session_state.user_cookie else ''
                    }
                    resp = requests.get(thumb_url, headers=img_headers, timeout=15)
                    if resp.status_code == 200:
                        st.session_state.thumbnail_bytes = resp.content
                except:
                    pass
            
            progress_bar.empty()
            status_text.empty()
        except Exception as e:
            st.error(f"Đã xảy ra lỗi hệ thống: {e}")

if b1.button("ORIGIN", disabled=is_disabled): process_and_download("Origin")
if b2.button("BẢN 1080P", disabled=is_disabled): process_and_download("1080p")
if b3.button("BẢN 720P", disabled=is_disabled): process_and_download("720p")
if b4.button("BẢN 480P", disabled=is_disabled): process_and_download("480p")

# --- HIỂN THỊ KẾT QUẢ TỪ SESSION STATE ---
if st.session_state.video_data and st.session_state.video_file_path:
    data = st.session_state.video_data
    file_path = st.session_state.video_file_path
    
    st.divider()
    
    raw_title = data.get('title', 'Tu_Lieu_XHS')
    safe_author = re.sub(r'[\\/*?:"<>|\n\r]', "", st.session_state.author_name).strip()
    safe_title = re.sub(r'[\\/*?:"<>|\n\r]', "", raw_title).strip()
    
    if len(safe_title) > 60:
        safe_title = safe_title[:60] + "..."
        
    export_filename = f"@{safe_author}_{safe_title}"
    
    res_c1, res_c2 = st.columns([1, 1.4])
    with res_c1:
        if st.session_state.thumbnail_bytes:
            st.image(st.session_state.thumbnail_bytes, caption="Ảnh xem trước chất lượng cao", use_container_width=True)
            st.download_button(
                label="🖼️ TẢI ẢNH BÌA",
                data=st.session_state.thumbnail_bytes,
                file_name=f"{export_filename}.jpg",
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
        
        st.write(f"**Tác giả:** {st.session_state.author_name}")
        st.write(f"**Tiêu đề:** {data.get('title', 'N/A')}")
        st.write(f"**Độ phân giải:** {data.get('width', 'N/A')}x{data.get('height', 'N/A')} | **FPS:** {data.get('fps', 'N/A')}")
        
        if os.path.exists(file_path):
            file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            st.write(f"**Dung lượng tải về:** {file_size_mb} MB")
            
            with open(file_path, "rb") as video_file:
                st.download_button(
                    label="📥 TẢI XUỐNG VIDEO",
                    data=video_file,
                    file_name=f"{export_filename}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
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
    
    # Nút COPY VĂN BẢN 
    meta_txt = f"TÁC GIẢ: {st.session_state.author_name}\nTIÊU ĐỀ: {data.get('title')}\n\nNỘI DUNG:\n{description}"
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
