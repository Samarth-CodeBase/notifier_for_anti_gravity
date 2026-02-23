# Attention Alert MCP Server Setup Guide

This guide explains how to install and configure the `attention_alert` Model Context Protocol (MCP) server for your autonomous AI agent (e.g., AntiGravity).

This server exposes tools for notifying the user via their OS desktop UI (and audio beeps) and contains a watchdog timer that will automatically trigger notifications if the agent stalls without explicitly asking the user for help.

## 1. Installation

The extension relies on the official `mcp` SDK and os-specific notification packages.

```bash
# Install the core MCP SDK and cross-platform fallback
pip install mcp plyer

# If you are on Windows, install the native toast library for better reliability
pip install windows-toasts
```

## 2. Configuration

1. You can use the provided `config.yaml.example` as a starting point. Create a `config.yaml` file in the same directory as the server.

   ```yaml
   attention_alert:
     enabled: true
     stall_timeout_seconds: 30
     backends:
       audio:
         enabled: true
       desktop:
         enabled: true
   ```

## 3. MCP Server Integration

You do not need to modify your agent's Python code directly. Instead, you register this repository as an MCP Server in your agent environment. 

Add the following JSON to your MCP configuration file (typically located at `C:\Users\Saksham\.gemini\antigravity\mcp_config.json` for AntiGravity, or your respective Claude/Cursor config):

```json
{
  "mcpServers": {
    "attention-alert": {
      "command": "python",
      "args": ["-m", "extensions.attention_alert.server"],
      "env": {
        "PYTHONPATH": "c:/Users/Saksham/.gemini/antigravity/scratch/notifier_for_anti_gravity"
      }
    }
  }
}
```

> **Note:** Update the `PYTHONPATH` appropriately if you move the codebase to a new permanent directory.

## 4. How the Tools Work

Once the MCP server initializes, it exposes two native tools to the agent:

1. **`notify_user(message: str, urgency_level: str)`**: The agent can explicitly invoke this tool when it hits a natural stopping point to demand the user's attention (e.g., waiting for permission).
2. **`pet_watchdog()`**: The agent should routinely ping this tool to reset the internal 30-second stall timer. If the agent enters an infinite loop or freezes on a long-running subprocess without regularly petting the watchdog, the server will automatically intercept and trigger an audible desktop alert to pull the human back to the screen.

### Clean Shutdown
The background thread containing the watchdog timer is tied cleanly to the MCP Server lifecycle. When the host app closes the stdio pipeline to shutdown the MCP Server, the `finalizer` block will safely stop the thread and exit without leaving zombies.
