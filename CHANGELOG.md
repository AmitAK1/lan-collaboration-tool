# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-21

### Added
- **Real-time chat** with message broadcasting
- **File transfer system** with upload/download capabilities
- **Screen sharing** with JPEG compression
- **Video conferencing** with multi-user support
- **Voice communication** with audio mixing on server
- **Opus codec support** with graceful fallback to raw audio
- **User reporting system** for moderation
- **Professional file browser** with Treeview (Filename, Size, Sender columns)
- **Unique username validation** with retry mechanism
- **Webcam error handling** with consecutive failure detection
- **Thread-safe GUI updates** using window.after()
- **Graceful server shutdown** with Ctrl+C handling
- **Progress bars** for file transfers
- **Mute/unmute functionality** for audio
- **Video feed controls** with report buttons

### Features
- TCP/IP for reliable data transfer (chat, files, commands)
- UDP for real-time audio/video streaming
- Automatic audio mixing from multiple sources
- Network binding to specific IP addresses
- Daemon threads for background operations
- Socket locking for concurrent file operations
- Custom protocol commands (CMD:PRESENTER_REQUEST, CMD:FILE_UPLOAD, etc.)

### Technical Highlights
- Python 3.12+ compatible
- Cross-platform support (Windows, Linux, macOS)
- Efficient JPEG compression for video (320x240 @ 50% quality)
- Audio streaming at 44.1kHz, 16-bit, mono
- Screen capture using MSS library for high performance
- OpenCV for video processing
- NumPy for audio mixing operations
- PyAudio for audio I/O

### Documentation
- Comprehensive README with usage guide
- Requirements.txt with all dependencies
- Architecture documentation
- Troubleshooting section
- Contributing guidelines
- MIT License

## [Unreleased]

### Planned Features
- [ ] End-to-end encryption for file transfers
- [ ] Persistent chat history
- [ ] Emoji and reaction support
- [ ] Admin/moderator roles
- [ ] Whiteboard/drawing feature
- [ ] Bandwidth usage monitor
- [ ] User profile pictures
- [ ] Mobile app version
- [ ] Group chat rooms
- [ ] Private messaging
- [ ] File preview before download
- [ ] Dark/light theme toggle

---

## Version History

### Version Numbering
- **Major.Minor.Patch** (e.g., 1.0.0)
- **Major**: Breaking changes or major feature additions
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, minor improvements

### Release Notes Format
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

---

**Note**: This is the initial release version (1.0.0) developed as a Computer Networks course project for Semester 5.
