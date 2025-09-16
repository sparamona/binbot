# BinBot UI Wireframe Design

## Layout Overview
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        🤖 BinBot Inventory System                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  🎤 Hold to Talk    � Voice Output: ON    🎛️ Provider: OpenAI    ⚙️ Settings  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │        Actions & Chat           │  │      📦 Current Bin View            │  │
│  │                                 │  │                                     │  │
│  │      Quick Actions              │  │        📍 Bin 5 Contents            │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ │  │  ┌─────────────────────────────┐   │  │
│  │  │ ➕  │ │ 🔍  │ │ ↔️  │ │ ➖  │ │  │  │ • screws (just added) 📷    │   │  │
│  │  │Add  │ │Search│ │Move │ │Remove│ │  │  │ • washers                   │   │  │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ │  │  │ • springs                   │   │  │
│  │                                 │  │  │ • bolts 📷                  │   │  │
│  │         � Image Upload         │  │  │ • nuts                      │   │  │
│  │    [Drop image or click here]   │  │  │                             │   │  │
│  │                                 │  │  │ Total: 5 items (2 w/images) │   │  │
│  │                                 │  │  │ • bolts                     │   │  │
│  │         Chat Interface          │  │  │ • nuts                      │   │  │
│  │  ┌─────────────────────────────┐ │  │  │                             │   │  │
│  │  │ User: add screws to bin 5   │ │  │  │ Total: 5 items              │   │  │
│  │  │ Bot: ✅ Added screws to bin 5│ │  │  │ Last updated: 2 min ago     │   │  │
│  │  │                             │ │  │  │                             │   │  │
│  │  │ User: what's in this image? │ │  │  │ [🔄 Refresh] [📋 Full List] │   │  │
│  │  │ Bot: � I see a mouse, pen, │ │  │  │ [📷 Add Image] [🖼️ Gallery] │   │  │
│  │  │ and coaster. Added to bin 4 │ │  │  └─────────────────────────────┘   │  │
│  │  │                             │ │  │                                     │  │
│  │  │ User: move bolts to bin 7   │ │  │        Current Context              │  │
│  │  │ Bot: ✅ Moved bolts: 3→7     │ │  │  � Session: Active (15 min)       │  │
│  │  │                             │ │  │  📝 Recent items: screws, bolts    │  │
│  │  │ [Scroll for more...]        │ │  │                                     │  │
│  │  └─────────────────────────────┘ │  │        Bin Quick Stats              │  │
│  │                                 │  │  📊 Total bins with items: 8        │  │
│  │  ┌─────────────────────────────┐ │  │  📈 Most active bin: 3              │  │
│  │  │  💬 Type your command...    │ │  │  🔄 Last operation: 2 min ago       │  │
│  │  │  [                        ] │ │  │                                     │  │
│  │  │  🎤 Hold to Talk  📤 Send   │ │  │                                     │  │
│  │  └─────────────────────────────┘ │  │                                     │  │
│  └─────────────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  📋 Recent Activity: • Added screws to bin 5 • Moved bolts: 3→7 • Removed pens │
│  💾 Database: ✅  🧠 AI: ✅  🔊 Voice: ✅     Session: 15 min     Items: 47    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  💡 Try: "add bolts to bin 3" • "what's in bin 5?" • "move screws to bin 2"   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Header Section
- **Title**: "🤖 BinBot Inventory System"
- **Style**: Large, prominent branding
- **Color**: Primary brand color

### 2. Voice Controls Bar
- **PTT Button**: "Hold to Talk" - Press and hold to activate voice input
- **Voice Output Toggle**: ON/OFF switch for voice responses with speaker icon
- **Provider Display**: Shows current voice provider (Browser/OpenAI)
- **Settings**: Gear icon for voice configuration

### 3. Main Content Area (Split Layout)

#### Left Panel (60% width) - Actions & Chat
- **Quick Actions Section**:
  - 6 action buttons in 2x3 grid layout (Add, Search, Smart Image Upload, Move, Remove, Images)
  - **Smart Image Upload**: Camera icon - upload image to automatically identify and add items
  - **Images**: Gallery icon - view and manage images associated with items
  - Prominent placement at top for easy access
  - Visual icons with clear labels

- **Chat Interface**:
  - Scrollable message history below actions
  - User messages: Right-aligned, blue background
  - Bot responses: Left-aligned, gray background
  - Timestamps on hover, auto-scroll to bottom

- **Input Area**:
  - Large text input with placeholder at bottom
  - PTT button for voice input (press and hold)
  - Send button (Enter key also works)
  - Voice and text input work together seamlessly

#### Right Panel (40% width) - Current Bin View
- **Current Bin Contents**: Primary focus showing live view of active bin
  - Shows up to 5 items with newest/changed items highlighted
  - **Image indicators**: 📷 icon next to items that have associated images
  - Refresh button to update contents
  - "Full List" button to see all items in modal
  - **Add Image** button to associate images with bin or items
  - **Gallery** button to view all images in current bin
  - Total item count and image count displayed
  - Auto-updates when operations affect the displayed bin

- **Current Context**: Shows session state and working bin
- **Bin Quick Stats**: Overview statistics (total bins, most active, etc.)

### 4. Bottom Status Area
- **Recent Activity Bar**: Horizontal scrolling list of last few operations
- **System Status Strip**: Compact status indicators for database, AI, voice
- **Session Info**: Active session time and total item count
- **All information condensed into 2 horizontal strips for space efficiency**

### 5. Current Bin Contents Panel (Right Panel)
- **Dynamic Updates**: Automatically shows contents of the most recently accessed bin
- **Context Awareness**: Updates when user adds/removes/moves items to/from the displayed bin
- **Visual Indicators**:
  - Recently added items show "(just added)" annotation
  - Recently modified items are highlighted
  - Items that were just moved show "(moved from bin X)" temporarily
- **Interactive Elements**:
  - Refresh button to manually update contents
  - Full List button opens modal with complete bin inventory
  - Click on item name to search for similar items
- **Smart Behavior**:
  - Persists across page refreshes (remembers last bin)
  - Shows "No bin accessed yet" message on first visit
  - Handles empty bins gracefully with "Bin X is empty" message

### 6. Footer
- **Help Text**: Example commands
- **Keyboard Shortcuts**: Hints for power users

## Modal Dialogs

### Quick Add Modal
```
┌─────────────────────────────────┐
│           Add New Item          │
├─────────────────────────────────┤
│  Item Name: [_______________]   │
│  Bin Number: [____]             │
│  Description: [_______________] │
│  📷 Add Image (Optional)        │
│                                 │
│     [Cancel]    [Add Item]      │
└─────────────────────────────────┘
```



### Search Results Modal
```
┌─────────────────────────────────────────────────────┐
│                  Search Results                     │
├─────────────────────────────────────────────────────┤
│  🔍 Found 3 items for "screws":                    │
│                                                     │
│  📦 Bin 3: screws (95% match) 📷                   │
│     [🖼️ View Images] [📷 Add Image]                │
│                                                     │
│  📦 Bin 7: wood screws (87% match)                 │
│     [📷 Add Image]                                  │
│                                                     │
│  📦 Bin 2: machine screws (82% match) 📷           │
│     [🖼️ View Images] [📷 Add Image]                │
│                                                     │
│           [Close Results]                           │
└─────────────────────────────────────────────────────┘
```

### Disambiguation Modal
```
┌─────────────────────────────────────────┐
│          Multiple Items Found           │
├─────────────────────────────────────────┤
│  Which item did you mean?               │
│                                         │
│  ○ screws in bin 3 (95% match)         │
│  ○ screws in bin 7 (87% match)         │
│  ○ wood screws in bin 2 (75% match)    │
│                                         │
│     [Cancel]    [Select Item]           │
└─────────────────────────────────────────┘
```

### Full Bin Contents Modal
```
┌─────────────────────────────────────────────────────┐
│                📦 Bin 5 - Complete Contents         │
├─────────────────────────────────────────────────────┤
│  🔍 Filter: [_______________] 🔄 Refresh            │
│                                                     │
│  📋 All Items (5 total, 2 with images):            │
│                                                     │
│  • screws (just added) 📷 - Added 2 min ago        │
│    [🖼️ View] [📷 Add] [✏️ Edit]                    │
│  • washers - Added 1 day ago                       │
│    [📷 Add Image] [✏️ Edit]                        │
│  • springs - Added 3 days ago                      │
│    [📷 Add Image] [✏️ Edit]                        │
│  • bolts 📷 - Added 1 week ago                     │
│    [🖼️ View] [📷 Add] [✏️ Edit]                    │
│  • nuts - Added 1 week ago                         │
│    [📷 Add Image] [✏️ Edit]                        │
│                                                     │
│  📊 Bin Statistics:                                 │
│  • Total Items: 5 • Items with Images: 2           │
│  • Last Activity: 2 minutes ago                    │
│  • Most Common: Hardware items                     │
│                                                     │
│  🔧 Quick Actions:                                  │
│  [➕ Add Item] [� Smart Upload] [🖼️ Gallery]      │
│  [�🔍 Search Similar] [↔️ Move All]                  │
│                                                     │
│                    [Close]                          │
└─────────────────────────────────────────────────────┘
```

### Image Gallery Modal
```
┌─────────────────────────────────────────────────────┐
│              🖼️ Image Gallery - Bin 5               │
├─────────────────────────────────────────────────────┤
│  📷 Images (3 total) | 🔍 Filter: [__________]     │
│                                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │ ┌─────┐ ┌─────┐ ┌─────┐                       │ │
│  │ │ 📷  │ │ 📷  │ │ 📷  │                       │ │
│  │ │Thumb│ │Thumb│ │Thumb│                       │ │
│  │ │ 1   │ │ 2   │ │ 3   │                       │ │
│  │ └─────┘ └─────┘ └─────┘                       │ │
│  │ screws  bolts   washers                        │ │
│  │ 2m ago  1w ago  3d ago                         │ │
│  └─────────────────────────────────────────────────┘ │
│                                                     │
│  Selected: screws image                             │
│  ┌─────────────────────────────────────────────────┐ │
│  │                                                 │ │
│  │           [Large Image Preview]                 │ │
│  │                                                 │ │
│  └─────────────────────────────────────────────────┘ │
│                                                     │
│  🔧 Actions:                                        │
│  [🔍 Analyze] [✏️ Edit Item] [🗑️ Delete]           │
│  [📤 Download] [🔗 Copy Link]                      │
│                                                     │
│     [📷 Add New Image]              [Close]        │
└─────────────────────────────────────────────────────┘
```

### Voice Settings Modal
```
┌─────────────────────────────────────────────────────┐
│                🎤 Voice Settings                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🎙️ Voice Input (PTT):                             │
│  ○ Enabled    ○ Disabled                           │
│  Shortcut: [Spacebar ▼]                            │
│  □ Audio feedback on start/stop                    │
│                                                     │
│  🔊 Voice Output:                                   │
│  ○ Enabled    ○ Disabled                           │
│  Volume: [████████░░] 80%                          │
│  Speed: [██████░░░░] 1.2x                          │
│                                                     │
│  🎛️ Voice Provider:                                │
│  ○ Browser (Free, Fast)                            │
│  ○ OpenAI (Premium Quality)                        │
│                                                     │
│  OpenAI Voice: [Alloy ▼]                           │
│  (Nova, Echo, Fable, Onyx, Shimmer)                │
│                                                     │
│  🧪 Test Voice:                                     │
│  [🎤 Test Input] [🔊 Test Output]                  │
│                                                     │
│     [Reset to Defaults]    [Save Settings]         │
└─────────────────────────────────────────────────────┘
```

## Responsive Design Notes

### Desktop (1200px+)
- Full split layout as shown above
- All panels visible simultaneously

### Tablet (768px - 1199px)
- Stack panels vertically
- Chat on top, info panel below
- Collapsible sections

### Mobile (< 768px)
- **Priority Layout**: Current bin contents prominently displayed at top
- **Sticky Bin View**: Current bin info always visible while scrolling
- **Collapsible Chat**: Chat history can be minimized to save space
- **Bottom Actions**: Quick action buttons in bottom navigation bar
- **Voice-First**: PTT button prominent and easily accessible
- **Swipe Navigation**: Swipe between bin view, chat, and actions

### Mobile Layout Wireframe
```
┌─────────────────────────────────┐
│    🤖 BinBot    🎤 🔊 ⚙️      │ ← Header with voice controls
├─────────────────────────────────┤
│      📦 Bin 5 Contents          │ ← PRIORITY: Always visible
│  ┌─────────────────────────┐   │
│  │ • screws (just added) 📷│   │
│  │ • washers               │   │
│  │ • springs               │   │
│  │ • bolts 📷              │   │
│  │ • nuts                  │   │
│  │ Total: 5 items (2 w/📷) │   │
│  │ [🔄] [📋] [📷] [🖼️]     │   │
│  └─────────────────────────┘   │
├─────────────────────────────────┤
│ 💬 Chat History [▼ Minimize]   │ ← Collapsible
│ ┌─────────────────────────────┐ │
│ │ User: add screws to bin 5   │ │
│ │ Bot: ✅ Added screws...     │ │
│ │ [Scroll for more...]        │ │
│ └─────────────────────────────┘ │
├─────────────────────────────────┤
│ [        Type here...         ] │ ← Input area
│ [🎤 Hold to Talk]  [📤 Send]   │
├─────────────────────────────────┤
│ [➕Add] [🔍Search] [📷Upload] [🖼️] │ ← Bottom action bar
└─────────────────────────────────┘
```

### Mobile-Specific Features

#### Current Bin Priority
- **Always Visible**: Bin contents stay at top, never hidden
- **Sticky Header**: Bin name and item count remain visible while scrolling
- **Quick Refresh**: Pull-to-refresh gesture updates bin contents
- **Visual Emphasis**: Larger text and icons for bin contents

#### Space-Efficient Design
- **Collapsible Sections**: Chat history can be minimized when not needed
- **Swipe Gestures**: Swipe left/right to switch between active bins
- **Bottom Sheet**: Full bin contents modal slides up from bottom
- **Compact Actions**: Action buttons optimized for thumb navigation

#### Touch-Optimized Interactions
- **Large PTT Button**: Easy to press and hold with thumb
- **Voice-First Flow**: Voice input prioritized over typing on small screens
- **Haptic Feedback**: Vibration confirms PTT activation and actions
- **One-Handed Use**: All primary functions accessible with thumb

## Color Scheme Suggestions

### Primary Colors
- **Brand Blue**: #2563eb (buttons, links)
- **Success Green**: #10b981 (success messages)
- **Warning Orange**: #f59e0b (warnings)
- **Error Red**: #ef4444 (errors)

### Background Colors
- **Main Background**: #f8fafc (light gray)
- **Panel Background**: #ffffff (white)
- **Chat User**: #dbeafe (light blue)
- **Chat Bot**: #f1f5f9 (light gray)

### Text Colors
- **Primary Text**: #1f2937 (dark gray)
- **Secondary Text**: #6b7280 (medium gray)
- **Muted Text**: #9ca3af (light gray)

## Image Handling Features

### Simplified Image Upload Workflow
1. **Upload Trigger**: User drags image to upload area or clicks to browse
2. **Auto-Analysis**: System automatically analyzes image using AI vision
3. **Chat Integration**: AI describes what it sees and adds image to conversation context
4. **Natural Commands**: User can then use voice/text to decide what to do with identified items
   - "add the mouse to bin 7"
   - "put everything in bin 4"
   - "just add the pen to bin 2"
5. **Context Retention**: AI remembers image contents for follow-up commands
6. **Automatic Association**: Images are linked to items when they're created

### Image Search Integration
- **Search Results**: Items with images show 📷 indicator in search results
- **Image Preview**: Click image indicator to view thumbnail in search results
- **Image Actions**: "View Images" and "Add Image" buttons for each search result
- **Visual Context**: Images help users identify correct items when multiple matches exist

### Post-Creation Image Association
- **Add to Existing Items**: "📷 Add Image" button available for any item
- **Multiple Images**: Items can have multiple associated images
- **Primary Image**: First or designated image serves as primary thumbnail
- **Image Management**: Edit, delete, or reorder images through gallery interface

### Image Display Patterns
- **List Views**: 📷 icon indicates items with images, count shows total images
- **Gallery View**: Grid of thumbnails with item names and timestamps
- **Detail View**: Large image preview with metadata and action buttons
- **Search Integration**: Images appear in search results and help with disambiguation

## Interactive Elements

### Voice Interaction Design

#### Push-to-Talk (PTT) Behavior
1. **Ready State**: Gray microphone button with "Hold to Talk" text
2. **Active State**: Red pulsing microphone while held down, "Listening..." text
3. **Processing State**: Blue spinning microphone, "Processing..." text
4. **Error State**: Red microphone with X, error message displayed

#### Voice Output Control
- **Toggle Button**: Speaker icon with ON/OFF state clearly visible in header
- **Visual Feedback**: When voice output is OFF, responses show 🔇 icon
- **User Preference**: Setting persists across sessions
- **Quick Access**: Toggle available in both header and settings

#### PTT Implementation Details
- **Desktop**: Mouse down/up on PTT button or spacebar hold
- **Mobile**: Touch and hold gesture on PTT button
- **Keyboard Shortcut**: Spacebar (when not focused in text input)
- **Visual Feedback**: Button changes color and shows recording animation
- **Audio Feedback**: Optional beep on start/stop (configurable in settings)

### Button States
- **Default**: Subtle shadow, hover lift
- **Hover**: Slight scale increase
- **Active**: Pressed appearance
- **Disabled**: Grayed out, no interaction

### Loading States
- **Chat**: Typing indicator with dots
- **Search**: Spinner in results area
- **Voice**: Waveform animation

## Accessibility Features

### Keyboard Navigation
- Tab through all interactive elements
- Enter to activate buttons
- Escape to close modals
- Arrow keys for selection lists

### Screen Reader Support
- Proper ARIA labels
- Live regions for dynamic content
- Semantic HTML structure
- Alt text for all icons

### Voice Accessibility
- Voice commands work without mouse
- Audio feedback for all actions
- Configurable speech rate/voice

## Technical Implementation Notes

### Framework Suggestions
- **CSS Framework**: Tailwind CSS for rapid styling
- **Icons**: Heroicons or Lucide for consistency
- **Animations**: CSS transitions + Framer Motion for complex animations
- **Responsive**: Mobile-first approach

### Performance Considerations
- Lazy load chat history
- Debounce search input
- Cache recent operations
- Optimize voice processing
- **Image Optimization**: Compress images, generate thumbnails, lazy load galleries
- **Smart Caching**: Cache image analysis results, thumbnail generation
- **Progressive Loading**: Load image previews before full resolution images

### Image Technical Requirements
- **File Support**: JPG, PNG, WEBP formats with size limits (max 10MB)
- **Thumbnail Generation**: Small (150px), Medium (300px), Large (800px) variants
- **AI Integration**: OpenAI Vision API for automatic item identification
- **Storage**: Local filesystem with organized directory structure
- **Metadata**: Track image dimensions, file size, creation date, associated items
- **Security**: Validate file types, sanitize filenames, prevent malicious uploads

Would you like me to modify any aspects of this wireframe or create additional detailed views for specific components?
