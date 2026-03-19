# Google Workspace MCP Server

## Project Overview

A comprehensive Google Workspace MCP (Model Context Protocol) server that exposes Google Workspace tools over HTTP. It integrates with Gmail, Google Drive, Calendar, Docs, Sheets, Slides, Forms, Tasks, Chat, Contacts, Search, and Apps Script.

## Architecture

- **Language**: Python 3.11
- **Framework**: FastMCP 3.x (built on FastAPI + Uvicorn)
- **Transport**: Streamable HTTP (primary) or STDIO
- **Protocol**: Model Context Protocol (MCP)
- **Auth**: Google OAuth 2.0 (multi-user or single-user mode)

## Project Structure

```
main.py                  - Entry point, argument parsing, server startup
fastmcp_server.py        - FastMCP server configuration
core/                    - Core server, config, logging, tool registry
auth/                    - OAuth 2.0/2.1 authentication, middleware
gmail/                   - Gmail MCP tools
gdrive/                  - Google Drive MCP tools
gcalendar/               - Google Calendar MCP tools
gdocs/                   - Google Docs MCP tools
gsheets/                 - Google Sheets MCP tools
gslides/                 - Google Slides MCP tools
gforms/                  - Google Forms MCP tools
gtasks/                  - Google Tasks MCP tools
gchat/                   - Google Chat MCP tools
gcontacts/               - Google Contacts MCP tools
gsearch/                 - Google Search MCP tools
gappsscript/             - Google Apps Script MCP tools
```

## Running the Server

```bash
# HTTP transport (default port 5000)
PORT=5000 python3 main.py --transport streamable-http

# STDIO transport
python3 main.py
```

## Configuration

Key environment variables:
- `GOOGLE_OAUTH_CLIENT_ID` - Google OAuth Client ID (required)
- `GOOGLE_OAUTH_CLIENT_SECRET` - Google OAuth Client Secret (required)
- `PORT` / `WORKSPACE_MCP_PORT` - Server port (default: 8000, workflow uses 5000)
- `WORKSPACE_MCP_HOST` - Server host (default: 0.0.0.0)
- `WORKSPACE_MCP_BASE_URI` - Base URI for OAuth callbacks
- `MCP_ENABLE_OAUTH21` - Enable OAuth 2.1 multi-user mode
- `WORKSPACE_MCP_STATELESS_MODE` - Enable stateless mode (requires OAuth 2.1)

See `.env.oauth21` for a full configuration example.

## Workflow

- **Start application**: `PORT=5000 python3 main.py --transport streamable-http` (port 5000, console output)

## Dependencies

Managed via pip (Python packages):
- fastapi, fastmcp, uvicorn
- google-api-python-client, google-auth-httplib2, google-auth-oauthlib
- httpx, pyjwt, python-dotenv, pyyaml, cryptography, defusedxml, py-key-value-aio
