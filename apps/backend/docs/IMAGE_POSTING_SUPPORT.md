# Image Support in Social Media Posting

## Overview
Social media posting now supports images for both LinkedIn and Twitter. Images are automatically downloaded and uploaded to the respective platforms.

## Features

### ✅ LinkedIn Image Support
- Automatic image registration with LinkedIn API
- Binary upload to LinkedIn storage
- Image attached to posts with proper URNs
- Fallback to text-only if image upload fails

### ✅ Twitter Media Support  
- Media upload via Twitter v1.1 API
- Media ID attachment to tweets (v2 API)
- Support for images in tweets
- Graceful degradation to text-only

## API Changes

### Updated ShareRequest Model
```python
{
  "platform": "linkedin" | "twitter",
  "content": "Post text content",
  "title": "Optional post title",
  "url": "Optional article link",
  "image_url": "URL to image (NEW)",  # ⭐ New field
  "target_urn": "Optional organization URN"
}
```

## Usage Examples

### 1. Post with Generated Image (from /generate)

```python
# Step 1: Generate content with image
response = requests.post("/v1/content/generate", json={
    "prompt": "Write about AI",
    "intent": "blog"
})

content = response.json()["content"]
image_url = response.json()["image_url"]  # DALL-E generated

# Step 2: Post to LinkedIn with image
requests.post("/v1/social/share", json={
    "platform": "linkedin",
    "content": content[:1000],
    "image_url": image_url  # Pass the generated image
})
```

### 2. Post with External Image

```python
requests.post("/v1/social/share", json={
    "platform": "twitter",
    "content": "Check out this amazing tech!",
    "image_url": "https://example.com/image.jpg"
})
```

### 3. Post Text + URL + Image

```python
requests.post("/v1/social/share", json={
    "platform": "linkedin",
    "content": "Read my latest blog post!",
    "url": "https://myblog.com/post",
    "title": "AI Revolution",
    "image_url": "https://myblog.com/cover.jpg"
})
```

## How It Works

### LinkedIn Flow:
```
1. Download image from URL
2. Register upload with LinkedIn API
   → Get uploadUrl and asset URN
3. Upload binary to uploadUrl
4. Create post with asset URN in media field
5. Set shareMediaCategory = "IMAGE"
```

### Twitter Flow:
```
1. Download image from URL
2. Upload to upload.twitter.com/1.1/media/upload
   → Get media_id_string
3. Create tweet with media_ids array
```

## Priority Handling

The system uses this priority for post types:

**LinkedIn:**
```
Image > URL (article) > Text only
```

**Twitter:**
```
Image > Text with embedded URL > Text only
```

## Error Handling

- If image download fails → Post text only
- If image upload fails → Post text only  
- Logs all failures for debugging
- Returns 500 with error details if posting fails

## Image Requirements

### LinkedIn:
- Supported formats: JPG, PNG, GIF
- Max size: 10 MB
- Recommended: 1200x627px

### Twitter:
- Supported formats: JPG, PNG, GIF, WebP
- Max size: 5 MB
- Max dimensions: 1024x512px for cards

## Implementation Details

### New Methods in SocialPublisher:

```python
# LinkedIn
register_image_upload(access_token, user_urn) → {uploadUrl, asset}
upload_image_binary(upload_url, access_token, image_data)
publish_to_linkedin(..., image_data=None)  # Updated

# Twitter
upload_twitter_media(access_token, image_data) → media_id
post_tweet(access_token, text, image_data=None)  # Updated
```

### Share Endpoint Updates:

1. Added `image_url` to ShareRequest
2. Downloads image if URL provided
3. Passes binary data to publishers
4. Handles errors gracefully

## Testing

Run the test script:
```bash
cd apps/backend
python scripts/test_image_posting.py
```

Tests:
- ✅ Generate content with DALL-E image
- ✅ Post to LinkedIn with image
- ✅ Post to Twitter with image
- ✅ Post with external image URL

## Troubleshooting

### "Failed to register image upload"
- Check LinkedIn access token has `w_member_social` scope
- Verify URN format is correct (`urn:li:person:xxx`)

### "Failed to upload Twitter media"
- Check token has `tweet.write` scope
- Verify image size < 5 MB

### "Image download error"
- Check image URL is publicly accessible
- Verify DALL-E URLs haven't expired (1 hour TTL)

## Future Enhancements

- [ ] Image caching (store uploaded images)
- [ ] Alt text support for accessibility
- [ ] Multiple images (carousel posts)
- [ ] Video support
- [ ] Image optimization (resize, compress)
- [ ] GIF and animation support
