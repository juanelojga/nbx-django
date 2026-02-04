# MCP Django Server Setup

This project includes `mcp-django`, an MCP server that allows LLM clients to interact with the Django project through a stateful Python shell.

## Features

- **Django Project Exploration**: Access project info, apps, and models via MCP resources
- **Stateful Python Shell**: Execute Python code in a persistent Django environment
- **Session Management**: Reset shell sessions as needed

## Installation

The package is already added to `requirements.txt`. To install:

```bash
pip install -r requirements.txt
```

Or with the virtual environment activated:
```bash
pip install mcp-django
```

## MCP Client Configuration

### VS Code

The MCP configuration is in `.vscode/mcp.json`. VS Code should automatically detect it.

### Claude Desktop

Add the following to your Claude Desktop configuration:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "django": {
      "command": "python",
      "args": ["-m", "mcp_django"],
      "cwd": "/home/juanelojga/Code/nbx-django/nbxdjango",
      "env": {
        "DJANGO_SETTINGS_MODULE": "nbxdjango.settings"
      }
    }
  }
}
```

### Kimi Code CLI

Add the following to your Kimi Code CLI configuration file (run `kimi config` to find it):

```yaml
mcp_servers:
  django:
    command: python
    args:
      - -m
      - mcp_django
    env:
      DJANGO_SETTINGS_MODULE: nbxdjango.settings
    cwd: /home/juanelojga/Code/nbx-django/nbxdjango
```

## Usage

### Running the MCP Server

**Option 1: Direct module execution (recommended)**
```bash
cd nbxdjango
python -m mcp_django
```

**Option 2: Using Django management command**
```bash
cd nbxdjango
python manage.py mcp
```

### Available Resources

- `django://project` - Project information and configuration
- `django://apps` - List of installed apps and their models
- `django://models` - Detailed model information

### Available Tools

- `shell` - Execute Python code in a Django environment
- `shell_reset` - Reset the shell session

## Example Usage

Once connected to an MCP client, you can:

1. Explore the project structure through resources
2. Execute Django ORM queries via the shell tool
3. Interact with models and perform database operations

Example shell commands:
```python
# Query all users
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.all()

# Create a new instance
from packagehandling.models import Package
Package.objects.create(name="Test Package", ...)
```
