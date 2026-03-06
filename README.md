# Rendimension Slide Compositor

Flask API for compositing branded Instagram/Facebook carousel slides for Rendimension.

## Features

- Blue gradient overlays (top and bottom)
- Small logo positioned top-left
- 8-slide structure with Headline + Big Text + Description
- Smart text wrapping (no word cutting)
- Bullet points for multi-line descriptions
- Slide 8 CTA with large centered logo
- Arrow indicators for navigation
- Automatic Cloudinary upload

## API Endpoints

### POST /render-slide

Renders a single carousel slide and uploads to Cloudinary.

**Request Body:**
```json
{
  "image_url": "https://example.com/render.jpg",
  "headline": "DESIGN SMARTER",
  "big_text": "Your Vision, Visualized",
  "description": "See your project before breaking ground. Make confident decisions early.",
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
  "slide_number": 1,
  "png_url": "https://res.cloudinary.com/...",
  "download_url": "https://res.cloudinary.com/...",
  "public_id": "rendimension_composed/..."
}
```

### GET /health

Health check endpoint.

## Deployment to Railway

### Option 1: Deploy from GitHub

1. Push this code to a GitHub repository
2. Go to [Railway](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables:
   - `CLOUDINARY_CLOUD_NAME`: dotimxrnh
   - `CLOUDINARY_API_KEY`: your_key
   - `CLOUDINARY_API_SECRET`: your_secret
6. Deploy!

### Option 2: Deploy with Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init

# Deploy
railway up

# Add environment variables
railway variables set CLOUDINARY_CLOUD_NAME=dotimxrnh
railway variables set CLOUDINARY_API_KEY=your_key
railway variables set CLOUDINARY_API_SECRET=your_secret
```

## Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CLOUDINARY_CLOUD_NAME=dotimxrnh
export CLOUDINARY_API_KEY=your_key
export CLOUDINARY_API_SECRET=your_secret

# Run
python app.py
```

## Slide Structure

### Slides 1-7: Content Slides
- **Top gradient**: Blue fade from top
- **Logo**: Small, top-left corner
- **Bottom gradient**: Solid blue area for text
- **Headline**: Small caps, light blue
- **Big Text**: Large, bold, white (up to 2 lines)
- **Description**: Regular text with bullets (up to 4 lines)
- **Arrow**: Navigation indicator (→)

### Slide 8: CTA Slide
- **Background**: Solid blue overlay
- **Logo**: Large, centered
- **Tagline**: "Architectural Visualization for Real Estate Development"
- **Divider**: Horizontal line
- **Website**: www.rendimension.com

## Integration with n8n

Update the HTTP Request node URL to point to your Railway deployment:

```
https://your-app.up.railway.app/render-slide
```

## Color Palette

- Primary Blue: `#1E3A8A` (RGB: 30, 58, 138)
- Secondary Blue: `#1E40AF` (RGB: 30, 64, 175)
- Text White: `#FFFFFF`
- Text Light: `#DCE6FF`
