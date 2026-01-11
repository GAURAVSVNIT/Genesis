# Regenerate Image API - Improvements

## Overview
The regenerate image endpoint has been significantly enhanced to provide better control and smarter image generation based on blog content.

## What's New

### 1. **Automatic Tone Detection**
- No longer hardcoded to "neutral"
- Intelligently infers tone from content:
  - `technical` - API docs, code tutorials, architecture
  - `professional` - Business, enterprise, strategy
  - `casual` - Conversational, friendly blogs
  - `educational` - Tutorials, guides, how-tos
  - `inspirational` - Motivational, transformation stories
  - `neutral` - Default fallback

### 2. **Style Preferences**
Choose from predefined styles:
- `photorealistic` - High-detail photography
- `illustration` - Digital art, vibrant
- `3d_render` - Modern 3D graphics
- `minimalist` - Clean, simple design
- `cinematic` - Dramatic, film-like

### 3. **Smart Content Parsing**
- Prioritizes title and first paragraphs over full content
- Extracts keywords from most relevant sections
- Creates intelligent summaries (first 3 paragraphs)
- Better context for image generation

### 4. **Customization Options**
- **Specific Focus**: Emphasize particular elements
- **Exclude Elements**: Avoid unwanted content (e.g., text, logos, people)
- **Variation Level**: Control creativity
  - `low` - Consistent style
  - `medium` - Creative variations (default)
  - `high` - Bold interpretations

## API Changes

### Request Model (Before)
```python
{
  "content": "string"
}
```

### Request Model (After)
```python
{
  "content": "string",                      # Required
  "tone": "string",                         # Optional - auto-detected if not provided
  "style_preference": "string",             # Optional
  "specific_focus": "string",               # Optional
  "exclude_elements": ["string"],           # Optional
  "variation_level": "medium"               # Optional: low/medium/high
}
```

## Usage Examples

### Basic Usage (Auto-detect)
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/content/regenerate-image",
    json={
        "content": "Your blog post content here..."
    }
)
```

### With Style Preference
```python
response = requests.post(
    "http://localhost:8000/v1/content/regenerate-image",
    json={
        "content": "Technical blog about cloud architecture...",
        "style_preference": "minimalist",
        "tone": "technical"  # or let it auto-detect
    }
)
```

### Full Control
```python
response = requests.post(
    "http://localhost:8000/v1/content/regenerate-image",
    json={
        "content": "Blog post content...",
        "tone": "professional",
        "style_preference": "cinematic",
        "specific_focus": "cloud servers and data flow",
        "exclude_elements": ["people", "text", "logos"],
        "variation_level": "high"
    }
)
```

## Benefits

1. **Better Image Relevance**: Smarter keyword extraction from titles and key paragraphs
2. **Tone-Aware Generation**: Images match content mood and style
3. **User Control**: Specify exactly what you want/don't want
4. **Flexibility**: Works great with defaults or fine-tuned control
5. **Consistency**: Variation control prevents wildly different results

## Testing

Run the test script:
```bash
cd apps/backend
uv run python scripts/test_regenerate_improved.py
```

## Implementation Details

### Tone Inference Algorithm
Uses keyword frequency analysis across multiple categories:
- Technical terms (algorithm, API, framework)
- Professional terms (enterprise, strategy, business)
- Casual patterns (!, ?, hey, awesome)
- Educational terms (learn, tutorial, guide)
- Inspirational terms (inspire, achieve, transform)

### Prompt Enhancement Pipeline
1. Extract keywords from title/first paragraphs
2. Infer tone from content patterns
3. Create smart summary (first 3 paragraphs)
4. Generate base prompt via AI Art Director
5. Enhance with user preferences
6. Add style, exclusions, variation instructions

## Migration Notes

**Backward Compatible**: Old requests with just `content` field still work perfectly!

```python
# Old code - still works!
{"content": "blog content"}

# New code - enhanced control
{"content": "blog content", "style_preference": "minimalist"}
```
