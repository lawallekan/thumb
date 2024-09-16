import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
import io
import os
import json
import colorsys

# Set page config for a wider layout
st.set_page_config(layout="wide", page_title="Improved YouTube Thumbnail Creator")

# Custom CSS for improved styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stDownloadButton>button {
        width: 100%;
    }
    .card {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Font handling functions
def get_font_files(directory):
    return [f for f in os.listdir(directory) if f.lower().endswith(('.ttf', '.otf'))]

def get_font_path(font_name, custom_font_dir):
    return os.path.join(custom_font_dir, font_name)

# Color handling functions
def hex_to_rgb(hex_color):
    return tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

def generate_color_scheme(base_color):
    r, g, b = [x/255.0 for x in hex_to_rgb(base_color)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    complementary_h = (h + 0.5) % 1.0
    complementary_rgb = colorsys.hsv_to_rgb(complementary_h, s, v)
    complementary_hex = '#{:02x}{:02x}{:02x}'.format(int(complementary_rgb[0]*255), int(complementary_rgb[1]*255), int(complementary_rgb[2]*255))
    
    analogous1_h = (h + 0.083333) % 1.0
    analogous2_h = (h - 0.083333) % 1.0
    analogous1_rgb = colorsys.hsv_to_rgb(analogous1_h, s, v)
    analogous2_rgb = colorsys.hsv_to_rgb(analogous2_h, s, v)
    analogous1_hex = '#{:02x}{:02x}{:02x}'.format(int(analogous1_rgb[0]*255), int(analogous1_rgb[1]*255), int(analogous1_rgb[2]*255))
    analogous2_hex = '#{:02x}{:02x}{:02x}'.format(int(analogous2_rgb[0]*255), int(analogous2_rgb[1]*255), int(analogous2_rgb[2]*255))
    
    return {
        "base": base_color,
        "complementary": complementary_hex,
        "analogous1": analogous1_hex,
        "analogous2": analogous2_hex
    }

# Text effect functions
def apply_text_effects(draw, text, font, color, x, y, outline_color, outline_width, shadow_color, shadow_offset):
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            draw.text((x + offset_x, y + offset_y), text, font=font, fill=outline_color)
    
    draw.text((x, y), text, font=font, fill=color)

# Main thumbnail creation function
def create_thumbnail(title, subtitle, bg_color, bg_image, overlay_opacity, border_color, border_width, 
                     title_font, title_size, title_color, title_outline_color, title_outline_width,
                     subtitle_font, subtitle_size, subtitle_color, subtitle_outline_color, subtitle_outline_width,
                     brightness, contrast, saturation, blur, shadow_color, shadow_offset, 
                     title_position, subtitle_position, text_spacing, custom_font_dir):
    img = Image.new('RGB', (1280, 720), color=bg_color)
    
    if bg_image is not None:
        bg = Image.open(bg_image).convert('RGBA')
        bg = bg.resize((1280, 720), Image.Resampling.LANCZOS)
        
        bg = ImageEnhance.Brightness(bg).enhance(brightness)
        bg = ImageEnhance.Contrast(bg).enhance(contrast)
        bg = ImageEnhance.Color(bg).enhance(saturation)
        if blur > 0:
            bg = bg.filter(ImageFilter.GaussianBlur(radius=blur))
        
        img = Image.alpha_composite(img.convert('RGBA'), bg)
    
    overlay = Image.new('RGBA', (1280, 720), color=(*hex_to_rgb(bg_color), int(255 * overlay_opacity)))
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    
    img = img.convert('RGB')
    
    if border_width > 0:
        img = ImageOps.expand(img, border=border_width, fill=border_color)
    
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype(get_font_path(title_font, custom_font_dir), title_size)
        subtitle_font = ImageFont.truetype(get_font_path(subtitle_font, custom_font_dir), subtitle_size)
    except IOError:
        st.error(f"Font not found. Please make sure the font files are present in {custom_font_dir}")
        return None

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
    
    if title_position == 'left':
        title_x = 40
    elif title_position == 'center':
        title_x = (1280 - title_width) // 2
    else:  # right
        title_x = 1280 - title_width - 40
    
    if subtitle_position == 'left':
        subtitle_x = 40
    elif subtitle_position == 'center':
        subtitle_x = (1280 - subtitle_width) // 2
    else:  # right
        subtitle_x = 1280 - subtitle_width - 40
    
    title_y = (720 - title_height - subtitle_height - text_spacing) // 2
    subtitle_y = title_y + title_height + text_spacing
    
    apply_text_effects(draw, title, title_font, title_color, title_x, title_y, title_outline_color, title_outline_width, shadow_color, shadow_offset)
    apply_text_effects(draw, subtitle, subtitle_font, subtitle_color, subtitle_x, subtitle_y, subtitle_outline_color, subtitle_outline_width, shadow_color, shadow_offset)
    
    return img

# Template management functions
def load_templates():
    try:
        with open('templates.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_templates(templates):
    with open('templates.json', 'w') as f:
        json.dump(templates, f)

# Sidebar for settings
st.sidebar.title("Thumbnail Settings")

# Font directory
custom_font_dir = r"C:\Users\Lekside Nation\Desktop\Python Project\video tb\fonts"
font_files = get_font_files(custom_font_dir)

# Text Content
st.sidebar.subheader("Text Content")
title = st.sidebar.text_input("Enter title", "RICK ASTLEY - NEVER", key="sidebar_title_1")
subtitle = st.sidebar.text_input("Enter subtitle", "GONNA GIVE YOU UP [HQ]", key="sidebar_subtitle_1")

# Title Settings
st.sidebar.subheader("Title Settings")
title_font = st.sidebar.selectbox("Title Font", font_files, key="sidebar_title_font_1")
title_size = st.sidebar.slider("Title Size", 20, 300, 80, key="sidebar_title_size_1")
title_color = st.sidebar.color_picker("Title Color", "#ffffff", key="sidebar_title_color_1")
title_outline_color = st.sidebar.color_picker("Title Outline Color", "#000000", key="sidebar_title_outline_color_1")
title_outline_width = st.sidebar.slider("Title Outline Width", 0, 5, 2, key="sidebar_title_outline_width_1")

# Subtitle Settings
st.sidebar.subheader("Subtitle Settings")
subtitle_font = st.sidebar.selectbox("Subtitle Font", font_files, key="sidebar_subtitle_font_1")
subtitle_size = st.sidebar.slider("Subtitle Size", 10, 300, 40, key="sidebar_subtitle_size_1")
subtitle_color = st.sidebar.color_picker("Subtitle Color", "#ffffff", key="sidebar_subtitle_color_1")
subtitle_outline_color = st.sidebar.color_picker("Subtitle Outline Color", "#000000", key="sidebar_subtitle_outline_color_1")
subtitle_outline_width = st.sidebar.slider("Subtitle Outline Width", 0, 5, 1, key="sidebar_subtitle_outline_width_1")

# Add checkboxes for title and subtitle style settings
st.sidebar.subheader("Title Style")
title_bold = st.sidebar.checkbox("Bold Title", key="sidebar_title_bold_1")
title_italic = st.sidebar.checkbox("Italic Title", key="sidebar_title_italic_1")

st.sidebar.subheader("Subtitle Style")
subtitle_bold = st.sidebar.checkbox("Bold Subtitle", key="sidebar_subtitle_bold_1")
subtitle_italic = st.sidebar.checkbox("Italic Subtitle", key="sidebar_subtitle_italic_1")
# Background Settings
st.sidebar.subheader("Background Settings")
bg_color = st.sidebar.color_picker("Background Color", "#3498db", key="sidebar_bg_color_1")
overlay_opacity = st.sidebar.slider("Overlay Opacity", 0.0, 1.0, 0.5, 0.01, key="sidebar_overlay_opacity_1")
bg_image = st.sidebar.file_uploader("Upload background image (optional)", type=["png", "jpg", "jpeg"], key="sidebar_bg_image_1")

# Border Settings
st.sidebar.subheader("Border Settings")
border_color = st.sidebar.color_picker("Border Color", "#ffffff", key="sidebar_border_color_1")
border_width = st.sidebar.slider("Border Width", 0, 20, 5, key="sidebar_border_width_1")

# Image Filters
st.sidebar.subheader("Image Filters")
brightness = st.sidebar.slider("Brightness", 0.5, 1.5, 1.0, 0.1, key="sidebar_brightness_1")
contrast = st.sidebar.slider("Contrast", 0.5, 1.5, 1.0, 0.1, key="sidebar_contrast_1")
saturation = st.sidebar.slider("Saturation", 0.0, 2.0, 1.0, 0.1, key="sidebar_saturation_1")
blur = st.sidebar.slider("Blur", 0.0, 5.0, 0.0, 0.1, key="sidebar_blur_1")

# Text Effects
st.sidebar.subheader("Text Effects")
shadow_color = st.sidebar.color_picker("Shadow Color", "#000000", key="sidebar_shadow_color_1")
shadow_offset = st.sidebar.slider("Shadow Offset", 0, 10, 2, key="sidebar_shadow_offset_1")

# Text Positioning
st.sidebar.subheader("Text Positioning")
title_position = st.sidebar.selectbox("Title Position", ['left', 'center', 'right'], key="sidebar_title_position_1")
subtitle_position = st.sidebar.selectbox("Subtitle Position", ['left', 'center', 'right'], key="sidebar_subtitle_position_1")
text_spacing = st.sidebar.slider("Space between Title and Subtitle", 0, 100, 20, key="sidebar_text_spacing_1")

# Color Scheme Generator
st.sidebar.subheader("Color Scheme Generator")
base_color = st.sidebar.color_picker("Base Color", "#3498db", key="sidebar_base_color_1")
if st.sidebar.button("Generate Color Scheme", key="sidebar_generate_scheme_1"):
    st.session_state.color_scheme = generate_color_scheme(base_color)
    st.sidebar.success("Color scheme generated successfully!")

# Template Management
templates = load_templates()
template_name = st.sidebar.text_input("Template Name", key="sidebar_template_name_1")
if st.sidebar.button("Save Template", key="sidebar_save_template_1"):
    templates[template_name] = {
        "title": title,
        "subtitle": subtitle,
        "bg_color": bg_color,
        # Add all other settings here
    }
    save_templates(templates)
    st.sidebar.success(f"Template '{template_name}' saved successfully!")

selected_template = st.sidebar.selectbox("Load Template", [""] + list(templates.keys()), key="sidebar_select_template_1")
if selected_template and st.sidebar.button("Load Template", key="sidebar_load_template_1"):
    template = templates[selected_template]
    # Load all settings from the template
    title = template["title"]
    subtitle = template["subtitle"]
    bg_color = template["bg_color"]
    # Load all other settings here
    st.sidebar.success(f"Template '{selected_template}' loaded successfully!")

# Main content area
st.title("Improved YouTube Thumbnail Creator")
st.write("Customize your thumbnail using the settings in the sidebar!")

# Use tabs for better organization
tab1, tab2, tab3 = st.tabs(["Preview", "Generated Thumbnail", "Current Settings"])

with tab1:
    st.subheader("Preview")
    st.write("Click 'Generate Thumbnail' to see a preview of your thumbnail with current settings.")

with tab2:
    st.subheader("Generated Thumbnail")
    if st.button("Generate Thumbnail", key="main_generate_thumbnail"):
        try:
            thumbnail = create_thumbnail(
                title, subtitle, bg_color, bg_image, overlay_opacity, 
                border_color, border_width, title_font, title_size, 
                title_color, title_outline_color, title_outline_width,
                subtitle_font, subtitle_size, subtitle_color, subtitle_outline_color, subtitle_outline_width,
                brightness, contrast, saturation, blur, shadow_color, shadow_offset,
                title_position, subtitle_position, text_spacing, custom_font_dir
            )
            
            if thumbnail:
                buf = io.BytesIO()
                thumbnail.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.image(byte_im, caption="Generated Thumbnail", use_column_width=True)
                st.download_button("Download Thumbnail", byte_im, "thumbnail.png", "image/png", key="main_download_thumbnail")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

with tab3:
    st.subheader("Current Settings Preview")
    settings_preview = f"""
    - Title: {title}
    - Subtitle: {subtitle}
    - Background Color: {bg_color}
    - Title Font: {title_font}, Size: {title_size}
    - Subtitle Font: {subtitle_font}, Size: {subtitle_size}
    - Title Position: {title_position}
    - Subtitle Position: {subtitle_position}
    - Title Style: {"Bold" if title_bold else "Regular"}, {"Italic" if title_italic else "Normal"}
    - Subtitle Style: {"Bold" if subtitle_bold else "Regular"}, {"Italic" if subtitle_italic else "Normal"}
    - Text Spacing: {text_spacing}px
    """
    st.code(settings_preview, language="markdown")

    # Display generated color scheme
    if 'color_scheme' in st.session_state:
        st.subheader("Generated Color Scheme")
        cols = st.columns(4)
        for i, (name, color) in enumerate(st.session_state.color_scheme.items()):
            cols[i].markdown(f'<p style="color:{color};">{name.capitalize()}: {color}</p>', unsafe_allow_html=True)
            cols[i].markdown(f'<div style="width:100%;height:50px;background-color:{color};"></div>', unsafe_allow_html=True)

# Font loading logic update
try:
    title_font = ImageFont.truetype(get_font_path(title_font, custom_font_dir), title_size)
    if title_bold or title_italic:
        # You may need to load a bold or italic version of the font if necessary
        pass

    subtitle_font = ImageFont.truetype(get_font_path(subtitle_font, custom_font_dir), subtitle_size)
    if subtitle_bold or subtitle_italic:
        # Same here for bold or italic version of the subtitle font
        pass

except IOError:
    st.error("Font not found. Loading default font.")
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()