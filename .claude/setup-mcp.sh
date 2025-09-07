#!/bin/bash

# playwright mcp
claude mcp add playwright --scope user npx @playwright/mcp@latest

# figma mcp
claude mcp add --transport http --scope user figma-dev-mode-mcp-server http://127.0.0.1:3845/mcp

# ref mcp
claude mcp add --transport http --scope user Ref "https://api.ref.tools/mcp?apiKey=$1"

# atlassian
claude mcp add --transport sse --scope user atlassian https://mcp.atlassian.com/v1/sse
