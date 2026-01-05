from colorama import Fore, Style, init

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

init(autoreset=True)

class UI:
    @staticmethod
    def info(text=""):
        print(Fore.BLUE + text + Style.RESET_ALL)

    @staticmethod
    def success(text=""):
        print(Fore.GREEN + text + Style.RESET_ALL)

    @staticmethod
    def warning(text=""):
        print(Fore.YELLOW + text + Style.RESET_ALL)

    @staticmethod
    def error(text=""):
        print(Fore.RED + text + Style.RESET_ALL)

    @staticmethod
    def plain(text=""):
        print(text="")
