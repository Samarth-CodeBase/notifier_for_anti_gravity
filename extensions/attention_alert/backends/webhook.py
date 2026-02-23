import json
import asyncio
import hmac
import hashlib
import logging
import threading
from . import AlertBackend

logger = logging.getLogger(__name__)

class WebhookBackend(AlertBackend):
    """Dispatches a JSON payload via an async HTTP POST request."""

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._enabled = self._config.get("enabled", False)
        self._url = self._config.get("url", "")
        self._secret = self._config.get("secret", "").encode('utf-8')
        
        # Only enable if we have a URL and it's explicitly enabled
        if not self._url:
            if self._enabled:
                logger.warning("Webhook backend enabled but no URL provided. Disabling.")
            self._enabled = False

        try:
             import httpx
             self._httpx = httpx
        except ImportError:
             if self._enabled:
                  logger.warning("httpx not installed, webhook notifications will be disabled.")
             self._enabled = False

    def dispatch(self, title: str, message: str) -> bool:
        if not self._enabled:
            return False

        payload = {
            "title": title,
            "message": message,
            "source": "antigravity_attention_alert"
        }
        
        # Create a new thread to run the async dispatch so we don't block the caller
        threading.Thread(
            target=self._run_async_dispatch,
            args=(payload,),
            daemon=True
        ).start()
        
        return True

    def _run_async_dispatch(self, payload: dict):
        """Helper to run the async coroutine in a new thread's event loop."""
        asyncio.run(self._async_dispatch(payload))

    async def _async_dispatch(self, payload: dict):
         """Performs the actual HTTP request."""
         body = json.dumps(payload).encode('utf-8')
         headers = {
             "Content-Type": "application/json",
         }
         
         if self._secret:
             signature = hmac.new(self._secret, body, hashlib.sha256).hexdigest()
             headers["X-Hub-Signature-256"] = f"sha256={signature}"

         try:
             async with self._httpx.AsyncClient() as client:
                 response = await client.post(
                     self._url,
                     content=body,
                     headers=headers,
                     timeout=10.0
                 )
                 response.raise_for_status()
                 logger.debug(f"Webhook dispatched successfully: {response.status_code}")
         except Exception as e:
             logger.error(f"Failed to dispatch webhook to {self._url}: {e}")
