# RENDIMENSION Brand Engine v2.0
# Carousel compositor for Rendimension social media automation
# Blue gradient style with architectural visualization focus
# UPDATED: Larger fonts, white description, 4:5 vertical format

from flask import Flask, request, send_file, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
import uuid
import time
import requests

app = Flask(__name__)

# =========================
# Storage for generated images
# =========================
generated_images = {}

# =========================
# Paths
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POST_OUTPUT_DIR = os.path.join(BASE_DIR, 'post_output')
os.makedirs(POST_OUTPUT_DIR, exist_ok=True)

# =========================
# Font Configuration
# =========================
FONT_BOLD_PATH = "Montserrat-Bold.ttf"
FONT_REGULAR_PATH = "Montserrat-VariableFont_wght.ttf"

# =========================
# RENDIMENSION Brand Colors
# =========================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BLUE = (220, 230, 255)

# Rendimension Blue Gradient Colors
RENDI_BLUE_DARK = (30, 58, 138)      # #1E3A8A
RENDI_BLUE_MID = (30, 64, 175)       # #1E40AF
RENDI_BLUE_LIGHT = (59, 130, 246)    # #3B82F6

# =========================
# RENDIMENSION Brand Defaults
# =========================
DEFAULT_BRAND_NAME = os.environ.get('BRAND_NAME', 'RENDIMENSION')
DEFAULT_TAGLINE = os.environ.get('TAGLINE', 'Architectural Visualization for Real Estate Development')
DEFAULT_WEBSITE = os.environ.get('WEBSITE_URL', 'www.rendimension.com')
LOGO_URL = os.environ.get('LOGO_URL', 'https://res.cloudinary.com/dotimxrnh/image/upload/v1772757400/LOGO_FOR_STREAMING_v0aph8.png')

# =========================
# Layout Configuration - VERTICAL 4:5 for Instagram/Facebook
# =========================
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350  # 4:5 vertical format (more coverage)
MARGIN_LEFT = 50
MARGIN_RIGHT = 50
MARGIN_TOP = 30
MARGIN_BOTTOM = 50

# =========================
# Gradient Heights (adjusted for taller canvas)
# =========================
GRADIENT_TOP_HEIGHT = 120
GRADIENT_BOTTOM_HEIGHT = 450  # Larger for more text space

# =========================
# Load Fonts AT STARTUP
# =========================
def load_font(size, name, bold=True):
    font_path = FONT_BOLD_PATH if bold else FONT_REGULAR_PATH
    try:
        font = ImageFont.truetype(font_path, size)
        print(f"✅ {name} loaded at {size}px")
        return font
    except Exception as e:
        print(f"⚠️ {name} fallback: {e}")
        # Try system fonts
        for fallback in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 
                         '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
            try:
                font = ImageFont.truetype(fallback, size)
                print(f"✅ {name} using fallback font")
                return font
            except:
                continue
        return ImageFont.load_default()

# Font sizes for Rendimension - UPDATED SIZES
headline_font = load_font(34, "headline_font")      # Was 28, now 34
big_text_font = load_font(56, "big_text_font")      # Was 48, now 56
description_font = load_font(30, "description_font") # Was 24, now 30 - BOLD now
website_font = load_font(36, "website_font")
tagline_font = load_font(32, "tagline_font", bold=False)

# Cached logo
cached_logo = None


def cleanup_old_images():
    """Remove images older than 10 minutes"""
    current_time = time.time()
    keys_to_delete = []
    for key, value in generated_images.items():
        if current_time - value['timestamp'] > 600:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        del generated_images[key]


def fit_cover(img, target_w, target_h):
    """Scale and crop to fill"""
    img_w, img_h = img.size
    scale = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def load_logo():
    """Load Rendimension logo from URL (cached)"""
    global cached_logo
    if cached_logo is not None:
        return cached_logo.copy()
    
    try:
        resp = requests.get(LOGO_URL, timeout=10)
        resp.raise_for_status()
        logo = Image.open(io.BytesIO(resp.content))
        logo = logo.convert("RGBA")
        # Resize to fit header - max height 50px (slightly larger)
        max_height = 50
        ratio = max_height / logo.height
        new_width = int(logo.width * ratio)
        logo = logo.resize((new_width, max_height), Image.LANCZOS)
        cached_logo = logo
        print(f"✅ Logo loaded: {new_width}x{max_height}")
        return logo.copy()
    except Exception as e:
        print(f"⚠️ Could not load logo: {e}")
        return None


def create_top_gradient(width, height):
    """Create blue gradient overlay for top"""
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    for y in range(height):
        # Fade from semi-transparent blue to transparent
        progress = y / height
        alpha = int(200 * (1 - progress))  # Slightly stronger
        r = RENDI_BLUE_DARK[0]
        g = RENDI_BLUE_DARK[1]
        b = RENDI_BLUE_DARK[2]
        for x in range(width):
            overlay.putpixel((x, y), (r, g, b, alpha))
    
    return overlay


def create_bottom_gradient(width, height):
    """Create blue gradient overlay for bottom text area"""
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    for y in range(height):
        # Fade from transparent to solid blue
        progress = y / height
        alpha = int(255 * progress)
        r = RENDI_BLUE_DARK[0]
        g = RENDI_BLUE_DARK[1]
        b = RENDI_BLUE_DARK[2]
        for x in range(width):
            overlay.putpixel((x, y), (r, g, b, alpha))
    
    return overlay


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    if not text:
        return []
    
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def draw_text_with_shadow(draw, position, text, font, fill, shadow_offset=2, shadow_alpha=100):
    """Draw text with shadow for better readability"""
    x, y = position
    shadow_color = (0, 0, 0, shadow_alpha)
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def draw_text_with_strong_shadow(draw, position, text, font, fill):
    """Draw text with STRONG shadow for description - multiple layers"""
    x, y = position
    # Multiple shadow layers for stronger effect
    for offset in [4, 3, 2]:
        shadow_alpha = 80 + (4 - offset) * 40  # 80, 120, 160
        shadow_color = (0, 0, 0, shadow_alpha)
        draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def render_slide(image_source, headline='', big_text='', description='',
                 slide_number=1, total_slides=9, show_arrow=True, show_website=True,
                 is_cta=False):
    """Render a single Rendimension branded slide"""
    
    # Create canvas
    canvas = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), RENDI_BLUE_DARK)
    
    # Load background image
    try:
        if isinstance(image_source, str):
            resp = requests.get(image_source, timeout=30)
            resp.raise_for_status()
            bg_img = Image.open(io.BytesIO(resp.content))
        else:
            bg_img = image_source
        
        bg_img = bg_img.convert('RGBA')
        bg_img = fit_cover(bg_img, CANVAS_WIDTH, CANVAS_HEIGHT)
        canvas.paste(bg_img, (0, 0))
    except Exception as e:
        print(f"⚠️ Background load error: {e}")
        # Keep solid blue background
    
    # Check if this is CTA slide
    if is_cta or slide_number == total_slides:
        return render_cta_slide(canvas)
    
    # Add top gradient
    top_gradient = create_top_gradient(CANVAS_WIDTH, GRADIENT_TOP_HEIGHT)
    canvas.paste(top_gradient, (0, 0), top_gradient)
    
    # Add bottom gradient
    bottom_gradient = create_bottom_gradient(CANVAS_WIDTH, GRADIENT_BOTTOM_HEIGHT)
    canvas.paste(bottom_gradient, (0, CANVAS_HEIGHT - GRADIENT_BOTTOM_HEIGHT), bottom_gradient)
    
    # Add logo (top-left, small)
    logo = load_logo()
    if logo:
        canvas.paste(logo, (MARGIN_LEFT, MARGIN_TOP), logo)
    
    # Create draw object
    draw = ImageDraw.Draw(canvas)
    
    # Calculate text area (adjusted for taller canvas)
    text_area_top = CANVAS_HEIGHT - GRADIENT_BOTTOM_HEIGHT + 60
    
    # Draw headline (small, light blue, centered) - 34pt
    current_y = text_area_top
    if headline:
        headline_upper = headline.upper()
        lines = wrap_text(headline_upper, headline_font, CANVAS_WIDTH - 100, draw)
        for line in lines[:1]:  # Max 1 line for headline
            bbox = draw.textbbox((0, 0), line, font=headline_font)
            line_width = bbox[2] - bbox[0]
            x = (CANVAS_WIDTH - line_width) // 2
            draw_text_with_shadow(draw, (x, current_y), line, headline_font, LIGHT_BLUE, shadow_offset=2, shadow_alpha=120)
            current_y += headline_font.size + 15
    
    # Draw big text (large, white, centered) - 56pt
    current_y += 5
    if big_text:
        lines = wrap_text(big_text, big_text_font, CANVAS_WIDTH - 80, draw)
        for line in lines[:2]:  # Max 2 lines
            bbox = draw.textbbox((0, 0), line, font=big_text_font)
            line_width = bbox[2] - bbox[0]
            x = (CANVAS_WIDTH - line_width) // 2
            draw_text_with_shadow(draw, (x, current_y), line, big_text_font, WHITE, shadow_offset=3, shadow_alpha=150)
            current_y += big_text_font.size + 15
    
    # Draw description (WHITE with STRONG shadow, centered) - 30pt
    current_y += 20
    if description:
        lines = wrap_text(description, description_font, CANVAS_WIDTH - 100, draw)
        for line in lines[:3]:  # Max 3 lines
            bbox = draw.textbbox((0, 0), line, font=description_font)
            line_width = bbox[2] - bbox[0]
            x = (CANVAS_WIDTH - line_width) // 2
            # Use strong shadow for description
            draw_text_with_strong_shadow(draw, (x, current_y), line, description_font, WHITE)
            current_y += description_font.size + 10
    
    # Draw arrow (if not last slide)
    if show_arrow and slide_number < total_slides:
        arrow = "→"
        arrow_font = load_font(40, "arrow")
        bbox = draw.textbbox((0, 0), arrow, font=arrow_font)
        arrow_width = bbox[2] - bbox[0]
        draw.text(
            (CANVAS_WIDTH - arrow_width - 35, CANVAS_HEIGHT - 60),
            arrow,
            font=arrow_font,
            fill=WHITE
        )
    
    return canvas


def render_cta_slide(canvas):
    """Render the CTA slide (last slide) with large centered logo"""
    
    # Create solid blue overlay
    overlay = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (*RENDI_BLUE_DARK, 230))
    canvas.paste(overlay, (0, 0), overlay)
    
    draw = ImageDraw.Draw(canvas)
    
    # Load and draw large logo
    try:
        resp = requests.get(LOGO_URL, timeout=10)
        resp.raise_for_status()
        logo_large = Image.open(io.BytesIO(resp.content))
        logo_large = logo_large.convert("RGBA")
        
        # Make logo larger for CTA
        max_height = 120
        ratio = max_height / logo_large.height
        new_width = int(logo_large.width * ratio)
        logo_large = logo_large.resize((new_width, max_height), Image.LANCZOS)
        
        # Center the logo (adjusted for taller canvas)
        logo_x = (CANVAS_WIDTH - new_width) // 2
        logo_y = 500
        canvas.paste(logo_large, (logo_x, logo_y), logo_large)
    except Exception as e:
        print(f"⚠️ CTA logo error: {e}")
    
    # Reload draw after paste
    draw = ImageDraw.Draw(canvas)
    
    # Tagline line 1
    tagline1 = "Architectural Visualization"
    bbox1 = draw.textbbox((0, 0), tagline1, font=tagline_font)
    tagline1_x = (CANVAS_WIDTH - (bbox1[2] - bbox1[0])) // 2
    draw.text((tagline1_x, 670), tagline1, font=tagline_font, fill=LIGHT_BLUE)
    
    # Tagline line 2
    tagline2 = "for Real Estate Development"
    bbox2 = draw.textbbox((0, 0), tagline2, font=tagline_font)
    tagline2_x = (CANVAS_WIDTH - (bbox2[2] - bbox2[0])) // 2
    draw.text((tagline2_x, 720), tagline2, font=tagline_font, fill=LIGHT_BLUE)
    
    # Divider line
    line_width = 200
    line_x = (CANVAS_WIDTH - line_width) // 2
    draw.line([(line_x, 790), (line_x + line_width, 790)], fill=WHITE, width=2)
    
    # Website
    website = DEFAULT_WEBSITE
    bbox = draw.textbbox((0, 0), website, font=website_font)
    website_x = (CANVAS_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((website_x, 820), website, font=website_font, fill=WHITE)
    
    return canvas


# =========================
# ROUTES
# =========================

@app.route('/')
def home():
    return jsonify({
        "service": "Rendimension Brand Engine",
        "version": "2.0",
        "status": "running",
        "brand": DEFAULT_BRAND_NAME,
        "features": [
            "blue_gradient_overlay",
            "9_slide_carousels",
            "text_wrapping",
            "cta_slide",
            "logo_support",
            "4:5_vertical_format"
        ],
        "canvas_size": f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}",
        "font_sizes": {
            "headline": 34,
            "big_text": 56,
            "description": 30
        },
        "fonts": {
            "Montserrat-Bold": os.path.isfile(FONT_BOLD_PATH),
        },
        "images_in_cache": len(generated_images)
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': '2.0',
        'brand': 'Rendimension',
        'canvas': '1080x1350',
        'images_in_cache': len(generated_images)
    })


@app.route('/post_output/<filename>')
def serve_output(filename):
    return send_from_directory(POST_OUTPUT_DIR, filename)


@app.route('/download/<image_id>')
def download_image(image_id):
    """Download generated image by ID"""
    try:
        if image_id not in generated_images:
            return jsonify({'error': 'Image not found or expired'}), 404
        
        image_data = generated_images[image_id]['data']
        img_buffer = io.BytesIO(image_data)
        img_buffer.seek(0)
        
        return send_file(
            img_buffer,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'rendimension_{image_id}.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/render-slide', methods=['POST'])
def render_slide_endpoint():
    """Main endpoint for n8n"""
    try:
        cleanup_old_images()
        
        data = request.get_json(force=True)
        
        # Get image
        image_source = None
        
        if data.get('image_base64'):
            image_data = base64.b64decode(data['image_base64'])
            image_source = Image.open(io.BytesIO(image_data))
        elif data.get('image_url'):
            image_source = data['image_url']
        else:
            return jsonify({"error": "No image provided (need image_url or image_base64)"}), 400
        
        # Get text params
        headline = data.get('headline', '')
        big_text = data.get('big_text', data.get('subtitle', ''))
        description = data.get('description', '')
        
        # Slide position
        slide_number = data.get('slide_number', 1)
        total_slides = data.get('total_slides', 9)
        show_arrow = data.get('show_arrow', True)
        show_website = data.get('show_website', True)
        is_cta = data.get('is_cta', False)
        
        # Render
        img = render_slide(
            image_source=image_source,
            headline=headline,
            big_text=big_text,
            description=description,
            slide_number=slide_number,
            total_slides=total_slides,
            show_arrow=show_arrow,
            show_website=show_website,
            is_cta=is_cta
        )
        
        # Save to buffer
        img_buffer = io.BytesIO()
        img.convert("RGB").save(img_buffer, format='PNG', quality=95)
        img_buffer.seek(0)
        
        # Store in cache
        image_id = str(uuid.uuid4())
        generated_images[image_id] = {
            'data': img_buffer.getvalue(),
            'timestamp': time.time()
        }
        
        # Save to file
        filename = f"slide_{image_id}.png"
        output_path = os.path.join(POST_OUTPUT_DIR, filename)
        img.convert("RGB").save(output_path, format='PNG', quality=95)
        
        # Build URLs
        base_url = request.host_url.rstrip('/')
        
        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": f"{base_url}/download/{image_id}",
            "png_url": f"{base_url}/post_output/{filename}",
            "image_id": image_id,
            "slide_number": slide_number,
            "is_cta": is_cta or slide_number == total_slides
        })
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Rendimension Brand Engine v2.0 starting on port {port}")
    print(f"📍 Brand: {DEFAULT_BRAND_NAME}")
    print(f"📍 Canvas: {CANVAS_WIDTH}x{CANVAS_HEIGHT} (4:5 vertical)")
    print(f"📍 Fonts: Headline 34pt | Big Text 56pt | Description 30pt")
    print(f"📍 Logo: {LOGO_URL}")
    print(f"📍 Website: {DEFAULT_WEBSITE}")
    app.run(host='0.0.0.0', port=port, debug=False)
