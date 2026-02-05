# Visual Layout & UI Guide

## Screen Layout Before vs After

### BEFORE: Full Width Chat
```
┌─────────────────────────────────────────────────────────────┐
│  Genesis | Tone: Informative | Length: Medium | Settings    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [User Message 1]                                           │
│                                                              │
│                                  [AI Response 1]            │
│                                    [Edit Button]            │
│                                                              │
│  [User Message 2]                                           │
│                                                              │
│  [Inline Editor - Takes Full Width]                         │
│  [CKEditor Instance]                                        │
│  [Save] [Cancel] buttons                                    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  [Input Textarea]  [Send →]                                 │
└─────────────────────────────────────────────────────────────┘
```

### AFTER: Split Panel Layout
```
┌──────────────────────────────────┬───────────────────────────┐
│  Genesis | Tone | Length | [⊟]   │  Edit Content             │
│  Panel Icon to toggle            │  ────────────────────     │
├──────────────────────────────────┼───────────────────────────┤
│                                  │ [Color Pickers]           │
│  [User Message 1]                │ Text: ⚫ ⬜ 🔵 🔴 🟢 🟣 │
│                                  │ Bg: ⚪ ⬜ 🔵 ☀️ 🟢 🟣   │
│  [AI Response 1]                 │                           │
│  [Edit Button] ◇                 │ Image Position:           │
│                                  │ [Inline ▼]                │
│  [User Message 2]                │                           │
│                                  │ ┌─────────────────────┐  │
│                                  │ │ CKEditor Toolbar    │  │
│  Chat scrolls here...            │ │ undo | redo | ...   │  │
│                                  │ ├─────────────────────┤  │
│                                  │ │                     │  │
│                                  │ │ Edited Content      │  │
│                                  │ │ Preview Here        │  │
│                                  │ │                     │  │
│                                  │ │                     │  │
│                                  │ ├─────────────────────┤  │
│                                  │ │ [Reset] [Save] [X]  │  │
│                                  │ └─────────────────────┘  │
├──────────────────────────────────┼───────────────────────────┤
│  [Input Textarea]  [Send →]      │                           │
└──────────────────────────────────┴───────────────────────────┘
```

## Component Breakdown

### Header Section
```
┌─────────────────────────────────────────────────────────────┐
│  [Genesis Logo] Genesis                  [Tone] [Length] [⊟] │
│                Advanced AI Content                           │
└─────────────────────────────────────────────────────────────┘
```

### Main Chat Area (Left Panel - 2/3 width when editing)
```
┌──────────────────────────────────┐
│ Message 1                         │
│ [Avatar] User text               │
│                                  │
│ [Bot Avatar] AI Response          │
│                [Edit ◇] [Time]    │
│                                  │
│ Message 2                         │
│ [Avatar] User text               │
│                                  │
│ [Bot Avatar] AI Response          │
│                    [Edit ◇]       │
└──────────────────────────────────┘
```

### Sidebar Editor (Right Panel - 1/3 width when open)
```
┌────────────────────────────────┐
│ Edit Content            [X]     │
├────────────────────────────────┤
│ Image Position                  │
│ [Inline ▼]                      │
│                                │
│ Text Color                      │
│ ⚫ ⬜ 🔵 🔴 🟢 🟣               │
│                                │
│ Background Color                │
│ ⚪ ⬜ 🔵 ☀️ 🟢 🟣              │
├────────────────────────────────┤
│ [CKEditor Toolbar]              │
│ undo|redo|heading|bold|italic   │
│ ────────────────────────────────│
│                                │
│ Your formatted content here      │
│ with **bold** and *italic*       │
│ and other formatting            │
│                                │
│                                │
│                                │
├────────────────────────────────┤
│ [Reset]        [Save Changes]  │
└────────────────────────────────┘
```

## Color Picker Interface

### Text Color Selector
```
Text Color
┌─────────────────────────┐
│ ⚫ ⬜ 🔵 🔴 🟢 🟣      │  6 Colors
│ black slate blue red green purple
│           ↑
│    Currently selected
└─────────────────────────┘
```

### Background Color Selector
```
Background Color
┌─────────────────────────┐
│ ⚪ ⬜ 🔵 ☀️ 🟢 🟣     │  6 Colors
│ white slate blue yellow green purple
│       ↑
│ Currently selected
└─────────────────────────┘
```

## Image Positioning Options
```
Image Position
┌──────────────┐
│ Inline   ▼   │
├──────────────┤
│ Inline      │
│ Left Align  │
│ Center      │
│ Right Align │
│ Full Width  │
└──────────────┘
```

## CKEditor Toolbar
```
┌──────────────────────────────────────────────────────────┐
│ ↶ ↷ | H₁ | B I 🎨 | ⬅ ⬆ ➡ | 🔗 🖼️ □ ❮ ❯ ❋ ❀ ❋ ↦ ↤ │
└──────────────────────────────────────────────────────────┘
  U  R   H  Bold Italic Highlight  Align   Link Image Table List Quote Indent
  n  e   e                                                                   
  d  d   a
     o
```

## Message Display States

### AI Message in Chat (Hover State)
```
┌─────────────────────────────────────┐
│ [Bot Avatar] AI Response text       │
│                                    │
│ ✓ AI Generated | 2:30 PM | [Edit ◇] │
└─────────────────────────────────────┘
         Hover shows these details
```

### Edit Flow Visual
```
Step 1: Initial Message
┌─────────────────┐
│ AI Response     │
│         [Edit]  │
└─────────────────┘
        ↓ Click

Step 2: Sidebar Opens
┌─────────────────┬────────────────┐
│ Main Chat       │ Editor Panel   │
│ (2/3 width)     │ (1/3 width)    │
│                 │ [CKEditor] ✏️  │
└─────────────────┴────────────────┘
        ↓ User edits & saves

Step 3: Content Updated
┌─────────────────┐
│ Updated Content │
│ (reflected)     │
└─────────────────┘
```

## Responsive Behavior

### Desktop (>1024px)
```
Full sidebar visible when editing
┌─────────┬──────────┐
│ 2/3     │ 1/3      │
│ Main    │ Editor   │
└─────────┴──────────┘
```

### Tablet (768px-1024px)
```
Sidebar still 1/3 but may need scrolling
┌──────────┬────────┐
│ Main     │ Editor │
│ (66%)    │ (34%)  │
└──────────┴────────┘
```

### Mobile (<768px)
```
Sidebar becomes overlay or full-width
Option 1: Sidebar overlays main
Option 2: Bottom sheet
Option 3: Tab-based switching
```

## Interactive Elements

### Buttons
```
Primary (Active/Hover):
[Save Changes] → bright blue gradient

Secondary:
[Reset] → subtle gray

Close:
[X] → small in corner
```

### Dropdowns
```
Image Position
[Inline ▼] ← Shows dropdown on click

Styling:
- Dark theme matches app
- Blue accent on hover
- Smooth transitions
```

### Color Picker
```
Colors appear as clickable boxes
⚫ ⬜ 🔵 🔴 🟢 🟣

Selected box shows border glow
Currently selected has visible border
Hover shows slight animation
```

## Metadata Display

### After Generation
```
Analysis Depth: Comprehensive ▓▓▓▓▓ 
Tone: Analytical
Word Count: 847 words | Sections: 5
```

### In Response
```
✅ Success
⏱️  Generated in 2.3s
📊 Quality: SEO 0.82 | Unique 0.91 | Engage 0.88
💰 Cost: $0.0045
```

## Animation Timeline

### Sidebar Open
```
0ms:    Panel off-screen (right: -100%)
200ms:  Panel slides in (right: 0)
        Blur effect on main chat (slight)
```

### Color Selection
```
0ms:    User clicks color
100ms:  Color box gets selection glow
200ms:  Content color updates in editor
```

### Save Button
```
0ms:    User clicks Save
100ms:  Button shows "Saving..."
200ms:  Content syncs
300ms:  Button shows "Save Changes" again
400ms:  Optional: Show success toast
```

## Accessibility Features

### Keyboard Navigation
```
Tab → Navigate buttons
Enter → Activate button
Esc → Close sidebar
↑/↓ → Scroll content
```

### Screen Reader
```
"Edit Content panel with CKEditor"
"Text color picker, 6 options"
"Background color picker, 6 options"
"Image positioning dropdown"
"Save Changes button, currently inactive"
```

### Color Contrast
```
Dark theme with light text
WCAG AAA compliant
Color picker boxes have names
Labels for all inputs
```
