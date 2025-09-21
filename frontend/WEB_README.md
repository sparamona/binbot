# BinBot Web Frontend

A modern, responsive web interface for the BinBot AI inventory management system.

## Features

### 🎨 **Modern UI Design**
- Clean, split-panel layout (chat left, bin contents right)
- Responsive design that works on desktop and mobile
- Smooth animations and transitions
- Professional gradient styling with Inter font

### 💬 **Chat Interface**
- Natural language conversation with BinBot
- Real-time typing indicators
- Message history with user/bot distinction
- Auto-scroll to latest messages
- Enter key to send messages

### 📷 **Image Upload**
- Click camera button to upload images
- Automatic image analysis using Gemini Vision
- Display detected items in chat
- Support for JPEG, PNG, and other image formats
- 10MB file size limit with validation

### 📦 **Bin Contents Display**
- Real-time bin contents on the right panel
- Shows current bin based on conversation context
- Item details with names, descriptions, and IDs
- Associated images displayed as thumbnails
- Item count and last updated timestamp
- Manual refresh button

### 🔧 **Session Management**
- Automatic session creation on page load
- Secure HTTP-only cookie-based sessions
- Session cleanup on page unload
- Connection status indicator
- 30-minute session timeout

### ⚡ **User Experience**
- Loading states and error handling
- Toast notifications for errors
- Keyboard shortcuts (Enter to send)
- Auto-focus on input after sending
- Graceful degradation when offline

## Files

- **`index.html`** - Main HTML structure with semantic layout
- **`style.css`** - Complete CSS styling with responsive design
- **`app.js`** - JavaScript application with full functionality

## Usage

1. **Start the BinBot server** (see main README)
2. **Open `index.html`** in a web browser
3. **Start chatting** with natural language commands:
   - "add hammer to bin 3"
   - "what's in bin 5"
   - "find my electronics"
   - "move screws from bin 2 to bin 4"
4. **Upload images** by clicking the camera button
5. **View bin contents** in the right panel

## API Integration

The frontend integrates with these BinBot API endpoints:

- **`POST /api/session`** - Create new session
- **`GET /api/session/{id}`** - Get session state
- **`POST /api/chat/command`** - Send text messages
- **`POST /api/chat/image`** - Upload and analyze images
- **`GET /images/{id}`** - Serve image files

## Browser Support

- Modern browsers with ES6+ support
- Chrome, Firefox, Safari, Edge
- Mobile browsers (iOS Safari, Chrome Mobile)
- Responsive design for tablets and phones

## Development

The frontend is a vanilla JavaScript single-page application with no build process required. Simply serve the files from a web server or open `index.html` directly.

For development with the BinBot API server:
1. Start the FastAPI server on `http://localhost:8000`
2. Open the frontend in a browser
3. The app will automatically connect to the API server

## Architecture

```
Frontend (Browser)
├── Session Management (cookies, state)
├── Chat Interface (messages, typing)
├── Image Upload (file handling, preview)
├── Bin Display (contents, refresh)
└── API Client (fetch, error handling)
```

The frontend follows a clean separation of concerns with:
- **HTML** for semantic structure
- **CSS** for visual design and responsive layout  
- **JavaScript** for application logic and API integration
