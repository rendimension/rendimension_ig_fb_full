# Rendimension Brand Engine

Image compositor for Rendimension social media automation.

## Features

- **Blue gradient overlays**: Top and bottom
- **Logo integration**: Small top-left logo
- **8-slide carousels**: With CTA on last slide
- **Text wrapping**: Auto-wrap long text
- **Square 1:1 format**: Optimized for Instagram/Facebook

## Brand Colors

- Primary: `#1E3A8A` (Rendimension Blue)
- Text: White / Light Blue

## API Endpoints

### POST /render-slide

Main endpoint for n8n automation.

**Request body:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "headline": "DESIGN SMARTER",
  "big_text": "Your Vision, Visualized",
  "description": "See your project before breaking ground.",
  "slide_number": 1,
  "total_slides": 8,
  "show_arrow": true,
  "is_cta": false
}
```

**Response:**
```json
{
  "success": true,
  "download_url": "https://xxx.railway.app/download/uuid",
  "png_url": "https://xxx.railway.app/post_output/slide_uuid.png"
}
```

## Environment Variables

- `BRAND_NAME` - Default: "RENDIMENSION"
- `TAGLINE` - Default: "Architectural Visualization for Real Estate Development"
- `WEBSITE_URL` - Default: "www.rendimension.com"
- `LOGO_URL` - Default: Cloudinary logo URL

## Deployment

1. Push to GitHub
2. Connect to Railway
3. Deploy (uses NIXPACKS, no Dockerfile needed)
