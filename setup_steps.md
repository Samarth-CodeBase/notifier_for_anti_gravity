# Attention Interrupt Subsystem Setup Guide

This guide explains how to install and integrate the `attention_alert` extension into your autonomous AI agent (e.g., AntiGravity).

## 1. Installation

1. **Copy the extension**: Move the `extensions/attention_alert` folder into your agent's source code directory (e.g., alongside your other modules or plugins).
2. **Install dependencies**: The extension relies on a few Python packages for cross-platform notifications.
   ```bash
   pip install plyer httpx
   ```

## 2. Configuration

1. Create a `config.yaml` file in the same directory as your agent's main entry point, or directly inside the `attention_alert` folder.
2. You can use the provided `config.yaml.example` as a starting point:

   ```yaml
   attention_alert:
     enabled: true
     cooldown_seconds: 10
     stall_timeout_seconds: 30
     backends:
       audio:
         enabled: true
       desktop:
         enabled: true
       webhook:
         enabled: false
         url: "https://hooks.example.com/agent-alert"
         secret: "YOUR_WEBHOOK_SECRET"
     escalation:
       - delay_seconds: 0
         backend: audio
       - delay_seconds: 30
         backend: desktop
       - delay_seconds: 120
         backend: webhook
     history:
       enabled: true
       db_path: "notifications.db"
       retention_days: 30
   ```
   > **Note:** You can also override configuration via environment variables (e.g., `ALERT_WEBHOOK_SECRET`).

## 3. Initialization

In your agent's main startup script (e.g., `main.py` or `agent.py`), initialize the extension. This **must** be done before any subprocesses are spawned or tools are executed.

```python
from extensions.attention_alert import init

def main():
    # 1. Initialize the Attention Alert subsystem
    init()
    
    # 2. Start your agent's main loop
    agent.run()
```

> **Why this is important:** `init()` patches Python's `subprocess.Popen` globally. Any shell command the agent runs that stalls waiting for `stdin` (like a sudo prompt) will automatically trigger an alert without any further code changes.

## 4. Agent Loop Integration (Watchdog)

To prevent the agent from getting stuck in an infinite planning loop (stalling without executing action), you need to "pet" the watchdog.

Find your agent's main execution loop and add a call to `heartbeat()` at the end of each successful cycle:

```python
from extensions.attention_alert.watchdog import get_watchdog

def agent_execution_loop():
    watchdog = get_watchdog()
    
    while True:
        # 1. Plan next step
        plan = llm.generate_plan()
        
        # 2. Execute tools
        execute_tools(plan)
        
        # 3. Tell the watchdog the agent is healthy and making progress
        watchdog.heartbeat()
```
If `heartbeat()` is not called within `stall_timeout_seconds` (default: 30s), an `execution_stalled` alert will fire.

## 5. Tool Dispatch Integration (Explicit Blocks)

When your agent explicitly pauses to ask the user for permission or input (e.g., a `notify_user` or `ask_human` tool), you must publish an event to let the subsystem know it should alert the user immediately.

```python
import time
from extensions.attention_alert.event_bus import get_global_bus
from extensions.attention_alert.models import AgentEvent

def tool_notify_user(prompt_text):
    bus = get_global_bus()
    
    # 1. Publish the blocking event BEFORE pausing
    bus.publish(AgentEvent(
        type="awaiting_confirmation", # Or "awaiting_user_input", "permission_request"
        source="tool_notify_user",
        payload={"message": prompt_text},
        timestamp=time.monotonic(),
        severity="warning"
    ))
    
    # 2. Pause and wait for user input (blocking call)
    user_response = input(f"Agent asks: {prompt_text}\n> ")
    
    # 3. Publish a recovery event so the cooldown deduplicator resets
    bus.publish(AgentEvent(
        type="execution_running",
        source="tool_notify_user",
        payload={},
        timestamp=time.monotonic(),
        severity="info"
    ))
    
    return user_response
```

## 6. Verification

To verify the setup is working without running your full agent, run the included smoke test:

```bash
python smoke_test.py
```

This will simulate blocking events, test the cooldown suppression, and trigger standard audio/desktop alerts. You can also view the generated `notifications.db` SQLite database to see the audit trail of alerts.
