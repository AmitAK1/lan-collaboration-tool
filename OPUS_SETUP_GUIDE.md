# Opus Audio Codec Setup Guide for Windows

## ⚠️ Important: Opus is OPTIONAL!
Your LAN Collaboration Tool works perfectly fine **WITHOUT** Opus. It will automatically use raw audio instead. Only install Opus if you want slightly better audio compression (which doesn't really matter on LAN).

---

## 🎯 What You Need

The files you downloaded (`opusdec.exe`, `opusenc.exe`, `opusinfo.exe`) are **command-line tools**, not the library Python needs.

For Python's `opuslib` to work, you need:
1. **libopus DLL** (the actual library)
2. **opuslib Python package**

---

## 📥 How to Install Opus DLL for Python

### Method 1: Download Pre-built DLL (Easiest)

**Step 1: Download Opus DLL**

Go to one of these sources:
- https://github.com/xiph/opus/releases
- https://opus-codec.org/downloads/

Look for: **opus-1.3.x-win64.zip** or **opus-1.4-win64.zip**

**Step 2: Extract and Copy DLL**

1. Extract the ZIP file
2. Find `opus.dll` (or `libopus-0.dll`)
3. Copy it to one of these locations:

   **Option A: System folder (Recommended)**
   ```
   C:\Windows\System32\opus.dll
   ```

   **Option B: Python Scripts folder**
   ```
   C:\Users\Admin\AppData\Local\Programs\Python\Python312\Scripts\opus.dll
   ```

   **Option C: Project folder**
   ```
   D:\OneDrive\Desktop\Semester 5\Computer Networks\Project\lan-collaboration-tool\opus.dll
   ```

**Step 3: Install Python Package**
```powershell
pip install opuslib
```

**Step 4: Test**
```powershell
python -c "import opuslib; print('Opus installed successfully!')"
```

---

### Method 2: Using Conda (Alternative)

If you use Anaconda/Miniconda:

```bash
conda install -c conda-forge libopus
pip install opuslib
```

---

### Method 3: Build from Source (Advanced)

Only if you're comfortable with compiling C code:

1. Install Visual Studio Build Tools
2. Clone Opus repository
3. Build DLL
4. Follow Method 1, Step 2-4

---

## ✅ Verify Installation

Run your client or server:
```powershell
python client.py
```

**WITH Opus installed:**
```
[INFO] Opus codec available - using compressed audio
```

**WITHOUT Opus installed:**
```
[INFO] Opus codec not available - using raw audio
```

Both work perfectly fine! The application automatically detects and adapts.

---

## 🔍 Troubleshooting

### "Could not find Opus library"
- Make sure `opus.dll` is in one of the paths mentioned above
- Try renaming the file to exactly `opus.dll` (not `libopus-0.dll`)
- Restart your terminal/IDE after copying the DLL

### "DLL load failed"
- Make sure you downloaded the **64-bit** version if using 64-bit Python
- Check: `python -c "import platform; print(platform.architecture())"`

### Still not working?
Just use raw audio! It works great and there's no noticeable difference on LAN networks.

---

## 💡 Quick Decision Guide

**Should I install Opus?**

✅ **YES** if:
- You have limited bandwidth
- You want to learn about audio codecs
- You're connecting over internet (not just LAN)

❌ **NO** if:
- You're only using LAN (local network)
- You want quick setup
- You don't want to deal with DLL installation

**Current Status:** Your app works perfectly without it! 🎉

---

## 📊 Comparison: Opus vs Raw Audio

| Feature | Opus (Compressed) | Raw Audio |
|---------|------------------|-----------|
| Setup | Requires DLL installation | Works out of the box |
| Audio Quality | Excellent | Excellent (on LAN) |
| Bandwidth Usage | ~32 Kbps | ~1.4 Mbps |
| LAN Performance | Great | Great |
| Latency | Very low | Very low |
| **Recommended for LAN?** | Optional | ✅ Yes |

---

## 🎯 Recommendation

**For your Computer Networks project:**
- ✅ **Use raw audio** (what you have now)
- ✅ Works perfectly on LAN
- ✅ No setup headaches
- ✅ Easy for teammates to install

Only add Opus if your instructor specifically requires it or if you want to demonstrate codec optimization.

---

## 📝 Summary

**Files you have:** `opusdec.exe`, `opusenc.exe` = Command-line tools (not needed)

**What you need:** `opus.dll` = Library file for Python

**Where to get it:** https://github.com/xiph/opus/releases

**Do you NEED it?** No! Your app works great without it.

---

**Current Status: Your application is working correctly! 🎉**
