# 🌐 LAN Collaboration Tool

A feature-rich, real-time collaboration application for Local Area Networks, built with Python. Share your screen, transfer files, communicate via audio/video, and chat with multiple users on your network.

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Table of Contents
- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Architecture](#-architecture)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

## ✨ Features

### 💬 **Real-Time Chat**
- Instant messaging with all connected users
- System notifications for user join/leave events
- Message history during session

### 📁 **File Transfer**
- Upload and download files to/from the server
- Professional file browser with columns (Filename, Size, Sender)
- Progress bar for upload/download operations
- Automatic file size formatting (B, KB, MB)
- Support for all file types

### 🖥️ **Screen Sharing**
- Present your screen to all connected users
- JPEG compression for efficient network usage
- Real-time screen capture using mss library
- Presentation view window for viewers
- Single presenter mode (prevents conflicts)

### 🎥 **Video Conferencing**
- Multi-user video chat with webcam support
- Video grid layout showing all participants
- Low bandwidth usage with optimized compression (320x240 @ 50% quality)
- 15 FPS for smooth performance on LAN
- User identification labels on each video feed

### 🎤 **Voice Communication**
- Real-time audio streaming
- Automatic audio mixing on server
- Mute/unmute functionality
- Optional Opus codec support for better quality and lower bandwidth
- Graceful fallback to raw audio if Opus is unavailable

### 🔧 **Advanced Features**
- **Unique Username Validation**: Prevents duplicate nicknames (up to 5 retry attempts)
- **User Reporting System**: Report inappropriate behavior with server logging
- **Robust Error Handling**: Webcam failures, network issues handled gracefully
- **Thread-Safe GUI**: All UI updates use proper threading mechanisms
- **Graceful Shutdown**: Clean resource cleanup on exit

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.12 or higher
- **RAM**: 4 GB
- **Network**: LAN connection (100 Mbps recommended)
- **Webcam**: Optional (for video conferencing)
- **Microphone**: Optional (for voice chat)

### Recommended Requirements
- **OS**: Windows 11
- **Python**: 3.12+
- **RAM**: 8 GB or more
- **Network**: Gigabit LAN (1000 Mbps)
- **Webcam**: 720p or higher
- **Microphone**: USB or built-in with noise cancellation

## 📥 Installation

### Step 1: Clone or Download
```bash
# Clone the repository
git clone https://github.com/yourusername/lan-collaboration-tool.git
cd lan-collaboration-tool

# Or download and extract the ZIP file
```

### Step 2: Install Dependencies
```bash
# Install required packages
pip install -r Requirements.txt
```

**Note**: If `opuslib` installation fails (due to missing Opus native library), the application will still work with raw audio. To enable Opus:
- **Windows**: Download Opus DLL from [opus-codec.org](https://opus-codec.org/downloads/)
- **Linux**: `sudo apt-get install libopus-dev`
- **macOS**: `brew install opus`

### Step 3: Configure Network
Edit `server.py` and `client.py` to match your network:

```python
# In server.py (line 23)
HOST = '192.168.1.100'  # Replace with your server's IP address

# In client.py (line 33)
initialvalue="192.168.1.100"  # Replace with your server's IP address
```

To find your IP address:
- **Windows**: `ipconfig` → Look for "IPv4 Address"
- **Linux/Mac**: `ifconfig` or `ip addr`

## 🚀 Quick Start

### Starting the Server
```bash
# Run the server on the host machine
python server.py
```

You should see:
```
[INFO] Opus codec not available - using raw audio
[INFO] Files will be stored in: D:\...\server_files
[AV] UDP Audio/Video server listening on 192.168.1.100:6544
[LISTENING] TCP Server is listening on 192.168.1.100:6543
[INFO] Press Ctrl+C to stop the server
```

### Connecting Clients
```bash
# Run on each client machine
python client.py
```

1. Enter the **Server IP** (e.g., `192.168.1.100`)
2. Choose a **unique nickname**
3. Start collaborating!

## 📖 Usage Guide

### Chat Interface
- Type your message in the bottom text box
- Press **Enter** or click **Send** to broadcast
- Messages appear in the chat area with sender's name

### File Transfer

#### Uploading Files
1. Click **Send File** button
2. Select file from your computer
3. Wait for upload progress to complete
4. File appears in the file list for all users

#### Downloading Files
1. Select a file from the file list (Filename | Size | Sender)
2. Click **Download Selected**
3. Choose save location
4. Wait for download to complete

### Screen Sharing
1. Click **Start Presenting** (green button)
2. Your screen is now visible to all users
3. Click **Stop Presenting** (red button) to end
4. **Note**: Only one user can present at a time

### Video Conferencing
1. Click **Start Video** (blue button)
2. A video conference window opens showing all participants
3. Your webcam feed appears along with others
4. Click **Stop Video** (red button) to turn off camera

#### Reporting Users
- Click the red **Report** button under any user's video feed
- Confirm the report in the dialog
- Server logs the report with timestamp

### Audio Communication
- Audio automatically connects when you join
- Click **Mute** (yellow button) to mute your microphone
- Click **Unmute** to resume speaking
- Server mixes all audio streams automatically

## 🏗️ Architecture

### Network Design
```
┌─────────────┐
│   Server    │ ← TCP Port 6543 (Chat, Files, Commands)
│ 192.168.1.100│ ← UDP Port 6544 (Audio/Video)
└──────┬──────┘
       │
   ┌───┴───┬───────┬────────┐
   │       │       │        │
┌──▼───┐ ┌─▼───┐ ┌─▼────┐ ┌─▼────┐
│Client│ │Client│ │Client│ │Client│
│  #1  │ │  #2  │ │  #3  │ │  #4  │
└──────┘ └─────┘ └──────┘ └──────┘
```

### Protocols
- **TCP (Port 6543)**: Reliable data transfer
  - Chat messages
  - File transfers
  - Screen sharing data
  - Control commands (PRESENTER_REQUEST, FILE_UPLOAD, etc.)
  
- **UDP (Port 6544)**: Real-time streaming
  - Audio packets (with optional Opus compression)
  - Video frames (JPEG compressed)
  - Low latency, tolerates packet loss

### Threading Model
**Server Threads:**
- Main TCP listener (accepts connections)
- Client handler threads (one per connected client)
- UDP audio/video receiver thread
- Audio mixing/broadcast thread

**Client Threads:**
- Main GUI thread (Tkinter)
- TCP receive handler thread
- Audio send thread
- Audio receive thread
- Video send thread (when camera is on)
- File upload threads (on demand)
- Screen capture thread (when presenting)

## 🔧 Troubleshooting

### Server Won't Start
**Error**: `Address already in use`
- **Solution**: Another program is using port 6543 or 6544
  ```bash
  # Windows
  netstat -ano | findstr :6543
  taskkill /PID <process_id> /F
  
  # Linux/Mac
  lsof -i :6543
  kill -9 <process_id>
  ```

### Client Can't Connect
**Error**: `Connection refused`
- Verify server is running
- Check firewall settings (allow ports 6543 and 6544)
- Ensure server IP is correct
- Ping the server: `ping 192.168.1.100`

### Webcam Error
**Error**: `Failed to open webcam` or `Error: -1072875772`
- Close other applications using the webcam (Zoom, Teams, etc.)
- Check camera permissions in Windows Settings
- Try a different camera (if available)
- Application continues working without video

### Opus Codec Not Available
**Warning**: `[INFO] Opus codec not available - using raw audio`
- This is **not an error** - audio will work with raw PCM format
- For better quality, install native Opus library (optional)
- Performance impact is minimal on LAN

### Audio Not Working
- Check microphone/speaker permissions
- Verify no other app is using the audio device
- Try muting/unmuting
- Restart the client application

## 📂 Project Structure

```
lan-collaboration-tool/
│
├── server.py              # Main server application
├── client.py              # Client GUI application
├── Requirements.txt       # Python dependencies
├── README.md             # This file
│
└── server_files/         # Storage for uploaded files (auto-created)
    ├── photo.jpg
    ├── document.pdf
    └── ...
```

## 🎯 Key Components

### server.py
- **Lines 1-50**: Configuration and imports
- **Lines 51-110**: Client management (broadcast, remove_client)
- **Lines 111-280**: TCP handler (chat, files, screen sharing)
- **Lines 281-390**: UDP handler (audio/video decode and relay)
- **Lines 391-460**: Audio mixing and broadcast
- **Lines 461-512**: Server initialization and shutdown

### client.py
- **Lines 1-70**: Imports and configuration
- **Lines 71-130**: Connection and nickname validation
- **Lines 131-210**: GUI construction (Treeview, buttons)
- **Lines 211-340**: File transfer (upload/download)
- **Lines 341-440**: Screen sharing (capture and view)
- **Lines 441-590**: Audio system (Opus encoding/decoding)
- **Lines 591-790**: Video conferencing (webcam capture)
- **Lines 791-1020**: Message handler (TCP receive thread)

## 🤝 Contributing

Contributions are welcome! Here are some ideas:
- [ ] Add encryption for file transfers
- [ ] Implement persistent chat history
- [ ] Add emoji/reaction support
- [ ] Create admin/moderator roles
- [ ] Add whiteboard/drawing feature
- [ ] Implement bandwidth usage monitor
- [ ] Add user profile pictures
- [ ] Create mobile app version

## 📄 License

This project is licensed under the MIT License - free to use, modify, and distribute.

## 🙏 Acknowledgments

- **Python** - Core programming language
- **Tkinter** - GUI framework
- **PyAudio** - Audio I/O
- **OpenCV** - Video processing
- **MSS** - Fast screen capture
- **Opus Codec** - Audio compression
- **NumPy** - Audio mixing operations

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Email: amit.ak0599@gmail.com
- Documentation: [Wiki](https://github.com/AmitAK1/lan-collaboration-tool/)

---

**Made with ❤️ for Computer Networks Project - Semester 5**

**Version**: 1.0.0  
**Last Updated**: October 19, 2025
