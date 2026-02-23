import subprocess
import select
import time
import sys
import logging
from .models import AgentEvent
from .event_bus import get_global_bus
from .config import get_config

logger = logging.getLogger(__name__)

# To prevent infinite recursion if patched multiple times
_ORIGINAL_POPEN = subprocess.Popen
_PATCHED = False

class ObservablePopen(_ORIGINAL_POPEN):
    """Wraps subprocess.Popen to detect when a process is stalled waiting for stdin."""
    
    def __init__(self, *args, **kwargs):
        # We don't intercept __init__ arguments directly to remain fully compatible
        # with standard library subprocess.Popen signature.
        super().__init__(*args, **kwargs)
        
        # Load timeout from config, default 30s
        config = get_config()
        self._stall_timeout = config.stall_timeout_seconds
        self._bus = get_global_bus()
        self._last_output_time = time.monotonic()
        self._stalled = False

    def communicate(self, input=None, timeout=None):
        """Override communicate to observe blocking behavior before input is provided."""
        
        # If input is provided immediately, it's not blocking for interactive input
        if self.stdin and input is None:
            # We are waiting for output, but we might be blocked on stdin
            try:
                 return self._communicate_with_observation(timeout)
            except Exception as e:
                 logger.error(f"Error in observable communicate: {e}")
                 # Fallback to standard communicate if observation fails
                 return super().communicate(input, timeout)
                 
        return super().communicate(input, timeout)

    def _communicate_with_observation(self, timeout=None):
        """Reads stdout/stderr with a select loop to detect stalls."""
        stdout_data = []
        stderr_data = []
        
        # We need pipes to observe. If standard streams aren't piped, we can't observe them this way.
        reads = []
        if self.stdout is not None:
             reads.append(self.stdout)
        if self.stderr is not None:
             reads.append(self.stderr)
             
        if not reads:
             # Nothing to observe via select
             return super().communicate(None, timeout)

        start_time = time.monotonic()
        
        while self.poll() is None:
             # Check for timeout
             if timeout is not None and (time.monotonic() - start_time) > timeout:
                  # Standard behavior is to raise TimeoutExpired
                  super().kill()
                  raise subprocess.TimeoutExpired(self.args, timeout)

             # Wait up to 1 second for output
             
             # Windows select() only works on sockets, not pipes.
             # This is a major limitation of Python on Windows.
             if sys.platform != 'win32':
                 try:
                     rlist, _, _ = select.select(reads, [], [], 1.0)
                 except (select.error, OSError):
                     # Usually means a pipe was closed
                     break
                 
                 if rlist:
                     self._last_output_time = time.monotonic()
                     if self._stalled:
                          self._stalled = False
                          # Recovered from stall
                 else:
                     # Select timed out (1 second elapsed, no output)
                     elapsed = time.monotonic() - self._last_output_time
                     if elapsed > self._stall_timeout and not self._stalled:
                          self._stalled = True
                          logger.warning(f"Subprocess stalled (PID {self.pid}): No output for {elapsed:.1f}s")
                          self._bus.publish(AgentEvent(
                              type="stdin_request",
                              source="subprocess_patch",
                              payload={"pid": self.pid, "args": self.args},
                              severity="warning"
                          ))
             else:
                 # Windows fallback: we cannot use select on pipes.
                 # To faithfully detect stalls on Windows without select, we'd need
                 # background threads reading stdout/stderr with timeouts, or 
                 # peekconsole if it was a visible console.
                 # For now, we emulate a simple busy wait check if it's taking too long
                 # without complex thread-based readers.
                 time.sleep(1.0)
                 elapsed = time.monotonic() - self._last_output_time
                 if elapsed > self._stall_timeout and not self._stalled:
                      self._stalled = True
                      logger.debug(f"Subprocess potentially stalled (PID {self.pid}) on Windows: Running for {elapsed:.1f}s")
                      self._bus.publish(AgentEvent(
                          type="stdin_request",
                          source="subprocess_patch",
                          payload={"pid": self.pid, "args": self.args, "os": "windows_fallback"},
                          severity="warning"
                      ))

        # Once the process ends, read any remaining output standardly
        return super().communicate(None, timeout)

def apply_patch():
    """Monkey-patch subprocess.Popen globally."""
    global _PATCHED
    if not _PATCHED:
        subprocess.Popen = ObservablePopen
        _PATCHED = True
        logger.info("Applied global subprocess.Popen patch for stall detection.")

def remove_patch():
    """Restore original subprocess.Popen."""
    global _PATCHED
    if _PATCHED:
        subprocess.Popen = _ORIGINAL_POPEN
        _PATCHED = False
        logger.info("Removed global subprocess.Popen patch.")
