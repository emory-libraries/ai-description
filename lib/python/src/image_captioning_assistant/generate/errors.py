# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Custom error classes."""


class LLMResponseParsingError(Exception):
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        return f"LLMResponseParsingError: {self.message} (Error Code: {self.error_code})"


class DocumentLengthError(Exception):
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        return f"DocumentLengthError: {self.message} (Error Code: {self.error_code})"
