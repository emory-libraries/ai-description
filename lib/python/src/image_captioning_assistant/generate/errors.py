# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Custom error classes."""


class LLMResponseParsingError(Exception):
    """LLM response parsing error."""

    def __init__(self, message: str, error_code: str | None = None):
        """Initialize error."""
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return error in string form."""
        return f"LLMResponseParsingError: {self.message} (Error Code: {self.error_code})"


class DocumentLengthError(Exception):
    """Document length error."""

    def __init__(self, message: str, error_code: str | None = None):
        """Initialize error."""
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return error in string form."""
        return f"DocumentLengthError: {self.message} (Error Code: {self.error_code})"
