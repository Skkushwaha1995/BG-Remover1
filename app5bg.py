# NOTE: This script requires 'streamlit', 'rembg', and other dependencies to be installed in the environment.
# Ensure they are available before running this file.

import os
import zipfile
from io import BytesIO
from PIL import Image
import requests

try:
    import streamlit as st
    from rembg import remove
except ModuleNotFoundError as e:
    print(f"⚠️ Required module not found: {e.name}. Please install it using: pip install streamlit rembg pillow requests")
    exit()

WHITE_COLOR = (255, 255, 255)

def compress_and_resize(image, size):
    image = image.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', image.size, WHITE_COLOR)
    canvas.paste(image, (0, 0), image if image.mode == 'RGBA' else None)
    return canvas

def remove_background(image):
    return remove(image, alpha_matting=True,
                  alpha_matting_foreground_threshold=240,
                  alpha_matting_background_threshold=10,
                  alpha_matting_erode_size=10)

def add_bg(image, color):
    if image.mode == 'RGBA':
        bg = Image.new('RGB', image.size, color)
        bg.paste(image, (0, 0), image)
        return bg
    return image.convert('RGB')

def download_image_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return BytesIO(resp.content)
    except Exception as e:
        st.warning(f"⚠️ Couldn't fetch {url}: {e}")
        return None

def process_images(files, base, size, replace_bg, bg_color):
    out = []
    for idx, f in enumerate(files, 1):
        img = Image.open(f)
        img = remove_background(img)
        if replace_bg:
            img = add_bg(img, bg_color)
        img = compress_and_resize(img, size)
        name = f"{base}_{idx}.png"
        buf = BytesIO()
        img.save(buf, "PNG", optimize=True, quality=85)
        buf.seek(0)
        out.append({"name": name, "buf": buf, "img": img})
    return out

# Streamlit UI
st.title("🖼️ Background Remover")

# File Upload
st.subheader("📁 Upload Images from Your Computer")
uploaded = st.file_uploader("Choose images to upload", type=["png", "jpg", "jpeg", "bmp"], accept_multiple_files=True)
if uploaded:
    st.session_state["files"] = uploaded

# URL Input
st.markdown("---")
st.subheader("🌐 Or Enter Image URLs (one per line)")
urls = st.text_area("Enter image URLs", height=120)
if st.button("▶️ Preview URL Images"):
    raw = []
    for url in [u.strip() for u in urls.splitlines() if u.strip()]:
        buf = download_image_from_url(url)
        if buf:
            buf.name = os.path.basename(url) or f"url_{len(raw)+1}"
            raw.append(buf)
    st.session_state["raw_urls"] = raw

# Preview & Process URL Images
if st.session_state.get("raw_urls"):
    st.markdown("**Preview Raw URL Images**")
    cols = st.columns(4)
    for i, buf in enumerate(st.session_state["raw_urls"]):
        with cols[i % 4]:
            st.image(buf, use_container_width=True, caption=getattr(buf, "name", f"URL_{i+1}"))

    base_url = st.text_input("Base name for URL images", value="url_image")
    w_url = st.number_input("Width (URL images)", 50, 2000, 500, key="w_url")
    h_url = st.number_input("Height (URL images)", 50, 2000, 500, key="h_url")
    bg_choice_url = st.radio("URL Background:", ["Remove Background", "Replace with Color"], key="bg_url")
    replace_bg_url = bg_choice_url.startswith("Replace")
    color_url = None
    if replace_bg_url:
        hexc = st.color_picker("Pick URL BG Color", "#ffffff", key="col_url")
        color_url = tuple(int(hexc.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

    if st.button("✅ Process URL Images"):
        processed = process_images(
            st.session_state["raw_urls"],
            base_url, (w_url, h_url),
            replace_bg_url, color_url or WHITE_COLOR
        )
        st.session_state["proc_urls"] = processed
        st.success("✅ URL Images Processed")

# Display Processed URL Images
if st.session_state.get("proc_urls"):
    st.subheader("🖼️ Processed URL Images")
    cols = st.columns(4)
    for i, info in enumerate(st.session_state["proc_urls"]):
        with cols[i % 4]:
            st.image(info["img"], use_container_width=True, caption=info["name"])
            st.download_button("⬇️ Download", data=info["buf"], file_name=info["name"], mime="image/png", key=f"dl_url_{i}")

    zipb = BytesIO()
    with zipfile.ZipFile(zipb, "w") as zf:
        for info in st.session_state["proc_urls"]:
            zf.writestr(info["name"], info["buf"].getvalue())
    zipb.seek(0)
    st.download_button("📦 Download All URLs ZIP", data=zipb, file_name="urls_processed.zip", mime="application/zip")

# Display & Process Local Files
if st.session_state.get("files"):
    st.markdown("---")
    st.subheader("🖼️ Preview Local Uploads")
    cols = st.columns(4)
    for i, up in enumerate(st.session_state["files"]):
        with cols[i % 4]:
            st.image(up, use_container_width=True, caption=up.name)

    base_f = st.text_input("Base name for local images", "cleaned", key="base_f")
    w_f = st.number_input("Width (local)", 50, 2000, 500, key="w_f")
    h_f = st.number_input("Height (local)", 50, 2000, 500, key="h_f")
    bg_choice_f = st.radio("Local Background:", ["Remove Background", "Replace with Color"], key="bg_f")
    replace_bg_f = bg_choice_f.startswith("Replace")
    color_f = None
    if replace_bg_f:
        hexf = st.color_picker("Pick Local BG Color", "#ffffff", key="col_f")
        color_f = tuple(int(hexf.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

    if st.button("✅ Process Local Images"):
        processed = process_images(
            st.session_state["files"],
            base_f, (w_f, h_f),
            replace_bg_f, color_f or WHITE_COLOR
        )
        st.session_state["proc_files"] = processed
        st.success("✅ Local Images Processed")

if st.session_state.get("proc_files"):
    st.subheader("🖼️ Processed Local Images")
    cols = st.columns(4)
    for i, info in enumerate(st.session_state["proc_files"]):
        with cols[i % 4]:
            st.image(info["img"], use_container_width=True, caption=info["name"])
            st.download_button("⬇️ Download", data=info["buf"], file_name=info["name"], mime="image/png", key=f"dl_file_{i}")

    zipb = BytesIO()
    with zipfile.ZipFile(zipb, "w") as zf:
        for info in st.session_state["proc_files"]:
            zf.writestr(info["name"], info["buf"].getvalue())
    zipb.seek(0)
    st.download_button("📦 Download All Local ZIP", data=zipb, file_name="files_processed.zip", mime="application/zip")
