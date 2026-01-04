def input_int(prompt, min_value=None, max_value=None):
    try:
        value = int(input(prompt))
    except ValueError:
        UI.warning("Ошибка: введите целое число")
        return None

    if min_value is not None and value < min_value:
        UI.warning(f"Значение должно быть >= {min_value}")
        return None

    if max_value is not None and value > max_value:
        UI.warning(f"Значение должно быть <= {max_value}")
        return None

    return value

def input_str(prompt, allow_empty=False):
    value = input(prompt).strip()
    if not value and not allow_empty:
        UI.warning("Значение не может быть пустым")
        return None
    return value

class UI:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

    @staticmethod
    def info(text=""):
        print(f"{UI.BLUE}{text}{UI.RESET}")

    @staticmethod
    def success(text=""):
        print(f"{UI.GREEN}{text}{UI.RESET}")

    @staticmethod
    def warning(text=""):
        print(f"{UI.YELLOW}{text}{UI.RESET}")

    @staticmethod
    def error(text=""):
        print(f"{UI.RED}{text}{UI.RESET}")

    @staticmethod
    def plain(text=""):
        print(text="")
