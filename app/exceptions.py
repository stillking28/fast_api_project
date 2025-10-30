class UserNotFoundError(Exception):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"Пользователь с ID {user_id} не был найден.")


class UserAlreadyExistsError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)
