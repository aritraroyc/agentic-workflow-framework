# LLM Request/Response Logging

The framework includes comprehensive logging for all LLM API calls to help with debugging, performance monitoring, and troubleshooting.

## Overview

When enabled, the LLM logging feature logs:
- **Model name and provider** - Which LLM was called
- **Message count** - Number of messages sent to the LLM
- **Execution time** - How long the API call took (in seconds)
- **Response length** - Size of the response (in characters)
- **Error details** - If the call failed, the error type is logged

## Enabling LLM Logging

Add or modify the following in your `.env` file:

```bash
# Enable detailed LLM logging (default: false)
LOG_LLM_REQUESTS=true
```

Or set it at runtime:

```bash
LOG_LLM_REQUESTS=true python main.py story.md
```

## Log Format

### Successful Call
```
[LLM_CALL_BEGIN] Provider=openai Model=gpt-4-turbo-preview Messages=2
[LLM_CALL_END] Provider=openai Model=gpt-4-turbo-preview Status=success ExecutionTime=2.34s ResponseLength=523chars
```

### Failed Call
```
[LLM_CALL_BEGIN] Provider=anthropic Model=claude-3-sonnet-20240229 Messages=3
[LLM_CALL_ERROR] Provider=anthropic Model=claude-3-sonnet-20240229 Status=failure ExecutionTime=5.12s Error=APIConnectionError
```

## Log Levels

- **BEGIN** logs appear at **INFO** level when a call starts
- **END** logs appear at **INFO** level when a call succeeds
- **ERROR** logs appear at **ERROR** level when a call fails

## Security

The logging feature automatically redacts sensitive data including:
- **API Keys** - `sk-*` patterns are replaced with `[REDACTED_API_KEY]`
- **Bearer Tokens** - Authorization tokens are replaced with `[REDACTED_TOKEN]`
- **Basic Auth** - Base64-encoded credentials are replaced with `[REDACTED_AUTH]`

This ensures that even with logging enabled, your credentials remain safe.

## Performance Impact

The logging feature has minimal performance impact:
- Logging is only executed if `LOG_LLM_REQUESTS=true`
- Execution time measurement uses `time.time()` (microsecond precision)
- No additional API calls or network overhead

## Examples

### Development with Logging
```bash
# Enable logging to see detailed LLM call information
LOG_LLM_REQUESTS=true python main.py examples/stories/api_development.md
```

Output:
```
2025-11-08 10:22:15,234 - core.llm - INFO - [LLM_CALL_BEGIN] Provider=openai Model=gpt-4-turbo-preview Messages=2
2025-11-08 10:22:17,456 - core.llm - INFO - [LLM_CALL_END] Provider=openai Model=gpt-4-turbo-preview Status=success ExecutionTime=2.22s ResponseLength=1250chars
2025-11-08 10:22:17,460 - core.llm - INFO - [LLM_CALL_BEGIN] Provider=openai Model=gpt-4-turbo-preview Messages=2
2025-11-08 10:22:19,890 - core.llm - INFO - [LLM_CALL_END] Provider=openai Model=gpt-4-turbo-preview Status=success ExecutionTime=2.43s ResponseLength=2100chars
```

### Production (Logging Disabled)
```bash
# Default: logging disabled for minimal overhead
python main.py examples/stories/api_development.md
```

## Debugging with Logs

### Identify Slow LLM Calls
Look for calls with `ExecutionTime` > 5s - these may indicate network issues or rate limiting.

### Monitor Response Sizes
Check `ResponseLength` to understand how much data is being generated. Very small responses may indicate quality issues.

### Track Error Patterns
The `[LLM_CALL_ERROR]` logs show which LLM calls are failing and why, helping identify problematic requests.

## Configuration Behavior

| `LOG_LLM_REQUESTS` | Behavior |
|---|---|
| `true` or `1` or `yes` | Logging **enabled** - Detailed logs for all LLM calls |
| `false` (default) or `0` or `no` | Logging **disabled** - Only error logs appear |
| Not set | Defaults to `false` - Logging disabled |

## Related Configuration

See also:
- **LOG_LEVEL** - Controls overall application logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **LLM_PROVIDER** - Which LLM provider to use (openai or anthropic)
- **OPENAI_MODEL** - OpenAI model selection
- **ANTHROPIC_MODEL** - Anthropic model selection

## Example Log Analysis

```
[LLM_CALL_BEGIN] Provider=openai Model=gpt-4-turbo-preview Messages=2
[LLM_CALL_END] Provider=openai Model=gpt-4-turbo-preview Status=success ExecutionTime=2.34s ResponseLength=1250chars
↑ Provider and model ↑ Execution time  ↑ Response size
```

This tells us:
- Using OpenAI with GPT-4 Turbo
- Called with 2 messages
- Completed successfully in 2.34 seconds
- Generated a 1250-character response

## Troubleshooting

**Q: Logs are empty even with `LOG_LLM_REQUESTS=true`**
- Ensure the environment variable is set correctly before running the application
- Check that logging level in `.env` is not set to ERROR or CRITICAL
- Verify that the LLM is actually being called (check for other log messages)

**Q: API keys appear in logs**
- This should not happen - the logging system redacts known patterns
- Please report this as a security issue if you find unredacted keys

**Q: Execution time seems wrong**
- Execution time includes network latency and server response time
- Consider rate limiting if times are consistently > 10s

## Testing

Unit tests for LLM logging are in `tests/unit/test_llm_logging.py`:
- Test logging toggle behavior
- Test sensitive data redaction
- Test log format
- Test provider detection
