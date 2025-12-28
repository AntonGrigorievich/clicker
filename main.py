from pathlib import Path
import pyautogui
import time
import random

pyautogui.PAUSE = 0.25
pyautogui.FAILSAFE = True


class DogiatorsAutoClicker:
    def __init__(self):
        self.battle_count = 0
        self.screen_width, self.screen_height = pyautogui.size()
        self.click_delay = random.uniform(0.1, 0.3)
        self.repair_counter = 0
        self.next_repair = random.randint(10, 15)
        self.current_repair_index = 0
        self.cur_skill = 0

    def random_move(self):
        """Случайное движение мыши"""
        x = random.randint(100, self.screen_width - 100)
        y = random.randint(100, self.screen_height - 100)
        pyautogui.moveTo(x, y, duration=random.uniform(0.1, 0.2))

    def smart_click(self, x, y, click_delay=None):
        """Умный клик со случайными отклонениями и задержками"""
        if click_delay is None:
            click_delay = self.click_delay

        offset_x_activate = random.randint(-5, 5)
        offset_y_activate = random.randint(-5, 5)

        pyautogui.moveTo(x + offset_x_activate, y + offset_y_activate, duration=random.uniform(0.05, 0.1))

        pyautogui.mouseDown()

        move_distance = random.randint(100, 200)
        pyautogui.moveRel(move_distance, 0, duration=random.uniform(0.1, 0.2))
        pyautogui.mouseUp()

        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)

        pyautogui.moveTo(x + offset_x, y + offset_y, duration=random.uniform(0.05, 0.1))

        time.sleep(click_delay)
        pyautogui.click()

        self.random_move()

    def find_and_click_image(self, image_path, confidence=0.7, timeout=0.3):
        """Поиск и клик по изображению на экране"""

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                center_x, center_y = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)

                if center_x is not None and center_y is not None:
                    self.smart_click(center_x, center_y)
                    return True
            except pyautogui.ImageNotFoundException:
                pass
        return False

    def check_repair_needed(self):
        """Проверка необходимости починки"""
        if (self.repair_counter >= self.next_repair and
                self.find_and_click_image("images/inventory_button.png", timeout=2)):
            self.repair_counter = 0
            self.next_repair = random.randint(10, 15)
            return True
        return False

    def repair_equipment(self):
        """Починка оборудования"""
        print("Починка оборудования...")

        if self.find_and_click_image("images/repair_button.png", timeout=2):
            self.find_and_click_image("images/confirm_repair.png")

        self.find_and_click_image("images/home_button.png")

    def start_battle(self):
        print("Поиск кнопки fight")
        for count_scroll in range(10):
            try:
                try:
                    locks = list(pyautogui.locateAllOnScreen("images/lock.png", confidence=0.98))
                except Exception:
                    locks = []

                try:    
                    buttons = list(pyautogui.locateAllOnScreen("images/start_battle.png", confidence=0.88))
                except Exception:
                    buttons = []

                if len(buttons) > 0:
                    x, y = pyautogui.center(buttons[-1])
                    if len(buttons) == 1 or count_scroll == 9 or len(locks) > 0:
                        self.smart_click(x, y, click_delay=self.click_delay)
                        break

                    pyautogui.moveTo(int(x), int(y - 35), duration=0.1)
                    pyautogui.mouseDown()
                    pyautogui.moveTo(int(x), int(y - 190), duration=0.1)
                    pyautogui.mouseUp()
                elif len(buttons) == 0:
                    break
            except Exception as e: 
                print(e)
                break


    def dungeon_algorithm(self):
        """Алгоритм для подземелья"""
        print("Запуск алгоритма для подземелья...")

        while True:
            try:
                if self.find_and_click_image("images/no_energy.png"):
                    print("Не осталось энергии, остановка алгоритма подземелья...")
                    print(f"Сыграно боев: {self.battle_count}")
                    break

                self.use_additional()

                print("Поиск кнопки подземелья")
                self.find_and_click_image("images/dungeon_button.png", timeout=2)

                self.start_battle()

                print("Поиск кнопки авто режима")
                self.find_and_click_image("images/auto_button.png")

                self.check_for_battle_end()

                print("Поиск кнопки забора награды")
                self.find_and_click_image("images/collect_reward.png")

                print("Поиск кнопки получения нового уровня")
                self.find_and_click_image("images/new_level.png")

                self.open_chest()

                self.find_and_click_image("images/home_button.png")
                if self.check_repair_needed():
                    print("Необходима починка")
                    self.repair_equipment()

                self.use_skills()

            except KeyboardInterrupt:
                print("Остановка алгоритма подземелья...")
                print(f"Сыграно боев: {self.battle_count}")
                break
            except Exception as e:
                print(f"Ошибка в алгоритме подземелья: {e}")
                continue

    def arena_3v3_algorithm(self):
        """Алгоритм для арены 3 на 3"""
        print("Запуск алгоритма для арены 3 на 3...")

        while True:
            try:
                if self.find_and_click_image("images/no_energy.png"):
                    print("Не осталось энергии, остановка алгоритма подземелья...")
                    print(f"Сыграно боев: {self.battle_count}")
                    break

                self.use_additional()

                self.find_and_click_image("images/arena_button.png")

                if self.find_and_click_image("images/3v3_mode.png"):
                    if not self.find_and_click_image("images/start_arena_battle.png", timeout=1):
                        self.find_and_click_image("images/return_from_arena.png")

                self.find_and_click_image("images/auto_button.png")

                self.check_for_battle_end()

                print("Поиск кнопки забора награды")
                self.find_and_click_image("images/collect_reward.png")

                print("Поиск кнопки получения нового уровня")
                self.find_and_click_image("images/new_level.png")

                self.open_chest()

                self.find_and_click_image("images/home_button.png")
                if self.check_repair_needed():
                    print("Необходима починка")
                    self.repair_equipment()

                self.use_skills()

            except KeyboardInterrupt:
                print("Остановка алгоритма арены...")
                print(f"Сыграно боев: {self.battle_count}")
                break
            except Exception as e:
                print(f"Ошибка в алгоритме арены: {e}")

    def arena_1v1_algorithm(self):
        """Алгоритм для арены 1 на 1"""
        print("Запуск алгоритма для арены 1 на 1...")

        while True:
            try:
                if self.find_and_click_image("images/no_energy.png"):
                    print("Не осталось энергии, остановка алгоритма подземелья...")
                    print(f"Сыграно боев: {self.battle_count}")
                    break

                self.use_additional()

                self.find_and_click_image("images/arena_button.png")

                self.find_and_click_image("images/start_arena_battle.png")

                self.find_and_click_image("images/auto_button.png")

                self.check_for_battle_end()

                print("Поиск кнопки забора награды")
                self.find_and_click_image("images/collect_reward.png")

                print("Поиск кнопки получения нового уровня")
                self.find_and_click_image("images/new_level.png")

                self.open_chest()

                self.find_and_click_image("images/home_button.png")
                if self.check_repair_needed():
                    print("Необходима починка")
                    self.repair_equipment()

                self.use_skills()

            except KeyboardInterrupt:
                print("Остановка алгоритма арены...")
                print(f"Сыграно боев: {self.battle_count}")
                break
            except Exception as e:
                print(f"Ошибка в алгоритме арены: {e}")

    def use_skills(self):
        """Использование навыков во время боя"""
        skills_dir = Path("images/skills")
        skill_images = list(skills_dir.glob("*.png"))
        skill_img = skill_images[self.cur_skill % len(skill_images)]
        self.cur_skill += 1
        print(f"Поиск навыка №{self.cur_skill % len(skill_images) + 1}")

        start_time = time.time()
        while time.time() - start_time < 0.3:
            try:
                center_x, center_y = pyautogui.locateCenterOnScreen(str(skill_img), confidence=0.95)

                if center_x is not None and center_y is not None:
                    print(f"Навык найден")
                    pyautogui.doubleClick(center_x, center_y)
            except pyautogui.ImageNotFoundException:
                pass

    def use_additional(self):
        """Использование доп. функций во время боя"""
        skills_dir = Path("images/additional")
        skill_images = list(skills_dir.glob("*.png"))

        for i in range(len(skill_images)):
            print(f"Поиск дополнительной кнопки №{i + 1}")
            start_time = time.time()
            while time.time() - start_time < 0.3:
                try:
                    center_x, center_y = pyautogui.locateCenterOnScreen(str(skill_images[i]), confidence=0.95)

                    if center_x is not None and center_y is not None:
                        pyautogui.doubleClick(center_x, center_y)
                except pyautogui.ImageNotFoundException:
                    pass

    def check_for_battle_end(self):
        """Проверка на окончания боя"""
        print("Проверка на окончания боя...")

        if self.find_and_click_image("images/continue_after_battle.png"):
            self.repair_counter += 1
            self.battle_count += 1
            print(f"Бой №{self.battle_count} завершён")
            return True
        return False

    def open_chest(self):
        """Открытие сундука"""
        print("Открытие сундука...")
        self.find_and_click_image("images/open_chest.png")


def main():
    clicker = DogiatorsAutoClicker()

    print("Автокликер для Догиаторс")
    print("1 - Алгоритм для подземелья")
    print("2 - Алгоритм для арены 3 на 3")
    print("3 - Алгоритм для арены 1 на 1")
    print("0 - Выход")

    while True:
        choice = input("\nВыберите режим: ")

        if choice == "1":
            clicker.dungeon_algorithm()
        elif choice == "2":
            clicker.arena_3v3_algorithm()
        elif choice == "3":
            clicker.arena_1v1_algorithm()
        elif choice == "0":
            print("Выход...")
            break
        else:
            print("Неверный выбор")


if __name__ == "__main__":
    main()