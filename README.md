# GCP MCP Server

Extended Google Cloud Platform MCP server with 200+ tools for Google Workspace and GCP services.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

## Features

### Google Workspace
- **Gmail** - Search, send, manage emails and attachments
- **Drive** - File operations, sharing, Office format support
- **Calendar** - Events, scheduling, availability
- **Docs** - Create, edit, format documents
- **Sheets** - Spreadsheet operations with formatting
- **Slides** - Presentation management
- **Forms** - Form creation and response handling
- **Tasks** - Task and task list management
- **Contacts** - Contact and group management
- **Chat** - Space messaging and reactions
- **Apps Script** - Automate and execute custom code

### Google Cloud Platform
- **Cloud Storage** - Bucket and object management
- **Pub/Sub** - Topics, subscriptions, messaging
- **Cloud Functions** - Deploy and invoke serverless functions
- **Admin SDK** - User and group management
- **Vault** - eDiscovery and compliance

### Consumer Apps
- **Keep** - Note management
- **Photos** - Album and media management
- **YouTube** - Video search and channel info
- **Maps** - Places, directions, geocoding

## Quick Start

```bash
# Set credentials
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-secret"

# Run the server
uv run main.py --transport streamable-http
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth client ID from Google Cloud |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth client secret |
| `MCP_ENABLE_OAUTH21` | Enable OAuth 2.1 support |
| `USER_GOOGLE_EMAIL` | Default email for single-user auth |

### Google Cloud Setup

1. Create a project at [console.cloud.google.com](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials (Desktop Application)
3. Enable required APIs:
   - Calendar, Drive, Gmail, Docs, Sheets, Slides, Forms, Tasks, Chat, People
   - Keep, Photos Library, YouTube Data
   - Cloud Storage, Pub/Sub, Cloud Functions
   - Admin SDK, Vault

## Available Tools

| Module | Tools |
|--------|-------|
| Gmail | 14 tools |
| Drive | 13 tools |
| Calendar | 10 tools |
| Docs | 18 tools |
| Sheets | 10 tools |
| Slides | 7 tools |
| Forms | 5 tools |
| Tasks | 6 tools |
| Contacts | 8 tools |
| Chat | 6 tools |
| Apps Script | 9 tools |
| Search | 2 tools |
| Keep | 6 tools |
| Photos | 6 tools |
| YouTube | 6 tools |
| Maps | 5 tools |
| Cloud Storage | 9 tools |
| Pub/Sub | 10 tools |
| Cloud Functions | 4 tools |
| Admin SDK | 9 tools |
| Vault | 7 tools |

**Total: ~200 tools**

## Development

```bash
# Install dependencies
uv sync --group dev

# Run tests
uv run pytest

# Start server
uv run main.py --transport streamable-http
```

## License

MIT
