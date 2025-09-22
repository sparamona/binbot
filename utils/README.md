# BinBot Utilities

## Centralized Logging

The `utils/logging.py` module provides a centralized logging utility for consistent logging across all BinBot modules.

### Usage

```python
from utils.logging import setup_logger

# Set up logger for your module
logger = setup_logger(__name__)

# Use the logger
logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")
```

### Features

- **Consistent formatting**: All logs use the same timestamp and format
- **Environment-based log levels**: Set `LOG_LEVEL` environment variable (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **No duplicate handlers**: Safe to call `setup_logger()` multiple times
- **Helper functions**: Utilities for logging function calls and results

### Log Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Something unexpected happened but the program continues
- `ERROR`: A serious problem occurred
- `CRITICAL`: A very serious error occurred

### Environment Configuration

Set the log level using environment variables:

```bash
# Development - see all logs
export LOG_LEVEL=DEBUG

# Production - only important messages
export LOG_LEVEL=WARNING

# Default if not set
LOG_LEVEL=INFO
```

### Current Bin Debugging

The logging system now tracks `current_bin` updates throughout the system:

- **Session Manager**: Logs when `current_bin` is set or changed
- **Function Wrappers**: Logs which functions update `current_bin`
- **Chat Endpoint**: Logs incoming requests and outgoing `current_bin` values

To debug current_bin issues:

1. Set `LOG_LEVEL=INFO` or `LOG_LEVEL=DEBUG`
2. Run the test script: `python test_logging_current_bin.py`
3. Watch the server logs for detailed current_bin tracking

### Helper Functions

```python
from utils.logging import log_function_call, log_function_result

# Log function calls with arguments
log_function_call(logger, "my_function", arg1, arg2, keyword=value)

# Log function results
log_function_result(logger, "my_function", result, success=True)
```
