# Technical Implementation Details

## Backend Architecture

### Tone Enhancement System (`intelligence/tone_enhancer.py`)

#### Core Functions

1. **`get_enhanced_system_prompt()`**
   - Generates system prompt with selected tone
   - Adds critical thinking guidelines
   - Includes multiple perspective instructions
   - Returns complete prompt for LLM

2. **`get_content_enrichment_prompt()`**
   - Adds 4 enrichment sections:
     - Critical Analysis
     - Alternative Perspectives
     - Real-World Implications
     - Questions to Consider
   - Can be appended to main prompt

3. **`get_formatted_output_prompt()`**
   - NEW: Controls output format directly
   - Supports: markdown, html, plain, structured
   - Enforces word limits
   - Manages section creation
   - Returns format-specific instructions

#### Tone Configurations

```python
TONE_CONFIGS = {
    "analytical": {
        "system": "thoughtful analyst and critic",
        "emphasis": "critical_analysis"
    },
    "opinionated": {
        "system": "bold commentator with strong opinions",
        "emphasis": "personal_perspective"
    },
    "critical": {
        "system": "discerning critic",
        "emphasis": "critical_evaluation"
    },
    "investigative": {
        "system": "investigative journalist",
        "emphasis": "deep_investigation"
    },
    "contrarian": {
        "system": "thoughtful contrarian",
        "emphasis": "alternative_perspectives"
    }
}
```

### API Endpoint Changes (`api/v1/content.py`)

#### Request Model Updates
```python
class GenerateContentRequest(BaseModel):
    # Existing fields
    prompt: str
    conversation_history: Optional[List[Message]] = None
    safety_level: str = "moderate"
    guestId: Optional[str] = None
    
    # NEW tone fields
    tone: str = "analytical"
    include_critique: bool = True
    include_alternatives: bool = True
    include_implications: bool = True
    
    # NEW formatting fields
    format: str = "markdown"
    max_words: Optional[int] = None
    include_sections: bool = True
```

#### Response Model Updates
```python
class GenerateContentResponse(BaseModel):
    # Existing fields
    success: bool
    content: str
    ...
    
    # NEW tone info
    tone_applied: str = "analytical"
    includes_critique: bool = True
    includes_alternatives: bool = True
    includes_implications: bool = True
    analysis_depth: str = "comprehensive"
    
    # NEW formatting info
    format_applied: str = "markdown"
    word_count: int = 0
    sections_count: int = 0
```

#### Processing Flow

```
1. Rate Limit Check
2. Prompt Hashing
3. Cache Check
   ├─ HIT: Return cached + metadata
   └─ MISS:
      4. Build Enhanced Prompt
         ├─ get_enhanced_system_prompt()
         ├─ get_content_enrichment_prompt()
         └─ get_formatted_output_prompt()
      5. Add System Message to History
      6. Generate via Vertex AI
      7. Calculate Metrics
         ├─ Word count: len(content.split())
         ├─ Section count: regex match '^#{1,3}\s+'
         ├─ Uniqueness: embedding comparison
         └─ Engagement: placeholder
      8. Store & Cache
      9. Return Response with Metadata
```

#### Word Count Calculation
```python
word_count = len(content_str.split())
section_count = len(re.findall(r'^#{1,3}\s+', content_str, re.MULTILINE))
```

## Frontend Architecture

### Sidebar Editor (`components/sidebar-editor.tsx`)

#### State Management
```typescript
interface SidebarEditorProps {
    initialData: string
    onSave: (content: string) => Promise<void>
    onClose: () => void
    title?: string
}

// Internal State
const [content, setContent] = useState(initialData)
const [isSaving, setIsSaving] = useState(false)
const [imagePosition, setImagePosition] = useState('inline')
const [textColor, setTextColor] = useState('black')
const [backgroundColor, setBackgroundColor] = useState('white')
const [isDirty, setIsDirty] = useState(false)
```

#### CKEditor Configuration
```javascript
config={{
    licenseKey: '...', // Production license
    plugins: [
        Essentials, Paragraph, Bold, Italic, List,
        Heading, Link, BlockQuote, Undo, Indent,
        Image, Table, Font, Highlight, Alignment
    ],
    toolbar: [
        'undo', 'redo',
        'heading',
        'bold', 'italic', 'highlight',
        'alignment',
        'link', 'image', 'table',
        'bulletedList', 'numberedList',
        'blockQuote', 'outdent', 'indent'
    ],
    image: {
        styles: ['alignLeft', 'alignCenter', 'alignRight'],
        resizeOptions: [
            { name: 'resizeImage:original', value: null },
            { name: 'resizeImage:50', value: '50' },
            { name: 'resizeImage:75', value: '75' }
        ],
        toolbar: [
            'imageTextAlternative',
            'imageStyle:alignLeft',
            'imageStyle:alignCenter',
            'imageStyle:alignRight',
            '|',
            'resizeImage'
        ]
    }
}}
```

#### Color Scheme
```typescript
TEXT_COLORS = ['black', 'slate-700', 'blue-600', 'red-600', 'green-600', 'purple-600']
BG_COLORS = ['white', 'slate-100', 'blue-50', 'yellow-50', 'green-50', 'purple-50']
IMAGE_POSITIONS = ['inline', 'left', 'center', 'right', 'full']
```

### Chat Interface Updates (`components/chat-interface.tsx`)

#### New State
```typescript
const [showSidebarEditor, setShowSidebarEditor] = useState(false)
const [sidebarEditingId, setSidebarEditingId] = useState<string | null>(null)
```

#### Layout Structure
```jsx
<div className="flex h-screen">
    <div className={cn("flex flex-col flex-1", showSidebarEditor && "w-2/3")}>
        {/* Main Chat Area */}
    </div>
    
    {showSidebarEditor && currentEditingMessage && (
        <div className="w-1/3 border-l">
            <SidebarEditor />
        </div>
    )}
</div>
```

#### Edit Flow
```
User clicks Edit Button
    ↓
setSidebarEditingId(msg.id)
setShowSidebarEditor(true)
    ↓
SidebarEditor mounts with initialData
    ↓
User edits content
    ↓
User clicks Save
    ↓
onSave() called with new content
    ↓
Updates message in state
    ↓
Reflects in main chat area
```

### Tone Options Config (`lib/tone-options.ts`)

```typescript
export const TONE_OPTIONS = {
    analytical: {
        label: "Analytical",
        description: "Critical analysis with multiple perspectives",
        icon: "🔬",
        ideal_for: "Deep dives, research, complex topics"
    },
    // ... other tones
}

export const ANALYSIS_OPTIONS = {
    include_critique: {
        label: "Include Critical Analysis",
        description: "Add critique section identifying weaknesses",
        default: true
    },
    // ... other options
}

export function getRecommendationsForContentType(contentType: string) {
    // Returns optimal settings based on content type
}
```

## Data Flow Diagrams

### Generation Flow
```
┌─────────────────────────┐
│   User Input + Options  │
├─────────────────────────┤
│ tone: "analytical"      │
│ include_critique: true  │
│ format: "markdown"      │
│ max_words: 500          │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   Backend: Generate with Enhancements   │
├─────────────────────────────────────────┤
│ 1. Build Enhanced Prompt                │
│    - Tone system prompt                 │
│    - Enrichment sections                │
│    - Format constraints                 │
│ 2. Call Vertex AI                       │
│ 3. Calculate metadata                   │
│    - Word count                         │
│    - Section count                      │
│    - Quality scores                     │
└────────────┬────────────────────────────┘
             │
             ▼
┌──────────────────────┐
│  Response with Meta  │
├──────────────────────┤
│ content: "..."       │
│ word_count: 475      │
│ sections_count: 4    │
│ tone_applied: "..."  │
└────────────┬─────────┘
             │
             ▼
┌─────────────────────────┐
│   Display in Chat       │
├─────────────────────────┤
│ Show content            │
│ Show metadata badges    │
│ Enable Edit button      │
└─────────────────────────┘
```

### Edit Flow
```
┌──────────────────┐
│ Message Content  │
├──────────────────┤
│ [Edit Button] ◇  │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Open Sidebar Editor             │
├─────────────────────────────────┤
│ Load content into CKEditor      │
│ Show color pickers              │
│ Show format options             │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ User Edits                      │
├─────────────────────────────────┤
│ - Edit text                     │
│ - Apply formatting              │
│ - Change colors                 │
│ - Position images               │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────┬──────────────┐
│ Reset Button │ Save Changes │
└──────────────┴──────┬───────┘
                      │
                      ▼
          ┌──────────────────────┐
          │ Update in State      │
          │ Close Sidebar        │
          │ Reflect in Chat      │
          └──────────────────────┘
```

## Performance Considerations

### Optimization Strategies
1. **Lazy Load CKEditor**: Only load when sidebar opens
2. **Debounce Changes**: Save state efficiently
3. **Memoize Prompts**: Cache tone configurations
4. **Batch Database Writes**: Group metadata updates
5. **Cache Generated Content**: Reuse exact prompts

### Resource Usage
- CKEditor Bundle: ~500KB (loaded on demand)
- Color Picker: CSS-only, <5KB
- Metadata Calculation: O(n) word split
- Sidebar State: Minimal re-renders with React.memo

## Security Considerations

1. **Input Validation**:
   - Max prompt length
   - Allowed tone values (enum)
   - Max word limit validation
   - HTML sanitization in editor

2. **Rate Limiting**:
   - Preserved from original system
   - Applied per user/guest

3. **Safety Checks**:
   - Content guardrails
   - Bias detection
   - Harmful content filtering

## Testing Checklist

- [ ] Generate with each tone option
- [ ] Test enhancement combinations
- [ ] Verify word count accuracy
- [ ] Test color picker functionality
- [ ] Test image positioning
- [ ] Test sidebar open/close
- [ ] Test save functionality
- [ ] Test format options
- [ ] Verify metadata in response
- [ ] Test with long content
- [ ] Test on mobile viewport
- [ ] Test accessibility (keyboard nav, screen readers)
