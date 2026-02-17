"""
Claude API client wrapper (Ticket 1.4.1).

Handles API communication, error handling, timeouts, and rate limiting.
"""

import time
from typing import Any

import anthropic
from anthropic import APIError, APITimeoutError, RateLimitError

from clarity.config import ConfigManager


class ClaudeAPIClient:
    """
    Wrapper around Anthropic SDK for transcript analysis.

    Handles:
    - API key validation
    - Error handling (API errors, timeouts, rate limits)
    - Retry logic with exponential backoff
    - Structured JSON responses
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (fetches from config if None)
            timeout: Request timeout in seconds (default: 30s)
            max_retries: Maximum retry attempts for rate limits (default: 3)

        Raises:
            ValueError: If API key is missing
        """
        # Get API key from config if not provided
        if api_key is None:
            config = ConfigManager()
            api_key = config.get_api_key()

        if not api_key:
            raise ValueError(
                "Anthropic API key is required.\n\n"
                "Set it via:\n"
                "  1. Environment variable: export ANTHROPIC_API_KEY='your-key'\n"
                "  2. Config file: clarity config set-api-key YOUR_KEY\n\n"
                "Get your API key at: https://console.anthropic.com/"
            )

        self.client = anthropic.Anthropic(
            api_key=api_key,
            timeout=timeout,
        )
        self.timeout = timeout
        self.max_retries = max_retries

    def analyze_transcript(
        self,
        prompt: str,
        transcript: str,
        temperature: float = 0.0,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        """
        Send transcript to Claude for analysis.

        Args:
            prompt: System prompt with rubric and instructions
            transcript: Transcript text to analyze
            temperature: Sampling temperature (0.0 for deterministic)
            max_tokens: Maximum response tokens

        Returns:
            Parsed JSON response from Claude

        Raises:
            APIError: If API call fails after retries
            ValueError: If response is not valid JSON
        """
        messages = [
            {
                "role": "user",
                "content": f"{prompt}\n\n<transcript>\n{transcript}\n</transcript>",
            }
        ]

        # Retry loop for rate limits
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",  # Latest Sonnet
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                )

                # Extract text from response
                response_text = response.content[0].text

                # Parse JSON
                import json

                try:
                    return json.loads(response_text)
                except json.JSONDecodeError as e:
                    # Try to extract JSON from response if wrapped in markdown
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                        return json.loads(json_text)
                    else:
                        raise ValueError(
                            f"Failed to parse Claude response as JSON: {e}\n\n"
                            f"Response: {response_text[:500]}..."
                        ) from e

            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    wait_time = 2 ** (attempt + 1)
                    print(
                        f"Rate limit hit. Retrying in {wait_time}s... "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    raise APIError(
                        f"Rate limit exceeded after {self.max_retries} retries.\n"
                        "Please wait a few moments and try again."
                    ) from e

            except APITimeoutError as e:
                raise APIError(
                    f"Claude API request timed out after {self.timeout}s.\n"
                    "Try again with a shorter transcript or check your connection."
                ) from e

            except APIError as e:
                # Re-raise other API errors with helpful message
                raise APIError(
                    f"Claude API error: {str(e)}\n\n"
                    "Check your API key and network connection.\n"
                    "Status: https://status.anthropic.com/"
                ) from e

        # Should not reach here, but for type safety
        raise APIError("Max retries exceeded")

    def test_connection(self) -> bool:
        """
        Test API connection with a simple request.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}],
            )
            return response.content[0].text is not None
        except Exception:
            return False
