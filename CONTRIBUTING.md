# Contributing to Pixel Knight

Thank you for your interest in contributing to Pixel Knight! 🎉

## Ways to Contribute

### 🐛 Bug Reports

Found a bug? Please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- Your environment (OS, Python version, browser)

### 💡 Feature Requests

Have an idea? Open an issue with:
- Description of the feature
- Use case / why it would be useful
- Any implementation ideas (optional)

### 🔧 Code Contributions

1. **Fork the repository**
2. **Create a branch** for your feature/fix:
   ```bash
   git checkout -b feature/my-awesome-feature
   ```
3. **Make your changes**
4. **Test your changes**:
   ```bash
   # Run tests
   pytest tests/
   
   # Run the app and verify manually
   ./start.sh
   ```
5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add awesome feature"
   ```
6. **Push and create a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/pixel_knight.git
cd pixel_knight

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

## Code Style

### Python (Backend)
- Use **type hints** where possible
- Follow **PEP 8** conventions
- Use **async/await** for I/O operations
- Add **docstrings** to functions and classes

```python
async def my_function(param: str) -> dict:
    """
    Brief description of function.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    pass
```

### JavaScript (Frontend)
- Use **const/let** (no var)
- Use **async/await** for API calls
- Keep functions small and focused
- Comment complex logic

### CSS
- Use **CSS variables** for colors/spacing
- Follow the existing cyberpunk theme
- Keep selectors specific but not overly nested

## Project Structure

```
pixel_knight/
├── backend/           # FastAPI backend
│   ├── services/      # Business logic
│   └── main.py        # API endpoints
├── frontend/          # Vanilla JS frontend
├── tests/             # pytest tests
└── data/              # Local storage (gitignored)
```

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting (no code change)
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance

Examples:
```
feat: add support for Mistral AI provider
fix: resolve streaming issue with Claude models
docs: update README with Groq setup instructions
```

## Pull Request Guidelines

- **Keep PRs focused** - One feature/fix per PR
- **Update documentation** if needed
- **Add tests** for new features
- **Don't break existing functionality**
- **Describe your changes** in the PR description

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=backend

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_get_models
```

## Adding a New Provider

1. Add provider type to `backend/models.py`:
   ```python
   class APIProviderType(str, Enum):
       # ...existing providers...
       NEW_PROVIDER = "new_provider"
   ```

2. Add default config to `backend/services/provider_service.py`:
   ```python
   DEFAULT_PROVIDERS = {
       # ...existing...
       "new_provider": {
           "name": "New Provider",
           "type": APIProviderType.NEW_PROVIDER,
           "api_base": "https://api.newprovider.com/v1",
           "api_key": "",
       },
   }
   ```

3. Update icon in `frontend/app.js`:
   ```javascript
   getProviderIcon(type) {
       const icons = {
           // ...existing...
           'new_provider': '🆕',
       };
   }
   ```

4. Test the integration!

## Adding a New Feature

1. **Backend**: Add endpoint in `main.py`, service logic in `services/`
2. **Frontend**: Add UI in `index.html`, styles in `styles.css`, logic in `app.js`
3. **Tests**: Add tests in `tests/`
4. **Docs**: Update README if needed

## Questions?

- Open an issue for questions
- Check existing issues/PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make Pixel Knight better! 🚀

