# MCP Server Project

This repository contains an implementation of a Model Context Protocol (MCP) server. This project demonstrates how to build and run a functional MCP server that can integrate with LLM clients like Claude Desktop.


## System Requirements

- Python 3.11 or higher (as specified in `pyproject.toml`)
- `uv` package manager
- Dependencies listed in `pyproject.toml` (e.g., `mcp[cli]`, `httpx`, `langchain`)

## Getting Started

### 1. Install `uv` Package Manager

If you don't have `uv` installed, you can install it using:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Restart your terminal after installation.

### 2. Project Setup

Clone this repository (if you haven't already) and navigate into the project directory:
```bash
# cd /path/to/your/mcp-server
```

Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt # Or use uv pip install -e . if setup.py or pyproject.toml is configured for editable install
# Based on your pyproject.toml, you might also directly use:
# uv add beautifulsoup4 httpx "mcp[cli]" langchain langchain-community langchain-core chromadb
# Or more simply if pyproject.toml is complete:
# uv sync
```
*(Note: Ensure your `pyproject.toml` is complete or you have a `requirements.txt` for `uv pip install -r requirements.txt`. `uv sync` is often preferred if `pyproject.toml` defines all dependencies.)*

### 3. Running the Server

To start the MCP server, run:
```bash
uv run main.py
```
The server will start and be ready to accept connections.

## Connecting to Claude Desktop

To connect this MCP server to Claude Desktop:

1.  Ensure Claude Desktop is installed.
2.  Edit the Claude Desktop configuration file located at `~/Library/Application Support/Claude/claude_desktop_config.json` (on macOS).
3.  Add or update the `mcpServers` section:

    ```json
    {
        "mcpServers": {
            "mcp-server": { // You can choose any name
                "command": "/full/path/to/your/.venv/bin/uv", // Use absolute path to uv in your venv
                "args": [
                    "run",
                    "main.py"
                ],
                "dir": "/full/path/to/your/mcp-server" // Absolute path to this project directory
            }
        }
    }
    ```
    **Important:** Replace `/full/path/to/your/...` with the correct absolute paths on your system. Using the `uv` from your project's virtual environment is recommended.

4.  Restart Claude Desktop.


## Acknowledgements

This project is inspired by and builds upon the concepts demonstrated in Alejandro AO's `mcp-server-example`. We extend our gratitude to Alejandro for providing a clear and helpful example for the community. You can find his original work here: [https://github.com/alejandro-ao/mcp-server-example](https://github.com/alejandro-ao/mcp-server-example).

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details (if one exists).
