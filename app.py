"""
Rendimension Slide Compositor
Creates branded Instagram/Facebook carousel slides with:
- Blue gradient overlays (top and bottom)
- Small logo top-left
- Headline + Big Text + Description (3-4 lines with bullets)
- Slide 8: CTA with large centered logo
"""

from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
import os
import tempfile
import textwrap
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================

# Cloudinary config
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dotimxrnh'),
    api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', '')
)

# Canvas dimensions (Instagram square)
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1080

# Colors (Rendimension blue palette)
GRADIENT_TOP_START = (30, 58, 138, 200)      # #1E3A8A with alpha
GRADIENT_TOP_END = (30, 58, 138, 0)          # Transparent
GRADIENT_BOTTOM_START = (30, 64, 175, 0)     # Transparent
GRADIENT_BOTTOM_END = (30, 58, 138, 255)     # #1E3A8A solid
TEXT_COLOR_WHITE = (255, 255, 255)
TEXT_COLOR_LIGHT = (220, 230, 255)

# Layout dimensions
LOGO_HEIGHT = 50
LOGO_MARGIN_TOP = 30
LOGO_MARGIN_LEFT = 30

GRADIENT_TOP_HEIGHT = 120
GRADIENT_BOTTOM_HEIGHT = 380  # Increased for more text space

TEXT_AREA_TOP = CANVAS_HEIGHT - GRADIENT_BOTTOM_HEIGHT + 40
HEADLINE_Y = TEXT_AREA_TOP
BIG_TEXT_Y = TEXT_AREA_TOP + 55
DESCRIPTION_Y = BIG_TEXT_Y + 70

# Font paths (will try multiple options)
FONT_PATHS = {
    'headline': [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        'arial.ttf'
    ],
    'big_text': [
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
        'times.ttf'
    ],
    'description': [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        'arial.ttf'
    ]
}

# Logo URL
LOGO_URL = "https://res.cloudinary.com/dotimxrnh/image/upload/v1772757400/LOGO_FOR_STREAMING_v0aph8.png"

# Cache for loaded assets
_logo_cache = None
_font_cache = {}


def get_font(font_type, size):
    """Load font with fallback options"""
    cache_key = f"{font_type}_{size}"
    if cache_key in _font_cache:
        return _font_cache[cache_key]
    
    for path in FONT_PATHS.get(font_type, FONT_PATHS['description']):
        try:
            font = ImageFont.truetype(path, size)
            _font_cache[cache_key] = font
            return font
        except (OSError, IOError):
            continue
    
    # Ultimate fallback
    font = ImageFont.load_default()
    _font_cache[cache_key] = font
    return font


def load_logo():
    """Load and cache the Rendimension logo"""
    global _logo_cache
    if _logo_cache is not None:
        return _logo_cache
    
    try:
        response = requests.get(LOGO_URL, timeout=10)
        response.raise_for_status()
        logo = Image.open(BytesIO(response.content)).convert('RGBA')
        
        # Resize maintaining aspect ratio
        aspect = logo.width / logo.height
        new_height = LOGO_HEIGHT
        new_width = int(new_height * aspect)
        logo = logo.resize((new_width, new_height), Image.LANCZOS)
        
        _logo_cache = logo
        return logo
    except Exception as e:
        print(f"Error loading logo: {e}")
        return None


def create_gradient_overlay(width, height, start_color, end_color, direction='vertical'):
    """Create a gradient overlay image"""
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    if direction == 'vertical':
        for y in range(height):
            ratio = y / height
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            a = int(start_color[3] + (end_color[3] - start_color[3]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    return overlay


def wrap_text_smart(text, font, max_width, draw):
    """Wrap text intelligently without cutting words"""
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


def render_slide(image_url, headline, big_text, description, slide_number, total_slides, 
                 show_arrow=True, is_cta=False):
    """
    Render a single carousel slide with Rendimension branding
    """
    
    # Load background image
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        background = Image.open(BytesIO(response.content)).convert('RGBA')
    except Exception as e:
        print(f"Error loading background: {e}")
        # Create fallback gradient background
        background = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (30, 58, 138, 255))
    
    # Resize/crop to canvas size
    bg_aspect = background.width / background.height
    canvas_aspect = CANVAS_WIDTH / CANVAS_HEIGHT
    
    if bg_aspect > canvas_aspect:
        # Image is wider - fit height, crop width
        new_height = CANVAS_HEIGHT
        new_width = int(new_height * bg_aspect)
    else:
        # Image is taller - fit width, crop height
        new_width = CANVAS_WIDTH
        new_height = int(new_width / bg_aspect)
    
    background = background.resize((new_width, new_height), Image.LANCZOS)
    
    # Center crop
    left = (new_width - CANVAS_WIDTH) // 2
    top = (new_height - CANVAS_HEIGHT) // 2
    background = background.crop((left, top, left + CANVAS_WIDTH, top + CANVAS_HEIGHT))
    
    # Create canvas
    canvas = background.copy()
    
    # Add top gradient overlay
    top_gradient = create_gradient_overlay(
        CANVAS_WIDTH, GRADIENT_TOP_HEIGHT,
        GRADIENT_TOP_START, GRADIENT_TOP_END
    )
    canvas.paste(top_gradient, (0, 0), top_gradient)
    
    # Add bottom gradient overlay
    bottom_gradient = create_gradient_overlay(
        CANVAS_WIDTH, GRADIENT_BOTTOM_HEIGHT,
        GRADIENT_BOTTOM_START, GRADIENT_BOTTOM_END
    )
    canvas.paste(bottom_gradient, (0, CANVAS_HEIGHT - GRADIENT_BOTTOM_HEIGHT), bottom_gradient)
    
    # Add logo (top-left, small)
    logo = load_logo()
    if logo:
        canvas.paste(logo, (LOGO_MARGIN_LEFT, LOGO_MARGIN_TOP), logo)
    
    # Create draw object for text
    draw = ImageDraw.Draw(canvas)
    
    # Load fonts
    font_headline = get_font('headline', 28)
    font_big_text = get_font('big_text', 48)
    font_description = get_font('description', 24)
    
    if is_cta:
        # CTA SLIDE (Slide 8) - Different layout
        render_cta_slide(canvas, draw)
    else:
        # REGULAR SLIDE - Headline + Big Text + Description
        
        # Draw headline (smaller, top of text area)
        if headline:
            headline_upper = headline.upper()
            bbox = draw.textbbox((0, 0), headline_upper, font=font_headline)
            headline_width = bbox[2] - bbox[0]
            headline_x = (CANVAS_WIDTH - headline_width) // 2
            
            # Add subtle shadow
            draw.text((headline_x + 2, HEADLINE_Y + 2), headline_upper, 
                     font=font_headline, fill=(0, 0, 0, 100))
            draw.text((headline_x, HEADLINE_Y), headline_upper, 
                     font=font_headline, fill=TEXT_COLOR_LIGHT)
        
        # Draw big text (larger, main message)
        if big_text:
            # Wrap if too long
            max_width = CANVAS_WIDTH - 80
            lines = wrap_text_smart(big_text, font_big_text, max_width, draw)
            
            y_offset = BIG_TEXT_Y
            for line in lines[:2]:  # Max 2 lines for big text
                bbox = draw.textbbox((0, 0), line, font=font_big_text)
                line_width = bbox[2] - bbox[0]
                line_x = (CANVAS_WIDTH - line_width) // 2
                
                # Shadow
                draw.text((line_x + 2, y_offset + 2), line, 
                         font=font_big_text, fill=(0, 0, 0, 150))
                draw.text((line_x, y_offset), line, 
                         font=font_big_text, fill=TEXT_COLOR_WHITE)
                y_offset += 55
        
        # Draw description (with bullets if multiple lines)
        if description:
            max_width = CANVAS_WIDTH - 120
            lines = wrap_text_smart(description, font_description, max_width, draw)
            
            y_offset = DESCRIPTION_Y
            for i, line in enumerate(lines[:4]):  # Max 4 lines
                # Add bullet for lines after the first if there are multiple
                if len(lines) > 1 and i > 0:
                    display_line = f"• {line}"
                elif len(lines) > 1 and i == 0:
                    display_line = f"• {line}"
                else:
                    display_line = line
                
                bbox = draw.textbbox((0, 0), display_line, font=font_description)
                line_width = bbox[2] - bbox[0]
                line_x = (CANVAS_WIDTH - line_width) // 2
                
                # Shadow
                draw.text((line_x + 1, y_offset + 1), display_line, 
                         font=font_description, fill=(0, 0, 0, 100))
                draw.text((line_x, y_offset), display_line, 
                         font=font_description, fill=TEXT_COLOR_LIGHT)
                y_offset += 32
        
        # Draw arrow indicator (if not last slide)
        if show_arrow and slide_number < total_slides:
            arrow_font = get_font('headline', 36)
            arrow = "→"
            bbox = draw.textbbox((0, 0), arrow, font=arrow_font)
            arrow_width = bbox[2] - bbox[0]
            arrow_x = CANVAS_WIDTH - arrow_width - 30
            arrow_y = CANVAS_HEIGHT - 50
            
            draw.text((arrow_x, arrow_y), arrow, font=arrow_font, fill=TEXT_COLOR_WHITE)
    
    # Convert to RGB for saving as PNG
    canvas_rgb = Image.new('RGB', canvas.size, (30, 58, 138))
    canvas_rgb.paste(canvas, mask=canvas.split()[3] if canvas.mode == 'RGBA' else None)
    
    return canvas_rgb


def render_cta_slide(canvas, draw):
    """Render the CTA slide (Slide 8) with large centered logo"""
    
    # Create solid blue background for CTA
    blue_overlay = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (30, 58, 138, 230))
    canvas.paste(blue_overlay, (0, 0), blue_overlay)
    
    # Load and display large logo
    try:
        response = requests.get(LOGO_URL, timeout=10)
        response.raise_for_status()
        logo_large = Image.open(BytesIO(response.content)).convert('RGBA')
        
        # Make logo larger for CTA
        logo_height = 120
        aspect = logo_large.width / logo_large.height
        logo_width = int(logo_height * aspect)
        logo_large = logo_large.resize((logo_width, logo_height), Image.LANCZOS)
        
        # Center the logo
        logo_x = (CANVAS_WIDTH - logo_width) // 2
        logo_y = 350
        canvas.paste(logo_large, (logo_x, logo_y), logo_large)
    except Exception as e:
        print(f"Error loading large logo for CTA: {e}")
    
    # Reload draw object after pasting
    draw = ImageDraw.Draw(canvas)
    
    # Fonts for CTA
    font_tagline = get_font('description', 28)
    font_website = get_font('headline', 32)
    
    # Tagline
    tagline = "Architectural Visualization"
    tagline2 = "for Real Estate Development"
    
    bbox1 = draw.textbbox((0, 0), tagline, font=font_tagline)
    tagline_x = (CANVAS_WIDTH - (bbox1[2] - bbox1[0])) // 2
    draw.text((tagline_x, 520), tagline, font=font_tagline, fill=TEXT_COLOR_LIGHT)
    
    bbox2 = draw.textbbox((0, 0), tagline2, font=font_tagline)
    tagline2_x = (CANVAS_WIDTH - (bbox2[2] - bbox2[0])) // 2
    draw.text((tagline2_x, 555), tagline2, font=font_tagline, fill=TEXT_COLOR_LIGHT)
    
    # Divider line
    line_y = 610
    line_width = 200
    line_x_start = (CANVAS_WIDTH - line_width) // 2
    draw.line([(line_x_start, line_y), (line_x_start + line_width, line_y)], 
              fill=TEXT_COLOR_WHITE, width=2)
    
    # Website
    website = "www.rendimension.com"
    bbox = draw.textbbox((0, 0), website, font=font_website)
    website_x = (CANVAS_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((website_x, 650), website, font=font_website, fill=TEXT_COLOR_WHITE)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "rendimension-compositor"})


@app.route('/render-slide', methods=['POST'])
def api_render_slide():
    """
    API endpoint to render a single slide
    
    Expected JSON body:
    {
        "image_url": "https://...",
        "headline": "DESIGN SMARTER",
        "big_text": "Your Vision, Visualized",
        "description": "See your project before breaking ground. Make confident decisions.",
        "slide_number": 1,
        "total_slides": 8,
        "show_arrow": true,
        "is_cta": false
    }
    """
    try:
        data = request.get_json()
        
        image_url = data.get('image_url', '')
        headline = data.get('headline', '')
        big_text = data.get('big_text', '')
        description = data.get('description', '')
        slide_number = data.get('slide_number', 1)
        total_slides = data.get('total_slides', 8)
        show_arrow = data.get('show_arrow', True)
        is_cta = data.get('is_cta', False) or slide_number == 8
        
        # Render the slide
        rendered = render_slide(
            image_url=image_url,
            headline=headline,
            big_text=big_text,
            description=description,
            slide_number=slide_number,
            total_slides=total_slides,
            show_arrow=show_arrow,
            is_cta=is_cta
        )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            rendered.save(tmp.name, 'PNG', quality=95)
            tmp_path = tmp.name
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            tmp_path,
            folder="rendimension_composed",
            resource_type="image"
        )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return jsonify({
            "success": True,
            "slide_number": slide_number,
            "png_url": upload_result.get('secure_url'),
            "download_url": upload_result.get('secure_url'),
            "public_id": upload_result.get('public_id')
        })
        
    except Exception as e:
        print(f"Error rendering slide: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/render-slide-local', methods=['POST'])
def api_render_slide_local():
    """
    Render slide and return the image directly (for testing)
    """
    try:
        data = request.get_json()
        
        rendered = render_slide(
            image_url=data.get('image_url', ''),
            headline=data.get('headline', ''),
            big_text=data.get('big_text', ''),
            description=data.get('description', ''),
            slide_number=data.get('slide_number', 1),
            total_slides=data.get('total_slides', 8),
            show_arrow=data.get('show_arrow', True),
            is_cta=data.get('is_cta', False)
        )
        
        # Return image directly
        img_buffer = BytesIO()
        rendered.save(img_buffer, 'PNG')
        img_buffer.seek(0)
        
        return send_file(img_buffer, mimetype='image/png')
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
