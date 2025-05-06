class ServiceCgiExceptions(Exception):
    """service.cgi 에서 발생하는 오류를 구조화함."""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

    def __str__(self):
        if self.code:
            return f"[Error {self.code}] {super().__str__()}"
        return super().__str__()