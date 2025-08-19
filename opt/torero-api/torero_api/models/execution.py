"""
Execution models for torero API

This module defines models related to service execution results.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ServiceExecutionResult(BaseModel):
    """
    Result of a service execution.
    
    Represents the output of running a torero service.
    
    Attributes:
        return_code: The exit code returned by the executed service
        stdout: Standard output captured during execution
        stderr: Standard error output captured during execution
        start_time: ISO 8601 timestamp when execution started
        end_time: ISO 8601 timestamp when execution completed
        elapsed_time: Execution duration in seconds
    """
    return_code: int = Field(..., description="Exit code from the execution")
    stdout: str = Field(..., description="Standard output from the execution")
    stderr: str = Field(..., description="Standard error output from the execution") 
    start_time: str = Field(..., description="ISO 8601 timestamp when execution started")
    end_time: str = Field(..., description="ISO 8601 timestamp when execution completed")
    elapsed_time: float = Field(..., description="Execution duration in seconds")
    
    # Pydantic v2 configuration
    model_config = {
        "json_schema_extra": {
            "example": {
                "return_code": 0,
                "stdout": "\nPLAY [Hello World] *************************************************************\n\nTASK [Gathering Facts] *********************************************************\nok: [127.0.0.1]\n\nTASK [Ping my hosts] ***********************************************************\nok: [127.0.0.1]\n\nTASK [Print message] ***********************************************************\nok: [127.0.0.1] => {\n    \"msg\": \"Hello world!\"\n}\n\nPLAY RECAP *********************************************************************\n127.0.0.1                  : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   \n\n",
                "stderr": "[WARNING]: No inventory was parsed, only implicit localhost is available\n[WARNING]: provided hosts list is empty, only localhost is available. Note that\nthe implicit localhost does not match 'all'\n",
                "start_time": "2025-05-26T22:18:41.905955Z",
                "end_time": "2025-05-26T22:18:45.034007Z",
                "elapsed_time": 3.1280594
            }
        }
    }