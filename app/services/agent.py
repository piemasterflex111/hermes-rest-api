"""Agent executor for Hermes REST API.

Spawns `hermes --cli -z "<prompt>"` as a subprocess for each message.
This is the correct approach since hermes --cli is a one-shot command,
not an interactive REPL.
"""
import asyncio
import logging
from typing import List, Optional, AsyncGenerator
from app.config import HERMES_CLI, HERMES_CLI_ARGS, SANDBOX_ENABLED, SANDBOX_DENIED_COMMANDS

logger = logging.getLogger(__name__)

class AgentExecutor:
    """Execute agent commands via hermes --cli."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.message_history: List[str] = []
        self.tool_log: List[str] = []
    
    async def execute(self, prompt: str) -> str:
        """Execute a prompt via hermes --cli and return the result."""
        logger.info(f"[{self.session_id}] Executing: {prompt[:80]}")
        
        cmd = [HERMES_CLI, "--cli", "-z", prompt]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120.0,  # 2 minute timeout
            )
            
            result = stdout.decode().strip()
            error = stderr.decode().strip()
            
            if process.returncode != 0 and not result:
                raise RuntimeError(f"Agent error: {error}")
            
            self.message_history.append(f"User: {prompt}\nAgent: {result[:200]}")
            return result
            
        except asyncio.TimeoutError:
            process.kill()
            raise TimeoutError("Agent execution timed out (120s)")
        except FileNotFoundError:
            raise RuntimeError(f"{HERMES_CLI} not found — is Hermes installed?")
    
    async def execute_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Execute a prompt and stream output line by line."""
        logger.info(f"[{self.session_id}] Streaming: {prompt[:80]}")
        
        cmd = [HERMES_CLI, "--cli", "-z", prompt]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Read stdout line by line
            async for line in process.stdout:
                decoded = line.decode().strip()
                if decoded:
                    yield f"data: {decoded}\n\n"
            
            # Wait for process to finish
            await process.wait()
            
        except Exception as e:
            yield f"data: ERROR: {e}\n\n"
    
    def get_history(self) -> List[str]:
        """Get message history."""
        return self.message_history.copy()
    
    def sandbox_check(self, command: str) -> bool:
        """Check if command is allowed."""
        if not SANDBOX_ENABLED:
            return True
        for denied in SANDBOX_DENIED_COMMANDS:
            if denied in command:
                return False
        return True
