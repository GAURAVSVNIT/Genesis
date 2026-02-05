# Quick Reference - New Features

## 🎯 Sidebar Editor

### How to Use
1. **Open Sidebar**: Click the panel icon (⊟) in top right header
2. **Edit Content**: Use CKEditor to modify text
3. **Apply Colors**: Use color pickers for text and background
4. **Position Images**: Select image alignment from dropdown
5. **Save**: Click "Save Changes" button
6. **Close**: Click X button or toggle panel icon

### Toolbar Options
```
Undo | Redo
Heading styles
Bold | Italic | Highlight
Text Alignment
Links | Images | Tables
Lists | Block Quotes
Indentation
```

## 🎨 Tone Options

### Available Tones
| Tone | Best For | Characteristics |
|------|----------|-----------------|
| Analytical | Research, Analysis | Multiple perspectives, nuanced |
| Opinionated | Commentary, Opinion Pieces | Bold, conviction-backed |
| Critical | Reviews, Critiques | Strengths AND weaknesses |
| Investigative | Deep Dives, Reporting | Patterns, hidden layers |
| Contrarian | Counter-narratives | Challenges consensus |

### Enhancement Options
```
☑ Include Critique
  → Shows weaknesses and limitations
  
☑ Include Alternative Perspectives  
  → Shows what critics say
  
☑ Include Real-World Implications
  → Shows consequences and trade-offs
```

## 📝 Format Options

### Output Formats
- **markdown**: Headers, lists, quotes, bold/italic
- **html**: Semantic HTML tags
- **plain**: Simple text format
- **structured**: Sections with clear hierarchy

### Word Limit
- Set max_words to limit output length
- Actual count returned in response
- Example: max_words=500

### Sections
- Automatic section detection
- Headers count returned
- Typical structure:
  1. Introduction
  2. Main Points
  3. Critical Analysis
  4. Implications
  5. Conclusion

## 🔧 API Request Example

```json
POST /v1/content/generate
Content-Type: application/json

{
  "prompt": "Write about the future of AI",
  "tone": "analytical",
  "include_critique": true,
  "include_alternatives": true,
  "include_implications": true,
  "format": "markdown",
  "max_words": 800,
  "include_sections": true,
  "safety_level": "moderate"
}
```

## 📊 Response Data

```json
{
  "success": true,
  "content": "...",
  "tone_applied": "analytical",
  "includes_critique": true,
  "includes_alternatives": true,
  "includes_implications": true,
  "analysis_depth": "comprehensive",
  "format_applied": "markdown",
  "word_count": 756,
  "sections_count": 5,
  "seo_score": 0.82,
  "uniqueness_score": 0.91,
  "engagement_score": 0.88,
  "generation_time_ms": 2345,
  "image_url": "https://..."
}
```

## 🎯 Quick Actions

### To Enable Comprehensive Analysis
```
✓ tone: "analytical" or "critical" or "investigative"
✓ include_critique: true
✓ include_alternatives: true
✓ include_implications: true
```

### To Get Concise Formatted Output
```
✓ format: "structured"
✓ max_words: 500
✓ include_sections: true
```

### To Get Bold Opinion Piece
```
✓ tone: "opinionated"
✓ include_critique: true
✓ format: "markdown"
```

## 🖼️ Color Picker Guide

### Text Colors
- Black: Standard, professional
- Slate: Secondary, subtle
- Blue: Accent, important
- Red: Alert, warning
- Green: Success, positive
- Purple: Creative, alternative

### Background Colors
- White: Clean, professional
- Slate: Subtle contrast
- Blue: Calm, trust
- Yellow: Attention, warning
- Green: Growth, positive
- Purple: Creative, unique

## 🎬 Workflow Examples

### Example 1: Create Opinion Piece
1. Input: "Is crypto the future?"
2. Select tone: "opinionated"
3. Check: Include Critique ✓
4. Format: markdown
5. Generate
6. Edit in sidebar if needed
7. Save

### Example 2: Deep Analysis
1. Input: "Climate change solutions"
2. Select tone: "analytical"
3. Check all enhancement options ✓
4. Format: structured
5. Set max_words: 1000
6. Generate
7. Review 5-section structure
8. Edit specific sections if needed

### Example 3: Investigate Topic
1. Input: "Why companies fail"
2. Select tone: "investigative"
3. Check alternatives ✓
4. Format: markdown
5. Generate
6. Use sidebar to refine
7. Apply colors to key points
8. Save final version

## ⚙️ Settings Tips

### For SEO-Optimized Content
- Use tone: "analytical"
- Include all enhancements ✓
- Format: "structured"
- Length: "medium" or "long"

### For Social Media
- Tone: "opinionated" or "contrarian"
- Format: "plain" or "markdown"
- Keep max_words low (200-300)
- Include critique for engagement

### For Academic Writing
- Tone: "analytical"
- Include all enhancements ✓
- Format: "markdown"
- Longer word limit (1000+)

### For Quick Newsletter
- Tone: "opinionated"
- Include alternatives only
- Format: "structured"
- max_words: 400
