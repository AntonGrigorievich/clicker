from pathlib import Path
import pyautogui
import time
import random

from db import init_db, drop_table
from logger import logger
from profiles import select_profile, create_profile, display_profile, edit_profile
from algorithms import create_algorithm, select_algorithm, run_algorithm, edit_algorithm, display_algorithm
from stats import save_battle_stat

pyautogui.PAUSE = 0.25
pyautogui.FAILSAFE = True
current_profile = None
current_algorithm = None


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
        logger.info("Починка оборудования...")

        if self.find_and_click_image("images/repair_button.png", timeout=2):
            self.find_and_click_image("images/confirm_repair.png")

        self.find_and_click_image("images/home_button.png")

    def start_battle(self):
        logger.debug("Поиск кнопки fight")
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
                logger.error(e)
                break


    def dungeon_algorithm(self):
        """Алгоритм для подземелья"""
        logger.debug("Запуск алгоритма для подземелья...")

        while True:
            try:
                if self.find_and_click_image("images/no_energy.png"):
                    logger.info("Не осталось энергии, остановка алгоритма подземелья...")
                    logger.info(f"Сыграно боев: {self.battle_count}")
                    return 0

                self.use_additional()

                logger.debug("Поиск кнопки подземелья")
                self.find_and_click_image("images/dungeon_button.png", timeout=2)

                self.start_battle()

                logger.debug("Поиск кнопки авто режима")
                self.find_and_click_image("images/auto_button.png")

                battle_res = self.check_for_battle_end()
                if battle_res:
                    logger.debug("Остановка алгоритма подземелья")
                    save_battle_stat(current_profile[0], current_algorithm[0], "dungeon", battle_res)
                    return 1

                logger.debug("Поиск кнопки забора награды")
                self.find_and_click_image("images/collect_reward.png")

                logger.debug("Поиск кнопки получения нового уровня")
                self.find_and_click_image("images/new_level.png")

                self.open_chest()

                self.find_and_click_image("images/home_button.png")
                if self.check_repair_needed():
                    logger.debug("Необходима починка")
                    self.repair_equipment()

                self.use_skills()

            except KeyboardInterrupt:
                logger.info("Остановка алгоритма подземелья...")
                logger.info(f"Сыграно боев: {self.battle_count}")
                return 0
            except Exception as e:
                logger.error(f"Ошибка в алгоритме подземелья: {e}")
                continue

    def arena_3v3_algorithm(self):
        """Алгоритм для арены 3 на 3"""
        logger.info("Запуск алгоритма для арены 3 на 3...")

        while True:
            try:
                if self.find_and_click_image("images/no_energy.png"):
                    logger.info("Не осталось энергии, остановка алгоритма подземелья...")
                    logger.info(f"Сыграно боев: {self.battle_count}")
                    return 0

                self.use_additional()

                self.find_and_click_image("images/arena_button.png")

                if self.find_and_click_image("images/3v3_mode.png"):
                    if not self.find_and_click_image("images/start_arena_battle.png", timeout=1):
                        self.find_and_click_image("images/return_from_arena.png")

                self.find_and_click_image("images/auto_button.png")

                battle_res = self.check_for_battle_end()
                if battle_res:
                    logger.debug("Остановка алгоритма подземелья")
                    save_battle_stat(current_profile[0], current_algorithm[0], "dungeon", battle_res)
                    return 1

                logger.debug("Поиск кнопки забора награды")
                self.find_and_click_image("images/collect_reward.png")

                logger.debug("Поиск кнопки получения нового уровня")
                self.find_and_click_image("images/new_level.png")

                self.open_chest()

                self.find_and_click_image("images/home_button.png")
                if self.check_repair_needed():
                    logger.debug("Необходима починка")
                    self.repair_equipment()

                self.use_skills()

            except KeyboardInterrupt:
                logger.info("Остановка алгоритма арены...")
                logger.info(f"Сыграно боев: {self.battle_count}")
                return 0
            except Exception as e:
                logger.error(f"Ошибка в алгоритме арены: {e}")
    def arena_1v1_algorithm(self):
        """Алгоритм для арены 1 на 1"""
        logger.info("Запуск алгоритма для арены 1 на 1...")

        while True:
            try:
                if self.find_and_click_image("images/no_energy.png"):
                    logger.info("Не осталось энергии, остановка алгоритма подземелья...")
                    logger.info(f"Сыграно боев: {self.battle_count}")
                    return 0

                self.use_additional()

                self.find_and_click_image("images/arena_button.png")

                self.find_and_click_image("images/start_arena_battle.png")

                self.find_and_click_image("images/auto_button.png")

                battle_res = self.check_for_battle_end()
                if battle_res:
                    logger.debug("Остановка алгоритма подземелья")
                    save_battle_stat(current_profile[0], current_algorithm[0], "dungeon", battle_res)
                    return 1

                logger.debug("Поиск кнопки забора награды")
                self.find_and_click_image("images/collect_reward.png")

                logger.debug("Поиск кнопки получения нового уровня")
                self.find_and_click_image("images/new_level.png")

                self.open_chest()

                self.find_and_click_image("images/home_button.png")
                if self.check_repair_needed():
                    logger.debug("Необходима починка")
                    self.repair_equipment()

                self.use_skills()

            except KeyboardInterrupt:
                logger.info("Остановка алгоритма арены...")
                logger.info(f"Сыграно боев: {self.battle_count}")
                return 0
            except Exception as e:
                logger.error(f"Ошибка в алгоритме арены: {e}")

    def run_battle(self, battle_type):
        if battle_type == "3x3":
            return self.arena_3v3_algorithm()
        elif battle_type == "1x1":
            return self.arena_1v1_algorithm()
        elif battle_type == "dungeon":
            return self.dungeon_algorithm()

        logger.error(f"Неизвестный тип боя: {battle_type}")
        

    def use_skills(self):
        """Использование навыков во время боя"""
        skills_dir = Path("images/skills")
        skill_images = list(skills_dir.glob("*.png"))

        if not skill_images:
            logger.warning("Не указаны изображения навыков.")
            return

        skill_img = skill_images[self.cur_skill % len(skill_images)]
        self.cur_skill += 1
        logger.debug(f"Поиск навыка №{self.cur_skill % len(skill_images) + 1}")

        start_time = time.time()
        while time.time() - start_time < 0.3:
            try:
                center_x, center_y = pyautogui.locateCenterOnScreen(str(skill_img), confidence=0.95)

                if center_x is not None and center_y is not None:
                    logger.debug(f"Навык найден")
                    pyautogui.doubleClick(center_x, center_y)
            except pyautogui.ImageNotFoundException:
                pass

    def use_additional(self):
        """Использование доп. функций во время боя"""
        skills_dir = Path("images/additional")
        skill_images = list(skills_dir.glob("*.png"))

        for i in range(len(skill_images)):
            logger.debug(f"Поиск дополнительной кнопки №{i + 1}")
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
        logger.debug("Проверка на окончания боя...")

        if self.find_and_click_image("images/continue_after_battle.png"):
            # Нет определения итога боя
            self.repair_counter += 1
            self.battle_count += 1
            logger.info(f"Бой №{self.battle_count} завершён")
            return True
        return False

    def open_chest(self):
        """Открытие сундука"""
        logger.debug("Открытие сундука...")
        self.find_and_click_image("images/open_chest.png")


def main():
    clicker = DogiatorsAutoClicker()


    while True:
        print("~~~~~~~~~~~~МЕНЮ~~~~~~~~~~~~")
        print("1 - Алгоритм для подземелья")
        print("2 - Алгоритм для арены 3 на 3")
        print("3 - Алгоритм для арены 1 на 1")
        print("4 - Выбрать профиль")
        print("5 - Редактировать профили")
        print("6 - Создать профиль")
        print("7 - Создать алгоритм")
        print("8 - Запустить алгоритм")
        print("9 - Редактировать алгоритмы")
        print("0 - Выход")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        choice = input("\n> ")

        if choice == "1":
            keep_playing = True
            while keep_playing:
                keep_playing = clicker.run_battle("dungeon")
        elif choice == "2":
            keep_playing = True
            while keep_playing:
                keep_playing = clicker.run_battle("3x3")
        elif choice == "3":
            keep_playing = True
            while keep_playing:
                keep_playing = clicker.run_battle("1x1")
        elif choice == "4":
            current_profile = select_profile()
            if current_profile:
                print("Выбран профиль:")
                display_profile(current_profile[0])        
                clicker.next_repair = random.randint(current_profile[3], current_profile[4])
                logger.debug(f"Починка через {clicker.next_repair} боев")
            else:
                print("Профили отсутствуют. Создайте новый профиль.")
        elif choice == "5":
            profile = select_profile()
            if profile:
                edit_profile(profile[0])
        elif choice == "6":
            create_profile()
        elif choice == "7":
            create_algorithm()
        elif choice == "8":
            current_algorithm = select_algorithm()
            if current_algorithm:
                print(f"Запуск алгоритма: {current_algorithm[1]}")
                run_algorithm(clicker, current_algorithm[0])
            else:
                print("Алгоритмы отсутствуют. Создайте новый алгоритм.")
        elif choice == "9":
            algorithm = select_algorithm()
            if algorithm:
                print("Редактирование алгоритма:")
                display_algorithm(algorithm[0])
                edit_algorithm(algorithm[0])
        elif choice == "0":
            print("Выход...")
            break
        else:
            print("Неверный выбор")


if __name__ == "__main__":
    init_db()
    main()