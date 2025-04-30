import os
import streamlit as st
from rembg import remove
from PIL import Image
import tempfile
import zipfile
from io import BytesIO

WHITE_COLOR = (255, 255, 255)

def compress_and_resize(image, size):
    image = image.resize(size, Image.Resampling.LANCZOS)
    compressed_image = Image.new('RGB', image.size, WHITE_COLOR)
    compressed_image.paste(image, (0, 0))
    return compressed_image

def remove_background(image):
    return remove(image)

def add_white_background(image, background_color=WHITE_COLOR):
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, background_color)
        background.paste(image, (0, 0), image)
        return background
    return image.convert('RGB')

def process_images(images, base_name, output_size, add_bg=False):
    results = []

    for idx, file in enumerate(images, start=1):
        img = Image.open(file)
        output_image = remove_background(img)
        if add_bg:
            output_image = add_white_background(output_image)
        output_image = compress_and_resize(output_image, output_size)

        filename = f"{base_name}_{idx}.png"
        buffer = BytesIO()
        output_image.save(buffer, format="PNG", quality=85, optimize=True)
        buffer.seek(0)
        file_size_kb = len(buffer.getvalue()) // 1024
        results.append({
            "filename": filename,
            "buffer": buffer,
            "size_kb": file_size_kb,
            "image": output_image
        })

    return results

# --- Streamlit App ---

st.title("🖼️ Background Remover")

# Session state setup
if "processed_images" not in st.session_state:
    st.session_state["processed_images"] = []
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []

# Upload images
uploaded_files = st.file_uploader("Upload Images", type=["png", "jpg", "jpeg", "bmp"], accept_multiple_files=True)

if uploaded_files:
    st.session_state.uploaded_files = uploaded_files

if st.session_state.uploaded_files:
    st.subheader("🖼️ Preview Uploaded Images")
    cols = st.columns(4)
    for idx, file in enumerate(st.session_state.uploaded_files):
        with cols[idx % 4]:
            st.image(file, caption=os.path.basename(file.name), use_container_width=True)

    st.markdown("---")
    base_name = st.text_input("🔤 Enter base name for all output files", value="cleaned_image")

    col1, col2 = st.columns(2)
    with col1:
        width = st.number_input("📏 Width", min_value=50, max_value=1000, value=500)
    with col2:
        height = st.number_input("📏 Height", min_value=50, max_value=1000, value=500)

    bg_choice = st.radio("🧼 Background option", ["Remove Background", "Replace with White Background"])
    add_bg = bg_choice == "Replace with White Background"

    if st.button("✅ Process Images"):
        with st.spinner("Processing..."):
            results = process_images(st.session_state.uploaded_files, base_name, (width, height), add_bg=add_bg)
            st.session_state.processed_images = results
        st.success("All images processed!")

# Show processed images
if st.session_state.processed_images:
    st.subheader("🖼️ Processed Images")

    selected_filenames = st.multiselect(
        "✅ Select images to download individually:",
        [img["filename"] for img in st.session_state.processed_images],
        default=[img["filename"] for img in st.session_state.processed_images]
    )

    cols = st.columns(4)
    for idx, img_info in enumerate(st.session_state.processed_images):
        with cols[idx % 4]:
            st.image(img_info["image"], caption=f"{img_info['filename']} ({img_info['size_kb']} KB)", use_container_width=True)
            if img_info["filename"] in selected_filenames:
                st.download_button(
                    label=f"⬇️ Download",
                    data=img_info["buffer"],
                    file_name=img_info["filename"],
                    mime="image/png",
                    key=f"download_{img_info['filename']}"
                )

    # Download all ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for img_info in st.session_state.processed_images:
            zipf.writestr(img_info["filename"], img_info["buffer"].getvalue())
    zip_buffer.seek(0)

    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="processed_images.zip",
        mime="application/zip"
    )

    # OPTIONAL – Download All Individually
    if st.button("⬇️ Download All Individually (No ZIP)"):
        ...
        # This part already in your script

    # 🔽 PLACE NEW CODE HERE
    st.markdown("---")
    st.subheader("🌐 Download Links for External Use")
    ...
    # Copyable Links Code
