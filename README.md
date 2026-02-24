# Attention Alert MCP for AntiGravity

![AntiGravity](https://img.shields.io/badge/AntiGravity-Agentic%20Coding-blueviolet)
![MCP](https://img.shields.io/badge/MCP-Protocol-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Attention Alert MCP** is a smart interruption subsystem designed for the **AntiGravity** agentic AI. It provides a robust mechanism to draw the user's attention using desktop notifications and audio alerts precisely when the agent is blocked or requires human intervention.

## 🚀 Why Attention Alert?

Agentic AI systems often run complex, long-duration tasks. If an agent gets stuck on a prompt, hits a rate limit, or requires a critical decision, it can sit idle for hours without the user knowing. **Attention Alert** solves this by:

- **Audible Alerts**: Wake up the user with sound when attention is needed.
- **Desktop Notifications**: Flash a system-level popup that persists until acknowledged.
- **Smart Watchdog**: Automatically detects if the agent has stalled or been silent for too long and triggers an "I'm stuck" alert.
- **Deduplication**: Prevents notification fatigue by suppressing repetitive alerts.

## ✨ Key Features

- **Multi-Backend Support**: Includes `Audio` (cross-platform), `Desktop` (Windows/macOS/Linux), and `Popup UI` backends.
- **Execution Watchdog**: A background timer that triggers if the agent hasn't "petted" the watchdog within a configurable timeout.
- **FastMCP Integration**: Built on top of the Model Context Protocol (MCP) for seamless integration with AntiGravity and other MCP-compliant hosts.
- **Indefinite Popups**: Notifications on Windows can be configured to stay active until the user clicks them, ensuring critical alerts aren't missed.

## 🛠️ Installation

```bash
git clone https://github.com/Samarth-CodeBase/notifier_for_anti_gravity.git
cd notifier_for_anti_gravity
pip install -r requirements.txt
```

### Setup for AntiGravity
Add the following to your AntiGravity configuration to enable the extension:

```yaml
extensions:
  - path: ./extensions/attention_alert
    enabled: true
```

## 🎮 Usage

Once integrated, the agent has access to the following tools:

### `notify_user(message, urgency_level)`
Explicitly sends a notification.
- **message**: The text to display.
- **urgency_level**: `info`, `warning`, `critical`.

### `pet_watchdog()`
Resets the stall timer. The agent should call this regularly during successful multi-step executions.

## ⚙️ Configuration

Copy `config.yaml.example` to `config.yaml` and customize your settings:

```yaml
stall_timeout_seconds: 300  # Alert if silent for 5 minutes
backends:
  audio:
    enabled: true
    volume: 0.8
  desktop:
    enabled: true
    indefinite: true  # Keep popup open until clicked
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue for bug reports and feature requests.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

*Built with ❤️ for the AntiGravity ecosystem.*
