# 🚀 GitHub Upload Guide

Complete step-by-step instructions to upload your LAN Collaboration Tool to GitHub.

## 📋 Prerequisites

1. **Git Installed**
   - Download from: https://git-scm.com/downloads
   - Verify: `git --version`

2. **GitHub Account**
   - Sign up at: https://github.com/signup
   - Verify email address

3. **Project Files Ready**
   - All code files present
   - Documentation complete
   - Tested and working

---

## 🔧 Method 1: Using GitHub Desktop (Easiest)

### Step 1: Install GitHub Desktop
1. Download from: https://desktop.github.com/
2. Install and sign in with your GitHub account

### Step 2: Create Repository
1. Open GitHub Desktop
2. Click `File` → `New Repository`
3. Fill in details:
   - **Name**: `lan-collaboration-tool`
   - **Description**: `Real-time LAN collaboration tool with chat, file sharing, screen sharing, and video conferencing`
   - **Local Path**: Choose parent folder (not project folder itself)
   - ✅ Check "Initialize with README" → **NO** (we already have one)
   - **Git Ignore**: Python
   - **License**: MIT

4. Click `Create Repository`

### Step 3: Add Your Files
1. Copy all project files to the new repository folder created by GitHub Desktop
2. GitHub Desktop will automatically detect changes
3. Review files in the "Changes" tab

### Step 4: Make First Commit
1. In GitHub Desktop, write commit message:
   - **Summary**: `Initial commit - LAN Collaboration Tool v1.0.0`
   - **Description**: `Complete implementation with chat, files, screen sharing, audio, and video`
2. Click `Commit to main`

### Step 5: Publish to GitHub
1. Click `Publish repository` button (top right)
2. Uncheck "Keep this code private" if you want it public
3. Click `Publish Repository`

✅ **Done!** Your project is now on GitHub.

---

## 💻 Method 2: Using Command Line (Advanced)

### Step 1: Prepare Local Repository

```bash
# Navigate to your project folder
cd "D:\OneDrive\Desktop\Semester 5\Computer Networks\Project\lan-collaboration-tool"

# Initialize git repository
git init

# Add all files
git add .

# Make first commit
git commit -m "Initial commit - LAN Collaboration Tool v1.0.0"
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Fill in:
   - **Repository name**: `lan-collaboration-tool`
   - **Description**: `Real-time LAN collaboration tool with chat, file sharing, screen sharing, and video conferencing`
   - **Visibility**: Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we have them)
3. Click `Create repository`

### Step 3: Link and Push

GitHub will show you commands. Use these:

```bash
# Add remote repository
git remote add origin https://github.com/YOUR-USERNAME/lan-collaboration-tool.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**Enter your GitHub credentials when prompted.**

✅ **Done!** Project uploaded.

---

## 🔐 Method 3: Using Personal Access Token (Most Secure)

### Step 1: Create Personal Access Token

1. Go to GitHub → Settings → Developer settings
2. Click "Personal access tokens" → "Tokens (classic)"
3. Click "Generate new token (classic)"
4. Give it a name: `LAN-Collab-Tool-Upload`
5. Select scopes:
   - ✅ `repo` (all)
6. Click "Generate token"
7. **COPY THE TOKEN** (you won't see it again!)

### Step 2: Use Token for Authentication

```bash
# When pushing, use token as password
git push -u origin main

Username: YOUR-GITHUB-USERNAME
Password: PASTE-YOUR-TOKEN-HERE
```

Or configure Git to remember:

```bash
# Store credentials (Windows)
git config --global credential.helper wincred

# Store credentials (Mac/Linux)
git config --global credential.helper store
```

---

## 📝 Post-Upload Checklist

### 1. Update README on GitHub
- [ ] Replace `YOUR-USERNAME` with actual username
- [ ] Update email address
- [ ] Add team member names
- [ ] Add project banner/logo (optional)

### 2. Add Topics/Tags
On GitHub repository page:
- Click ⚙️ (Settings wheel) next to "About"
- Add topics: `python`, `networking`, `lan`, `collaboration`, `video-conferencing`, `file-sharing`, `tkinter`

### 3. Create Releases
1. Go to "Releases" → "Create a new release"
2. Tag: `v1.0.0`
3. Title: `LAN Collaboration Tool v1.0.0`
4. Description: Copy from CHANGELOG.md
5. Upload ZIP of source code
6. Click "Publish release"

### 4. Add Screenshots (Optional but Recommended)
1. Take screenshots of:
   - Main interface
   - File transfer in action
   - Video conference
   - Screen sharing
2. Upload to `docs/` folder
3. Update README.md with image links:
   ```markdown
   ![Main Interface](docs/main-interface.png)
   ```

### 5. Enable GitHub Pages (Optional - for documentation)
1. Settings → Pages
2. Source: `main` branch, `/docs` folder
3. Save

---

## 🎯 Common Issues & Solutions

### Issue 1: "Permission Denied"
**Solution**:
```bash
# Use SSH instead of HTTPS
git remote set-url origin git@github.com:YOUR-USERNAME/lan-collaboration-tool.git
```

### Issue 2: "Repository Already Exists"
**Solution**:
```bash
# Force push (CAUTION: overwrites remote)
git push -u origin main --force
```

### Issue 3: "Large Files Warning"
**Solution**:
```bash
# Remove large files from git history
git filter-branch --tree-filter 'rm -f path/to/large/file' HEAD
```

### Issue 4: "Authentication Failed"
**Solution**:
- Use Personal Access Token instead of password
- Enable 2FA on GitHub account
- Check token has correct permissions

---

## 🔄 Updating Your Repository Later

```bash
# Make changes to your code
# ... edit files ...

# Check what changed
git status

# Add changes
git add .

# Commit with message
git commit -m "Fix: webcam error handling"

# Push to GitHub
git push origin main
```

---

## 📊 Repository Structure After Upload

```
lan-collaboration-tool/
│
├── .gitignore              ← Ignore unnecessary files
├── .github/                ← GitHub specific (optional)
│   └── workflows/          ← CI/CD (optional)
├── docs/                   ← Documentation & screenshots
│   └── README.md
├── server_files/           ← File storage (ignored except .gitkeep)
│   └── .gitkeep
│
├── client.py               ← Main client code
├── server.py               ← Main server code
├── Requirements.txt        ← Dependencies
│
├── README.md               ← Main documentation
├── LICENSE                 ← MIT License
├── CHANGELOG.md            ← Version history
└── CONTRIBUTING.md         ← Contribution guide
```

---

## 🌟 Making Your Repo Stand Out

### 1. Add Badges to README
```markdown
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Stars](https://img.shields.io/github/stars/YOUR-USERNAME/lan-collaboration-tool)
![Issues](https://img.shields.io/github/issues/YOUR-USERNAME/lan-collaboration-tool)
```

### 2. Create a Demo Video
- Record a walkthrough
- Upload to YouTube
- Add link to README

### 3. Add GitHub Actions (CI/CD)
Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r Requirements.txt
      - run: python -m pytest
```

### 4. Enable Discussions
Repository → Settings → Features → ✅ Discussions

---

## 📞 Need Help?

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **GitHub Community**: https://github.community/

---

## ✅ Final Checklist Before Sharing

- [ ] All files committed and pushed
- [ ] README.md looks good on GitHub
- [ ] Requirements.txt is complete
- [ ] License file included
- [ ] .gitignore working (no unwanted files)
- [ ] Repository is public (if intended)
- [ ] Topics/tags added
- [ ] Release created
- [ ] Repository description added
- [ ] Screenshots included (optional)
- [ ] Personal info updated (email, username)

**Congratulations! Your project is now live on GitHub! 🎉**

Share the link:
```
https://github.com/YOUR-USERNAME/lan-collaboration-tool
```
