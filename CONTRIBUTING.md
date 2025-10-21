# Contributing to LAN Collaboration Tool

Thank you for considering contributing to this project! 🎉

## How to Contribute

### Reporting Bugs
- Check if the bug has already been reported in Issues
- Include detailed steps to reproduce
- Specify your OS, Python version, and error messages

### Suggesting Features
- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Explain how it would benefit users

### Code Contributions

#### Getting Started
1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/lan-collaboration-tool.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test thoroughly
6. Commit: `git commit -m "Add: description of changes"`
7. Push: `git push origin feature/your-feature-name`
8. Open a Pull Request

#### Code Style
- Follow PEP 8 style guidelines
- Use descriptive variable names
- Add comments for complex logic
- Keep functions focused and modular

#### Testing
- Test on multiple network configurations
- Verify all features work (chat, files, audio, video)
- Check for memory leaks in long sessions
- Test with multiple simultaneous users

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r Requirements.txt

# Run server
python server.py

# Run client (in another terminal)
python client.py
```

## Pull Request Guidelines
- Provide clear description of changes
- Reference related issues
- Include screenshots for UI changes
- Ensure no merge conflicts
- Pass all tests

## Code of Conduct
- Be respectful and constructive
- Welcome newcomers
- Focus on the issue, not the person
- Help others learn and grow

## Questions?
Feel free to open an issue with the "question" label or reach out via email.

Thank you for contributing! 🙌
