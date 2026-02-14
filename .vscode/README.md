# VS Code Configuration Guide

This directory contains VS Code configuration files for the GridWise project.

## 🚀 Quick Start

### Run the API

**Method 1: Using Debug Panel (F5)**
1. Open VS Code
2. Press `F5` or go to Run & Debug panel
3. Select **"GridWise API (FastAPI)"**
4. Click the green play button

**Method 2: Using Tasks (Ctrl+Shift+B)**
1. Press `Ctrl+Shift+B` (or `Cmd+Shift+B` on Mac)
2. The default task "Start GridWise API" will run

The API will be available at:
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **API Root:** http://localhost:8000/

---

## 🐛 Debug Configurations

### Available Configurations (launch.json)

1. **GridWise API (FastAPI)** - Development mode with hot reload
   - Auto-reloads on file changes
   - Uses port 8000
   - Loads `.env` file
   - Full debugging support

2. **GridWise API (Production Mode)** - Production-like mode
   - No auto-reload
   - Single worker
   - Better for testing production behavior

3. **Run Tests** - Run pytest with debugging
   - Runs all tests in `service/tests/`
   - Can set breakpoints in tests
   - Shows verbose output

4. **Seed Database** - Run database seeding script
   - Populates MongoDB with initial data
   - Useful for resetting database

### How to Use
- Press `F5` to start the default configuration
- Or open Run & Debug panel (Ctrl+Shift+D) and select from dropdown

---

## ⚙️ Tasks (tasks.json)

### How to Run Tasks

**Quick Task Menu:**
- Press `Ctrl+Shift+P` (or `Cmd+Shift+P`)
- Type "Tasks: Run Task"
- Select from list

**Default Build Task:**
- Press `Ctrl+Shift+B` (or `Cmd+Shift+B`)
- Runs "Start GridWise API"

**Default Test Task:**
- Press `Ctrl+Shift+P` → "Tasks: Run Test Task"
- Runs pytest

### Available Tasks

**Development:**
- ✅ **Start GridWise API** - Start FastAPI server (default build task)
- 🧪 **Run Tests** - Run all tests (default test task)
- 📊 **Run Tests with Coverage** - Generate HTML coverage report
- 📋 **Generate OpenAPI Spec** - Update API documentation

**Database:**
- 🌱 **Seed Database** - Populate with initial data
- 🔍 **Explore Database** - View database contents
- 🗄️ **Start MongoDB (Docker)** - Start MongoDB container
- ⏹️ **Stop MongoDB (Docker)** - Stop MongoDB container
- 💻 **MongoDB Shell** - Open mongosh terminal

**Code Quality:**
- 🎨 **Format Code (Ruff)** - Auto-format Python files
- 🔍 **Lint Code (Ruff)** - Check and fix linting issues
- 📝 **Type Check (mypy)** - Run type checking

---

## 🔧 Settings (settings.json)

### Key Features

**Python Configuration:**
- Auto-detects virtual environment (`.venv`)
- Loads environment variables from `.env`
- Uses Ruff for formatting and linting

**Testing:**
- Pytest integration enabled
- Test discovery in `service/tests/`
- Can run tests from Test Explorer

**Auto-formatting:**
- Format on save enabled
- Auto-organize imports
- Auto-fix linting issues

**Performance:**
- Excludes `.venv`, `__pycache__`, etc. from file watcher
- Improves VS Code responsiveness

---

## 📝 Keyboard Shortcuts

| Action | Shortcut (Mac) | Shortcut (Windows/Linux) |
|--------|----------------|--------------------------|
| Start Debugging | `F5` | `F5` |
| Run Build Task | `Cmd+Shift+B` | `Ctrl+Shift+B` |
| Open Debug Panel | `Cmd+Shift+D` | `Ctrl+Shift+D` |
| Command Palette | `Cmd+Shift+P` | `Ctrl+Shift+P` |
| Run Task | `Cmd+Shift+P` → Tasks | `Ctrl+Shift+P` → Tasks |
| Toggle Terminal | `` Ctrl+` `` | `` Ctrl+` `` |

---

## 🔌 Recommended Extensions

Install these VS Code extensions for the best experience:

```bash
# Install all at once (paste in terminal):
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension ms-python.debugpy
```

**Essential:**
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) - Python language support
- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) - Fast Python language server
- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) - Fast Python linter/formatter
- [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy) - Debugging support

**Optional:**
- [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) - Test API endpoints
- [MongoDB for VS Code](https://marketplace.visualstudio.com/items?itemName=mongodb.mongodb-vscode) - MongoDB integration
- [Thunder Client](https://marketplace.visualstudio.com/items?itemName=rangav.vscode-thunder-client) - API testing

---

## 🐛 Troubleshooting

### "Python interpreter not found"
1. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose `./service/.venv/bin/python`

### "Module not found" errors
1. Make sure virtual environment is activated
2. Check that `PYTHONPATH` is set correctly in launch.json
3. Try reloading VS Code window

### MongoDB connection errors
1. Make sure MongoDB is running: Run task "Start MongoDB (Docker)"
2. Check `.env` file has correct `MONGODB_URL`
3. Verify with: `docker ps | grep gridwise-mongo`

### Tests not discovered
1. Check Python interpreter is from `.venv`
2. Reload Test Explorer (click refresh icon)
3. Check `python.testing.pytestArgs` in settings.json

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [VS Code Python Documentation](https://code.visualstudio.com/docs/python/python-tutorial)
- [Debugging in VS Code](https://code.visualstudio.com/docs/editor/debugging)
- [VS Code Tasks](https://code.visualstudio.com/docs/editor/tasks)
