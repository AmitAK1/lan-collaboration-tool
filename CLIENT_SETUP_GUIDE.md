# LAN Collaboration Tool - First Time Setup Guide

## 📋 Prerequisites
- Python 3.8 or higher
- Windows/Linux/MacOS
- Connected to the same LAN network

---

## 🚀 Quick Setup for Clients

### Step 1: Install Python
1. Download Python from: https://www.python.org/downloads/
2. During installation, **CHECK** "Add Python to PATH"
3. Verify installation:
   ```bash
   python --version
   ```

### Step 2: Download the Project
1. Download the project files
2. Extract to a folder (e.g., `lan-collaboration-tool`)

### Step 3: Install Required Libraries

#### For Windows (PowerShell/CMD):
```powershell
cd path\to\lan-collaboration-tool
pip install -r Requirements.txt
```

#### For Linux/MacOS (Terminal):
```bash
cd path/to/lan-collaboration-tool
pip3 install -r Requirements.txt
```

#### Manual Installation (if Requirements.txt fails):
```bash
pip install numpy>=1.24.0
pip install pyaudio>=0.2.13
pip install Pillow>=10.0.0
pip install mss>=9.0.0
pip install opencv-python>=4.8.0
```

---

## 🎮 Running the Application

### For Server (Host Machine):

#### Windows:
```powershell
# Method 1: Use batch file
start_server.bat

# Method 2: Manual command
python server.py
```

#### Linux/MacOS:
```bash
python3 server.py
```

**Note:** Keep the server terminal window open!

---

### For Clients (All Connected Machines):

#### Windows:
```powershell
# Method 1: Use batch file
start_client.bat

# Method 2: Manual command
python client.py
```

#### Linux/MacOS:
```bash
python3 client.py
```

**When prompted:**
1. Enter the **Server IP Address** (ask the host for their IP)
2. Enter your **Nickname**
3. Click OK

---

## 🔍 Finding the Server IP Address

### On Windows (Server Machine):
```powershell
ipconfig
```
Look for "IPv4 Address" under your active network adapter (usually starts with 192.168.x.x or 172.x.x.x)

### On Linux/MacOS (Server Machine):
```bash
ifconfig
# or
ip addr show
```

---

## 📦 One-Line Installation Commands

### Windows (PowerShell):
```powershell
# Install all dependencies
pip install numpy pyaudio Pillow mss opencv-python

# Run client
python client.py
```

### Linux/MacOS:
```bash
# Install all dependencies
pip3 install numpy pyaudio Pillow mss opencv-python

# Run client
python3 client.py
```

---

## 🐛 Troubleshooting

### PyAudio Installation Issues

#### Windows:
If `pip install pyaudio` fails:
1. Download precompiled wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Install with: `pip install PyAudio‑0.2.13‑cp312‑cp312‑win_amd64.whl`

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip3 install pyaudio
```

#### MacOS:
```bash
brew install portaudio
pip3 install pyaudio
```

### OpenCV Installation Issues
If `opencv-python` fails, try:
```bash
pip install opencv-python-headless
```

### Permission Errors
#### Windows:
```powershell
pip install --user -r Requirements.txt
```

#### Linux/MacOS:
```bash
sudo pip3 install -r Requirements.txt
# or
pip3 install --user -r Requirements.txt
```

---

## ✅ Verify Installation

Run this command to check if all libraries are installed:

### Windows:
```powershell
python -c "import numpy, pyaudio, PIL, mss, cv2; print('All libraries installed successfully!')"
```

### Linux/MacOS:
```bash
python3 -c "import numpy, pyaudio, PIL, mss, cv2; print('All libraries installed successfully!')"
```

---

## 🌐 Network Configuration

### Firewall Settings:
Make sure these ports are open:
- **TCP Port 6543** - Chat and File Transfer
- **UDP Port 6544** - Audio and Video Streaming

### Windows Firewall:
```powershell
# Allow Python through firewall (run as Administrator)
netsh advfirewall firewall add rule name="LAN Collaboration Tool" dir=in action=allow program="C:\Path\To\Python\python.exe" enable=yes
```

---

## 📝 Quick Reference Card for Clients

**1. Install Python:** https://python.org/downloads/

**2. Install Libraries:**
```bash
pip install numpy pyaudio Pillow mss opencv-python
```

**3. Run Client:**
```bash
python client.py
```

**4. Connect:**
- Enter Server IP (e.g., `192.168.1.100`)
- Enter Nickname
- Start collaborating!

---

## 💡 Optional: Opus Audio Codec (Better Quality)

For improved audio compression (optional):

### Windows:
1. Download Opus DLL: https://opus-codec.org/downloads/
2. Place `opus.dll` in `C:\Windows\System32\`
3. Install: `pip install opuslib`

### Linux:
```bash
sudo apt-get install libopus0 libopus-dev
pip3 install opuslib
```

### MacOS:
```bash
brew install opus
pip3 install opuslib
```

---

## 🎯 First-Time User Checklist

- [ ] Python installed and added to PATH
- [ ] All libraries installed (`pip install -r Requirements.txt`)
- [ ] Verified installation with test command
- [ ] Know the server IP address
- [ ] Firewall allows Python connections
- [ ] Connected to same LAN network as server

---

## 📞 Support

If you encounter any issues:
1. Check the main README.md for detailed troubleshooting
2. Ensure all machines are on the same network
3. Verify Python version is 3.8+
4. Check firewall settings

---

**Ready to collaborate? Start the server first, then connect clients!** 🚀
