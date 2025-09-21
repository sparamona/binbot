# BinBot CLI Frontend

A text-based command-line interface for the BinBot inventory management system.

## Features

- **Text Commands**: Send natural language commands to BinBot
- **Image Upload**: Upload and analyze images with the `upload` command
- **Session Management**: Automatically creates and manages API sessions
- **Interactive Interface**: Simple command-line interface with help system

## Usage

### Starting the CLI

1. **Start the BinBot API server:**
   ```bash
   python app.py
   ```

2. **Run the CLI:**
   ```bash
   python frontend/cli.py
   # or
   python run_cli.py
   ```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show available commands | `/help` |
| `/upload <path>` | Upload an image file | `/upload photo.jpg` |
| `/quit`, `/exit`, `/q` | Exit the application | `/quit` |
| `<any text>` | Send command to BinBot | `add screwdriver to bin A` |

### Example Session

```
🤖 BinBot CLI Frontend
==============================
✅ Session started: a1b2c3d4...
Type '/help' for commands or '/quit' to exit

🔧 > /help

📋 BinBot CLI Commands:
  /help                     - Show this help message
  /upload <path>            - Upload an image file
  /quit, /exit, /q          - Exit the application
  <any text>                - Send command to BinBot

💡 Examples:
  add screwdriver to bin A
  what's in bin B?
  /upload photo.jpg
  search for red items

🔧 > what bins do I have?
🤖 You currently have no bins set up. Would you like me to help you create some bins?

🔧 > create bin A for tools
🤖 I've created bin A for storing tools. You can now add items to this bin.

🔧 > /upload test/coaster_pen_mouse.jpg
📸 Image uploaded successfully
🤖 I've analyzed the image and found 3 items: wooden coaster, red pen, and Logitech mouse.

🔧 > what's in bin A?
🤖 Bin A (tools) contains:
- Wooden Coaster: Round coaster made of wood with spiral design
- Red Pen: A red ballpoint pen with white tip and clip  
- Logitech MX Master Mouse: Gray ergonomic computer mouse with multiple buttons

🔧 > /quit
✅ Session ended
👋 Goodbye!
```

## Configuration

### API Server URL

By default, the CLI connects to `http://localhost:8000`. You can change this by:

1. **Environment variable:**
   ```bash
   export BINBOT_API_URL=http://your-server:8000
   python frontend/cli.py
   ```

2. **Command line argument:**
   ```bash
   python frontend/cli.py http://your-server:8000
   ```

## Error Handling

The CLI handles common errors gracefully:

- **Connection errors**: Shows clear error messages if the API server is not running
- **File not found**: Validates image file paths before upload
- **API errors**: Displays server error messages
- **Keyboard interrupts**: Clean exit with Ctrl+C
- **Session cleanup**: Automatically ends sessions on exit

## Requirements

- Python 3.7+
- `requests` library (included in requirements.txt)
- Running BinBot API server

## Implementation Details

- **Session Management**: Creates a new session on startup and cleans up on exit
- **HTTP Requests**: Uses the `requests` library to communicate with the API
- **File Uploads**: Handles multipart form data for image uploads
- **Cookie Handling**: Manages session cookies for API authentication
- **Error Recovery**: Graceful handling of network and API errors
