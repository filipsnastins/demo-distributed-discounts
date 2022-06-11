from typing import Optional


class AppError(Exception):
    def __init__(
        self,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        status_code: int = 400,
    ):
        super().__init__(self)
        self.error_code = error_code
        self.error_message = error_message
        self.status_code = status_code

    def __str__(self) -> Optional[str]:
        return self.error_message

    def to_dict(self) -> dict:
        return {"error_code": self.error_code, "error_message": self.error_message}
