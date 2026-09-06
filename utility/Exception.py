import sys
from typing import Optional


class DeepFakeDetectionException(Exception):
    def __init__(
        self,
        message: str,
        error: Optional[Exception] = None,
        error_code: str = "DEEP_FAKE_DETECTION",
    ):
        self.message = message
        self.error = error
        self.error_code = error_code

        _, _, exc_tb = sys.exc_info()

        if exc_tb:
            self.file_name = exc_tb.tb_frame.f_code.co_filename
            self.line_number = exc_tb.tb_lineno
        else:
            self.file_name = None
            self.line_number = None

        super().__init__(self.message)

    def __str__(self) -> str:
        return (
            f"\nError Code : {self.error_code}\n"
            f"Message    : {self.message}\n"
            f"File       : {self.file_name}\n"
            f"Line       : {self.line_number}\n"
            f"Original   : {self.error}\n"
        )