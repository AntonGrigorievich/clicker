from pathlib import Path
import pyautogui
import time
import random
import dotenv

from db import init_db, drop_table
from logger import logger
from profiles import select_profile, create_profile, display_profile, edit_profile
from algorithms import create_algorithm, select_algorithm, run_algorithm, edit_algorithm, display_algorithm
from stats import *
from utils import UI

pyautogui.PAUSE = 0.25
pyautogui.FAILSAFE = True

DEBUG = dotenv.get_key(dotenv.find_dotenv(), "DEBUG") in ["True", 1, "1", True]

class DogiatorsAutoClicker:
    def __init__(self):
        self.battle_count = 0
        self.screen_width, self.screen_height = pyautogui.size()
        self.click_delay = random.uniform(0.1, 0.3)
        self.repair_counter = 0
        self.next_repair = random.randint(10, 15)
        self.current_repair_index = 0
        self.cur_skill = 0
        self.current_profile = None
        self.current_algorithm = None
        self.battle_boosts = False
        self.no_energy_mode = False
        self._missing_images = set()

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

        pyautogui.moveTo(x + offset_x_activate, y + offset_y_activate, duration=random.uniform(0.05, 0.1)) # mac // 2

        pyautogui.mouseDown()

        move_distance = random.randint(100, 200)
        pyautogui.moveRel(move_distance, 0, duration=random.uniform(0.1, 0.2))
        pyautogui.mouseUp()

        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)

        pyautogui.moveTo(x + offset_x, y + offset_y, duration=random.uniform(0.05, 0.1)) # mac // 2

        time.sleep(click_delay)
        pyautogui.click()

        self.random_move()

    def find_and_click_image(self, image_path, confidence=0.7, timeout=0.3):
        """Поиск и клик по изображению на экране"""
        if not Path(image_path).is_file():
            if image_path not in self._missing_images:
                self._missing_images.add(image_path)
                logger.warning(f"Изображение {image_path} не найдено.")
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                center_x, center_y = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)

                if center_x is not None and center_y is not None:
                    self.smart_click(center_x, center_y)
                    return True
            except pyautogui.ImageNotFoundException:
                pass
            except Exception as e:
                if image_path not in self._missing_images:
                    self._missing_images.add(image_path)
                    logger.warning(
                        f"Изображение {image_path} не найдено: {e}"
                    )
                return False
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
        # info: Функционал scroll вырезан, сайчас подземелья автоматически листается вниз
        logger.debug("Поиск кнопки fight")
        # for count_scroll in range(10):
        try:
            # try:
            #     locks = list(pyautogui.locateAllOnScreen("images/lock.png", confidence=0.98))
            # except Exception:
            #     locks = []

            try:    
                buttons = list(pyautogui.locateAllOnScreen("images/start_battle.png", confidence=0.88))
            except Exception:
                buttons = []

            if len(buttons) > 0:
                x, y = pyautogui.center(buttons[-1])
                self.smart_click(x, y, click_delay=self.click_delay)

                # if len(buttons) == 1 or count_scroll == 9 or len(locks) > 0:
                #     self.smart_click(x, y, click_delay=self.click_delay)
                #     break

                # pyautogui.moveTo(int(x) // 2, int(y - 35) // 2, duration=0.1) # mac // 2
                # pyautogui.mouseDown()
                # pyautogui.moveTo(int(x) // 2, int(y - 190) // 2, duration=0.1) # mac // 2
                # pyautogui.mouseUp()
            elif len(buttons) == 0:
                return
        except Exception as e: 
            logger.error(e)
            return


    def dungeon_algorithm(self):
        """Алгоритм для подземелья"""
        logger.debug("Запуск алгоритма для подземелья...")

        while True:
            try:
                if not self.no_energy_mode:
                    if self.find_and_click_image("images/no_energy.png"):
                        logger.info("Не осталось энергии, остановка алгоритма подземелья...")
                        logger.info(f"Сыграно боев: {self.battle_count}")
                        return 0
                else:
                    self.find_and_click_image("images/no_energy_continue.png")

                self.use_additional()

                if self.battle_boosts:
                    self.use_battle_boosts()

                logger.debug("Поиск кнопки подземелья")
                self.find_and_click_image("images/dungeon_button.png", timeout=2)

                self.start_battle()

                logger.debug("Поиск кнопки авто режима")
                self.find_and_click_image("images/auto_button.png")

                battle_res = self.check_for_battle_end()
                if battle_res != -1:
                    logger.debug("Остановка алгоритма подземелья")
                    if self.current_profile is not None and self.current_algorithm is not None:
                        save_battle_stat(
                            self.current_profile[0],
                            self.current_algorithm[0],
                            "dungeon",
                            battle_res
                        )
                        logger.debug("Итог боя сохранен")
                    else:
                        logger.warning("Профиль или алгоритм не выбраны. Статистика боя сохранена без привязки к профилю и алгоритму.")
                        save_battle_stat(
                            self.current_profile[0] if self.current_profile is not None else None,
                            self.current_algorithm[0] if self.current_algorithm is not None else None,
                            "dungeon",
                            battle_res,
                        )
                        logger.debug("Итог боя сохранен без привязки")
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
                if not self.no_energy_mode:
                    if self.find_and_click_image("images/no_energy.png"):
                        logger.info("Не осталось энергии, остановка алгоритма подземелья...")
                        logger.info(f"Сыграно боев: {self.battle_count}")
                        return 0
                else:
                    self.find_and_click_image("images/no_energy_continue.png")

                self.use_additional()

                if self.battle_boosts:
                    self.use_battle_boosts()

                self.find_and_click_image("images/arena_button.png")

                if self.find_and_click_image("images/3v3_mode.png"):
                    if not self.find_and_click_image("images/start_arena_battle.png", timeout=1):
                        self.find_and_click_image("images/return_from_arena.png")

                self.find_and_click_image("images/auto_button.png")

                battle_res = self.check_for_battle_end()
                if battle_res != -1:
                    logger.debug("Остановка алгоритма 3 на 3")
                    if self.current_profile is not None and self.current_algorithm is not None:
                        save_battle_stat(self.current_profile[0], self.current_algorithm[0], "3 на 3", battle_res)
                        logger.debug("Итог боя сохранен")
                    else:
                        logger.warning("Профиль или алгоритм не выбраны. Статистика боя сохранена без привязки к профилю и алгоритму.")
                        save_battle_stat(
                            self.current_profile[0] if self.current_profile is not None else None,
                            self.current_algorithm[0] if self.current_algorithm is not None else None,
                            "3 на 3",
                            battle_res,
                        )
                        logger.debug("Итог боя сохранен без привязки")
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
                logger.error(f"Ошибка в алгоритме арены 3 на 3: {e}")
    def arena_1v1_algorithm(self):
        """Алгоритм для арены 1 на 1"""
        logger.info("Запуск алгоритма для арены 1 на 1...")

        while True:
            try:
                if not self.no_energy_mode:
                    if self.find_and_click_image("images/no_energy.png"):
                        logger.info("Не осталось энергии, остановка алгоритма подземелья...")
                        logger.info(f"Сыграно боев: {self.battle_count}")
                        return 0
                else:
                    self.find_and_click_image("images/no_energy_continue.png")

                if self.battle_boosts:
                    self.use_battle_boosts()

                self.use_additional()

                self.find_and_click_image("images/arena_button.png")

                self.find_and_click_image("images/start_arena_battle.png")

                self.find_and_click_image("images/auto_button.png")

                battle_res = self.check_for_battle_end()
                if battle_res != -1:
                    logger.debug("Остановка алгоритма 1 на 1")
                    if self.current_profile is not None and self.current_algorithm is not None:
                        save_battle_stat(self.current_profile[0], self.current_algorithm[0], "1 на 1", battle_res)
                        logger.debug("Итог боя сохранен")
                    else:
                        logger.warning("Профиль или алгоритм не выбраны. Статистика боя сохранена без привязки к профилю и алгоритму.")
                        save_battle_stat(
                            self.current_profile[0] if self.current_profile is not None else None,
                            self.current_algorithm[0] if self.current_algorithm is not None else None,
                            "1 на 1",
                            battle_res,
                        )
                        logger.debug("Итог боя сохранен без привязки")
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
                logger.error(f"Ошибка в алгоритме арены 1 на 1: {e}")

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
                    pyautogui.doubleClick(center_x, center_y) # mac // 2
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
                        pyautogui.doubleClick(center_x, center_y) # mac // 2 
                except pyautogui.ImageNotFoundException:
                    pass

    def use_battle_boosts(self):
        """Использование боевых усилителей во время боя"""
        skills_dir = Path("images/boosts")
        skill_images = list(skills_dir.glob("*.png"))

        for i in range(len(skill_images)):
            logger.debug(f"Поиск боевого усилителя №{i + 1}")
            start_time = time.time()
            while time.time() - start_time < 0.3:
                try:
                    center_x, center_y = pyautogui.locateCenterOnScreen(str(skill_images[i]), confidence=0.95)

                    if center_x is not None and center_y is not None:
                        pyautogui.doubleClick(center_x, center_y) # mac // 2
                except pyautogui.ImageNotFoundException:
                    pass

    def check_for_battle_end(self):
        """Проверка окончания боя
        -1 — бой продолжается
        1 — победа
        0 — поражение
        """
        logger.debug("Проверка на окончания боя...")
        res = -1
        try:
            center = pyautogui.locateCenterOnScreen("images/victory.png", confidence=0.95)
            if center:
                res = 1
        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            if DEBUG:
                print(e)

        if res == -1 :
            try:
                center = pyautogui.locateCenterOnScreen("images/defeat.png", confidence=0.95)
                if center:
                    res = 0
            except pyautogui.ImageNotFoundException:
                pass
            except Exception as e:
                if DEBUG:
                    print(e)

        if res != -1 and self.find_and_click_image("images/continue_after_battle.png"):
            self.repair_counter += 1
            self.battle_count += 1
            logger.info(f"Бой №{self.battle_count} завершён: {'победа' if res else 'поражение'}")
        return res

    def open_chest(self):
        """Открытие сундука"""
        logger.debug("Открытие сундука...")
        self.find_and_click_image("images/open_chest.png")

    def prebattle_warnings(self):
        warnings = []

        if self.current_profile is None:
            warnings.append("игра без профиля")

        skills = list(Path("images/skills").glob("*.png"))
        if not skills:
            warnings.append("не заданы навыки")

        boosts = list(Path("images/boosts").glob("*.png"))
        if not boosts:
            warnings.append("не заданы боевые усилители")

        if warnings:
            logger.warning(
                "Внимание: " + ", ".join(warnings) + "."
            )


def select_date_range():
    UI.info("\nВыберите период статистики:")
    UI.info("1 - за всё время")
    UI.info("2 - сегодня")
    UI.info("3 - последние 7 дней")
    UI.info("4 - свой диапазон")
    choice = input("> ").strip()

    if choice == "1":
        return None, None

    if choice == "2":
        return (
            "date('now','start of day')",
            None
        )

    if choice == "3":
        return (
            "date('now','-7 day')",
            None
        )

    if choice == "4":
        UI.info("Формат даты: YYYY-MM-DD")
        date_from = input("Дата ОТ: ").strip()
        date_to = input("Дата ДО: ").strip()

        if not date_from:
            date_from = None
        if not date_to:
            date_to = None

        return date_from, date_to

    UI.warning("Неверный выбор, показана статистика за всё время")
    return None, None


def main():
    clicker = DogiatorsAutoClicker()


    while True:
        UI.info("~~~~~~~~~~~~МЕНЮ~~~~~~~~~~~~")
        UI.info("1 - Алгоритм для подземелья")
        UI.info("2 - Алгоритм для арены 3 на 3")
        UI.info("3 - Алгоритм для арены 1 на 1")
        UI.success("4 - Выбрать профиль")
        UI.success("5 - Редактировать профили")
        UI.success("6 - Создать профиль")
        UI.warning("7 - Создать алгоритм")
        UI.warning("8 - Запустить алгоритм")
        UI.warning("9 - Редактировать алгоритмы")
        UI.error("10 - Статистика")
        UI.error(f"11 - Переключить боевые усилители (сейчас {'вкл' if clicker.battle_boosts else 'выкл'})")
        UI.error(f"12 - Переключить режим игры без энергии (сейчас {'вкл' if clicker.no_energy_mode else 'выкл'})")
        UI.info("0 - Выход")
        UI.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        choice = input("\n> ")

        if choice == "1":
            clicker.prebattle_warnings()
            keep_playing = True
            while keep_playing:
                keep_playing = clicker.run_battle("dungeon")
        elif choice == "2":
            clicker.prebattle_warnings()
            keep_playing = True
            while keep_playing:
                keep_playing = clicker.run_battle("3x3")
        elif choice == "3":
            clicker.prebattle_warnings()
            keep_playing = True
            while keep_playing:
                keep_playing = clicker.run_battle("1x1")
        elif choice == "4":
            clicker.current_profile = select_profile()
            if clicker.current_profile:
                UI.info("Выбран профиль:")
                display_profile(clicker.current_profile[0])        
                clicker.next_repair = random.randint(clicker.current_profile[3], clicker.current_profile[4])
                logger.debug(f"Починка через {clicker.next_repair} боев")
            else:
                UI.warning("Профили отсутствуют. Создайте новый профиль.")
        elif choice == "5":
            profile = select_profile()
            if profile:
                edit_profile(profile[0])
        elif choice == "6":
            create_profile()
        elif choice == "7":
            create_algorithm()
        elif choice == "8":
            clicker.current_algorithm = select_algorithm()
            if clicker.current_algorithm:
                clicker.prebattle_warnings()
                UI.info(f"Запуск алгоритма: {clicker.current_algorithm[1]}")
                run_algorithm(clicker, clicker.current_algorithm[0])
                clicker.find_and_click_image("images/collect_reward.png")
            else:
                UI.warning("Алгоритмы отсутствуют. Создайте новый алгоритм.")
        elif choice == "9":
            algorithm = select_algorithm()
            if algorithm:
                UI.info("Редактирование алгоритма:")
                display_algorithm(algorithm[0])
                edit_algorithm(algorithm[0])
        elif choice == "10":
            date_from, date_to = select_date_range()

            UI.info("\n=== ОБЩАЯ СТАТИСТИКА ===")
            games, wins, losses, winrate = stats_overall(date_from, date_to)
            UI.info(f"Бои: {games}")
            UI.info(f"Победы: {wins} | Поражения: {losses}")
            UI.info(f"Винрейт: {winrate}%")
            UI.info("\n=== ПО ПРОФИЛЯМ ===")
            for profile, g, w, l, wr in stats_by_profiles(date_from, date_to):
                UI.info(f"{profile}: {wr}% ({w}/{g})")

            UI.info("\n=== ПО АЛГОРИТМАМ ===")
            for alg, g, w, l, wr in stats_by_algorithms(date_from, date_to):
                UI.info(f"{alg}: {wr}% ({w}/{g})")

            UI.info("\n=== ПРОФИЛЬ → АЛГОРИТМЫ ===")
            if clicker.current_profile is not None:
                UI.info(f"Профиль: {clicker.current_profile[1]}")
                rows = stats_profile_algorithms(clicker.current_profile[0], date_from, date_to)
            else:
                UI.info("Профиль: ANY")
                rows = stats_profile_algorithms(None, date_from, date_to)

            for alg, g, w, l, wr in rows:
                UI.info(f"{alg}: {wr}% ({w}/{g})")
            UI.info("\n=== ПО РЕЖИМАМ ===")
            for mode, g, w, l, wr in stats_by_battle_type(date_from, date_to):
                UI.info(f"{mode}: {wr}% ({w}/{g})\n")
        elif choice == "11":
            clicker.battle_boosts = not clicker.battle_boosts
        elif choice == "12":
            clicker.no_energy_mode = not clicker.no_energy_mode
        elif choice == "0":
            UI.info("Выход...")
            break
        else:
            UI.warning("Неверный выбор")
if __name__ == "__main__":
    init_db()
    main()