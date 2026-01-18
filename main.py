import platform

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

from multiprocessing import Process, Event
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pyautogui
import time
import random
import dotenv
import os
import json

from db import init_db, drop_table
from logger import logger
from profiles import select_profile, create_profile, edit_profile, get_all_profiles, delete_profile
from algorithms import create_algorithm, select_algorithm, run_algorithm, edit_algorithm, display_algorithm, delete_algorithm
from stats import *
from utils import UI
from windows_provider import WindowProvider
if IS_MAC:
    import Quartz


pyautogui.PAUSE = 0.25
pyautogui.FAILSAFE = True

DEBUG = dotenv.get_key(dotenv.find_dotenv(), "DEBUG") in ["True", 1, "1", True]

def get_scale_factor():
    if IS_MAC:
        display_id = Quartz.CGMainDisplayID()

        logical_width = Quartz.CGDisplayBounds(display_id).size.width
        pixel_width = Quartz.CGDisplayPixelsWide(display_id)

        return pixel_width / logical_width
    return 1.0

def scale_region(region):
    scale = get_scale_factor()
    x, y, w, h = region
    return (
        int(x * scale),
        int(y * scale),
        int(w * scale),
        int(h * scale),
    )


class DogiatorsAutoClicker:
    def __init__(self, game_window_region=None, profile=None, stop_event=None):
        self.battle_count = 0
        self.screen_width, self.screen_height = pyautogui.size()
        self.click_delay = random.uniform(0.1, 0.3)
        self.repair_counter = 0
        self.next_repair = random.randint(1000, 2000)
        self.current_repair_index = 0
        self.cur_skill = 0
        self.current_profile = profile
        self.current_algorithm = None
        self.battle_boosts = False
        self.no_energy_mode = False
        self._missing_images = set()
        self.region = game_window_region
        self.stop_event = stop_event

        self.skill_cooldowns = {}
        self.skill_last_used = {}

        self.booster_cooldowns = {}
        self.booster_last_used = {}


    def _region(self):
        return self.region

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

        move_distance = random.randint(500, 600)
        pyautogui.moveRel(move_distance, 0, duration=random.uniform(0.1, 0.2))
        pyautogui.mouseUp()

        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)

        pyautogui.moveTo(x + offset_x, y + offset_y, duration=random.uniform(0.05, 0.1)) # mac // 2

        time.sleep(click_delay)
        pyautogui.click()

        self.random_move()

    def find_image(self, image_path, confidence=0.7, timeout=0.3):
        if not Path(image_path).is_file():
            if image_path not in self._missing_images:
                self._missing_images.add(image_path)
                logger.warning(f"Изображение {image_path} не найдено.")
            return False

        start_time = time.time()
        while not self.stop_event.is_set() and time.time() - start_time < timeout:
            try:
                center = pyautogui.locateCenterOnScreen(
                    image_path,
                    confidence=confidence,
                    region=self._region(),
                )

                if center:
                    return center
            except pyautogui.ImageNotFoundException:
                pass
            except Exception as e:
                if image_path not in self._missing_images:
                    self._missing_images.add(image_path)
                    logger.warning(
                        f"Ошибка поиска {image_path}: {e}"
                    )
                return False
            time.sleep(0.1)
        return False

    def find_and_click_image(self, image_path, confidence=0.7, timeout=0.3):
        """Поиск и клик по изображению на экране"""
        if not Path(image_path).is_file():
            if image_path not in self._missing_images:
                self._missing_images.add(image_path)
                logger.warning(f"Изображение {image_path} не найдено.")
            return False

        start_time = time.time()
        while not self.stop_event.is_set() and time.time() - start_time < timeout:
            try:
                center = pyautogui.locateCenterOnScreen(
                    image_path,
                    confidence=confidence,
                    region=self._region(),
                )

                if center:
                    x, y = center
                    self.smart_click(x, y)
                    return True
            except pyautogui.ImageNotFoundException:
                pass
            except Exception as e:
                if image_path not in self._missing_images:
                    self._missing_images.add(image_path)
                    logger.warning(
                        f"Ошибка поиска {image_path}: {e}"
                    )
                return False
            time.sleep(0.1)
        return False

    def load_profile_abilities(self):
        if not self.current_profile:
            return

        profile_name = self.current_profile[1]
        profile_id = self.current_profile[0]
        base = Path("images/profiles") / f"profile_{profile_id}"

        def load(dir_name):
            cfg = base / dir_name / "_config.json"
            if not cfg.exists():
                return {}

            try:
                data = json.loads(cfg.read_text())
                return {
                    k: float(v)
                    for k, v in data.items()
                    if isinstance(k, str) and isinstance(v, (int, float))
                }
            except Exception as e:
                UI.warning(f"Ошибка чтения {cfg}: {e}")
                return {}

        self.skill_cooldowns = load("skills")
        self.booster_cooldowns = load("boosters")

        now = time.time()
        self.skill_last_used = {k: 0 for k in self.skill_cooldowns}
        self.booster_last_used = {k: 0 for k in self.booster_cooldowns}

        UI.info(f"Навыки профиля {profile_name}: {self.skill_cooldowns}")
        UI.info(f"Бустеры профиля {profile_name}: {self.booster_cooldowns}")



    def check_repair_needed(self):
        """Проверка необходимости починки"""
        if (self.repair_counter >= self.next_repair):
            return True
        return False

    def repair_equipment(self):
        """Починка оборудования"""
        UI.warning("Починка оборудования...")

        self.find_and_click_image("images/inventory_button.png", timeout=2)
        if self.find_and_click_image("images/repair_button.png", timeout=2) and self.find_and_click_image("images/confirm_repair.png", timeout=2):
            self.repair_counter = 0
            if self.current_profile:
                self.next_repair = random.randint(
                    self.current_profile[3],
                    self.current_profile[4]
                )
                UI.info(f"Починка завершена. Следующая починка {self.current_profile[1]} через {self.next_repair} боёв.")

        self.find_and_click_image("images/home_button.png")

    def start_battle(self):
        # info: Функционал scroll вырезан, сайчас подземелья автоматически листается вниз
        time.sleep(0.7)
        logger.debug("Поиск кнопки fight")
        # for count_scroll in range(10):
        try:
            # try:
            #     locks = list(pyautogui.locateAllOnScreen("images/lock.png", confidence=0.98))
            # except Exception:
            #     locks = []

            try:    
                buttons = list(pyautogui.locateAllOnScreen(
                    "images/start_battle.png",
                    confidence=0.78,
                    region=self._region()
                ))
            except Exception as e:
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
            UI.error(f"{e}")
            return


    def dungeon_algorithm(self):
        """Алгоритм для подземелья"""
        logger.debug("Запуск алгоритма для подземелья...")

        while not self.stop_event.is_set():
            try:
                if not self.no_energy_mode:
                    if self.find_and_click_image("images/no_energy.png"):
                        UI.info("Не осталось энергии, остановка алгоритма подземелья...")
                        UI.info(f"Сыграно боев: {self.battle_count}")
                        return 0
                else:
                    self.find_and_click_image("images/no_energy_continue.png")

                self.use_additional()

                if self.battle_boosts:
                    self.use_battle_boosts()

                logger.debug("Проверка необходимости починки")
                if self.check_repair_needed():
                    logger.debug("Необходима починка")
                    self.repair_equipment()
                else:
                    logger.debug("Поиск кнопки подземелья")
                    self.find_and_click_image("images/dungeon_button.png", timeout=2)


                logger.debug("Поиск кнопки начала боя")
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
                            "Подземелье",
                            battle_res
                        )
                        logger.debug("Итог боя сохранен")
                    else:
                        logger.warning("Профиль или алгоритм не выбраны. Статистика боя сохранена без привязки к профилю и алгоритму.")
                        save_battle_stat(
                            self.current_profile[0] if self.current_profile is not None else None,
                            self.current_algorithm[0] if self.current_algorithm is not None else None,
                            "Подземелье",
                            battle_res,
                        )
                        logger.debug("Итог боя сохранен без привязки")
                    return 1

                logger.debug("Поиск кнопки забора награды")
                self.find_and_click_image("images/collect_reward.png")

                logger.debug("Поиск кнопки получения нового уровня")
                self.find_and_click_image("images/new_level.png")

                self.open_chest()

                self.use_skills()

            except KeyboardInterrupt:
                UI.info("Остановка алгоритма подземелья...")
                UI.info(f"Сыграно боев: {self.battle_count}")
                return 0
            except Exception as e:
                UI.error(f"Ошибка в алгоритме подземелья: {e}")
                continue

    def arena_3v3_algorithm(self):
        """Алгоритм для арены 3 на 3"""
        UI.info("Запуск алгоритма для арены 3 на 3...")

        while not self.stop_event.is_set():
            try:
                if not self.no_energy_mode:
                    if self.find_and_click_image("images/no_energy.png"):
                        UI.info("Не осталось энергии, остановка алгоритма подземелья...")
                        UI.info(f"Сыграно боев: {self.battle_count}")
                        return 0
                else:
                    self.find_and_click_image("images/no_energy_continue.png")

                self.use_additional()

                if self.battle_boosts:
                    self.use_battle_boosts()

                logger.debug("Проверка необходимости починки")
                if self.check_repair_needed():
                    logger.debug("Необходима починка")
                    self.repair_equipment()
                else: 
                    self.find_and_click_image("images/arena_button.png")

                self.find_and_click_image("images/3v3_mode.png")
                self.find_and_click_image("images/start_arena_battle.png", timeout=1, confidence=0.85)

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

                self.use_skills()

            except KeyboardInterrupt:
                UI.info("Остановка алгоритма арены...")
                UI.info(f"Сыграно боев: {self.battle_count}")
                return 0
            except Exception as e:
                logger.error(f"Ошибка в алгоритме арены 3 на 3: {e}")

    def arena_1v1_algorithm(self):
        """Алгоритм для арены 1 на 1"""
        UI.info("Запуск алгоритма для арены 1 на 1...")

        while not self.stop_event.is_set():
            try:
                if not self.no_energy_mode:
                    if self.find_and_click_image("images/no_energy.png"):
                        UI.info("Не осталось энергии, остановка алгоритма подземелья...")
                        UI.info(f"Сыграно боев: {self.battle_count}")
                        return 0
                else:
                    self.find_and_click_image("images/no_energy_continue.png")

                if self.battle_boosts:
                    self.use_battle_boosts()

                self.use_additional()

                if self.check_repair_needed():
                    logger.debug("Необходима починка")
                    self.repair_equipment()
                else: 
                    logger.debug("Поиск кнопки арены")
                    self.find_and_click_image("images/arena_button.png")

                logger.debug("Поиск кнопки старта битвы")
                self.find_and_click_image("images/start_arena_battle.png", confidence=0.85)

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

                self.use_skills()

            except KeyboardInterrupt:
                UI.info("Остановка алгоритма арены...")
                UI.info(f"Сыграно боев: {self.battle_count}")
                return 0
            except Exception as e:
                logger.error(f"Ошибка в алгоритме арены 1 на 1: {e}")

    def run_battle(self, battle_type):
        if battle_type == "3x3":
            return self.arena_3v3_algorithm()
        elif battle_type == "1x1":
            return self.arena_1v1_algorithm()
        elif battle_type == "Подземелье":
            return self.dungeon_algorithm()

        logger.error(f"Неизвестный тип боя: {battle_type}")
        

    def use_skills(self):
        base = Path("images/profiles") / f"profile_{self.current_profile[0]}" / "skills"

        for img_name, cooldown in self.skill_cooldowns.items():
            last = self.skill_last_used.get(img_name, 0)

            if time.time() - last < cooldown:
                continue

            img_path = base / img_name
            if not img_path.exists():
                continue

            center = self.find_image(str(img_path), confidence=0.95)
            if center:
                x, y = center
                pyautogui.doubleClick(x, y) # mac // 2
                self.skill_last_used[img_name] = time.time()

    def use_additional(self):
        """Использование доп. функций во время боя"""
        skills_dir = Path("images/additional")
        skill_images = list(skills_dir.glob("*.png"))

        for i in range(len(skill_images)):
            logger.debug(f"Поиск дополнительной кнопки №{i + 1}")
            start_time = time.time()
            while time.time() - start_time < 0.3:
                try:
                    center = self.find_image(str(skill_images[i]), confidence=0.95)

                    if center:
                        x, y = center
                        pyautogui.doubleClick(x, y) # mac // 2 
                except pyautogui.ImageNotFoundException:
                    pass

    def use_battle_boosts(self):
        base = Path("images/profiles") / f"profile_{self.current_profile[0]}" / "boosters"

        for img_name, cooldown in self.booster_cooldowns.items():
            last = self.booster_last_used.get(img_name, 0)

            if time.time() - last < cooldown:
                continue

            img_path = base / img_name
            if not img_path.exists():
                continue

            center = self.find_image(str(img_path), confidence=0.95)
            if center:
                x, y = center
                pyautogui.doubleClick(x, y)
                self.booster_last_used[img_name] = time.time()

    def check_for_battle_end(self):
        """Проверка окончания боя
        -1 - бой продолжается
        1 - победа
        2 - ничья
        0 - поражение
        """
        logger.debug("Проверка на окончания боя...")
        res = -1
        try:
            center = self.find_image("images/victory.png", confidence=0.95)
            if center:
                res = 1
        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            if DEBUG:
                print(e)

        if res == -1 :
            try:
                center = self.find_image("images/defeat.png", confidence=0.95)
                if center:
                    res = 0
            except pyautogui.ImageNotFoundException:
                pass
            except Exception as e:
                if DEBUG:
                    print(e)

        if res == -1 :
            try:
                center = self.find_image("images/draw.png", confidence=0.95)
                if center:
                    res = 2
            except pyautogui.ImageNotFoundException:
                pass
            except Exception as e:
                if DEBUG:
                    print(e)

        if res != -1 and self.find_and_click_image("images/continue_after_battle.png", timeout=0.7):
            self.repair_counter += 1
            self.battle_count += 1
            UI.info(f"Бой №{self.battle_count} завершён: {'победа' if res else 'поражение'}")
            return res
        return -1

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

        if not self.skill_cooldowns:
            warnings.append("у профиля нет настроенных КД навыков")

        if self.battle_boosts and not self.booster_cooldowns:
            warnings.append("включены бустеры, но КД не заданы")


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

    now_utc = datetime.now(timezone.utc)

    if choice == "2":
        start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        return start.strftime("%Y-%m-%d %H:%M:%S"), None

    if choice == "3":
        start = now_utc - timedelta(days=7)
        return start.strftime("%Y-%m-%d %H:%M:%S"), None

    if choice == "4":
        UI.info("Формат даты: YYYY-MM-DD")
        date_from = input("Дата ОТ: ").strip()
        date_to = input("Дата ДО: ").strip()

        date_from = f"{date_from} 00:00:00" if date_from else None
        date_to = f"{date_to} 23:59:59" if date_to else None

        return date_from, date_to

    UI.warning("Неверный выбор, показана статистика за всё время")
    return None, None

def assign_profiles_to_windows(windows, profiles):
    remaining_profiles = profiles.copy()

    for i, window in enumerate(windows, 1):
        UI.info("\n----------------------------")
        UI.info(f"Окно #{i}: {window.win.title}")
        UI.info("----------------------------")

        if not remaining_profiles:
            UI.warning("Доступных профилей больше нет")
            break

        UI.info("Выберите профиль для этого окна:")
        for idx, prof in enumerate(remaining_profiles, 1):
            UI.info(f"{idx} - {prof[1]}")

        UI.info("0 - Пропустить это окно")

        while True:
            try:
                choice = int(input("> "))

                if choice == 0:
                    break

                if 1 <= choice <= len(remaining_profiles):
                    window.profile = remaining_profiles.pop(choice - 1)
                    break

            except ValueError:
                pass

            print("Неверный ввод")

import os

def run_clicker_process(region, profile, algorithm, stop_event):
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    try:
        # save_region_screenshot(
        #     region,
        #     name=f"profile_{profile[1]}"
        # )

        UI.info(
            f"[PID {os.getpid()}] Старт профиля {profile[1]}"
        )
        UI.info(f"▶ Алгоритм: {algorithm[1]}")
        UI.info(f"▶ Боевые усилители: {'да' if algorithm[2] else 'нет'}")
        UI.info(f"▶ Игра без энергии: {'да' if algorithm[3] else 'нет'}")

        if IS_MAC:
            region = scale_region(region)

        clicker = DogiatorsAutoClicker(
            game_window_region=region,
            profile=profile,
            stop_event=stop_event
        )
        clicker.current_algorithm = algorithm
        clicker.battle_boosts = bool(algorithm[2])
        clicker.no_energy_mode = bool(algorithm[3])
        clicker.load_profile_abilities()

        if profile:
            next_repair = random.randint(profile[3], profile[4]) 
            clicker.next_repair = next_repair
            UI.success(f"Следующая починка {profile[1]} через {next_repair}")

        clicker.prebattle_warnings()
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        run_algorithm(clicker, algorithm[0])

        UI.info(
            f"[PID {os.getpid()}] Профиль {profile[1]} завершён"
        )
    except KeyboardInterrupt:
        stop_event.set()
        UI.info(
            f"[PID {os.getpid()}] Процесс остановлен пользователем"
        )
    except Exception as e:
        logger.error(
            f"[PID {os.getpid()}] Ошибка процесса: {e}"
        )
    finally:
        stats = stats_for_run(
            profile[0] if profile else None,
            algorithm[0],
            started_at
        )

        UI.success(f"[PID {os.getpid()}] Итог алгоритма")

        total = stats["total"]
        total_line = (
            f"  Всего боёв: {total['games']} | "
            f"Победы: {total['wins']} | "
            f"Поражения: {total['losses']} | "
            f"Винрейт: {total['winrate']}%"
        )

        if total["winrate"] >= 60:
            UI.success(total_line)
        elif total["winrate"] >= 40:
            UI.warning(total_line)
        else:
            UI.error(total_line)

        for battle_type, data in stats["by_type"].items():
            line = (
                f"  ▶ {battle_type}: "
                f"{data['wins']}/{data['games']} "
                f"({data['winrate']}%)"
            )

            if data["winrate"] >= 60:
                UI.success(line)
            elif data["winrate"] >= 40:
                UI.warning(line)
            else:
                UI.error(line)

def action_assign_profiles():
    windows = WindowProvider("Dogiators").get_windows()
    profiles = get_all_profiles()

    if not profiles:
        UI.warning("Профили отсутствуют. Создайте новый профиль.")
        return []

    if not windows:
        UI.warning("Окна с игрой не найдены.")
        return []

    assign_profiles_to_windows(windows, profiles)

    clickers = []
    for window in windows:
        if window.profile:
            clickers.append(
                DogiatorsAutoClicker(
                    game_window_region=window.region,
                    profile=window.profile
                )
            )

    UI.success(f"Профили назначены. Активных окон: {len(clickers)}")
    return clickers

def save_region_screenshot(region, name="region_debug"):
    os.makedirs("debug", exist_ok=True)

    img = pyautogui.screenshot(region=region)
    ts = time.strftime("%H%M%S")

    path = f"debug/{name}_{ts}.png"
    img.save(path)

    UI.info(f"[DEBUG] Region screenshot saved: {path}")

def setup_profile_cooldowns():
    profile = select_profile()
    if not profile:
        return

    profile_name = profile[1]
    profile_id = profile[0]
    base = Path("images/profiles") / f"profile_{profile_id}"

    UI.info("\nЧто настраиваем?")
    UI.info("1 - Навыки")
    UI.info("2 - Боевые бустеры")
    UI.info("0 - Назад")

    ch = input("> ").strip()
    if ch == "0":
        return

    if ch == "1":
        folder = base / "skills"
    elif ch == "2":
        folder = base / "boosters"
    else:
        UI.warning("Неверный выбор")
        return

    if not folder.exists():
        UI.error("Папка не найдена")
        return

    config_path = folder / "_config.json"
    try:
        config = json.loads(config_path.read_text()) if config_path.exists() else {}
    except Exception:
        config = {}

    images = sorted(p.name for p in folder.glob("*.png"))

    if not images:
        UI.warning("В папке нет картинок")
        return

    UI.success(f"\nНастройка КД для профиля «{profile_name}»")
    UI.info("Enter — оставить текущее значение")
    UI.info("0 — отключить (удалить из конфига)\n")

    for img in images:
        current = config.get(img)
        prompt = f"{img} (КД сейчас: {current if current is not None else 'нет'}): "
        val = input(prompt).strip()

        if val == "":
            continue
        if val == "0":
            config.pop(img, None)
            continue

        try:
            cd = float(val)
            if cd < 0:
                raise ValueError
            config[img] = cd
        except ValueError:
            UI.warning("Некорректное значение, пропущено")

    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False)
    )

    UI.success("КД сохранены")


def action_run_algorithm(clickers, algorithm):
    if not clickers:
        UI.warning("Сначала выберите профили для окон.")
        return

    if not algorithm:
        UI.warning("Сначала выберите алгоритм.")
        return

    stop_event = Event()
    processes = []

    UI.info(f"Запуск алгоритма: {algorithm[1]}")

    for clicker in clickers:
        p = Process(
            target=run_clicker_process,
            args=(
                clicker.region,
                clicker.current_profile,
                algorithm,
                stop_event
            )
        )
        p.start()
        processes.append(p)

    UI.success(f"Запущено процессов: {len(processes)}")

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        UI.warning("Остановка всех процессов...")
        stop_event.set()
        for p in processes:
            p.join(timeout=2)

        for p in processes:
            if p.is_alive():
                p.terminate()
        UI.info("Все процессы остановлены")

def action_show_stats():
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

    UI.info("\n=== ПО РЕЖИМАМ ===")
    for mode, g, w, l, wr in stats_by_battle_type(date_from, date_to):
        UI.info(f"{mode}: {wr}% ({w}/{g})")

def action_select_algorithm():
    algorithm = select_algorithm()
    if not algorithm:
        UI.warning("Алгоритм не выбран.")
        return None

    UI.success(f"Выбран алгоритм: {algorithm[1]}")
    return algorithm


def show_menu(selected_algorithm):
    UI.info("\n========= DOGIATORS CLICKER =========")

    UI.success("ПРОФИЛИ")
    UI.info(" 1 - Выбрать профили для окон")
    UI.info(" 2 - Создать профиль")
    UI.info(" 3 - Редактировать профиль")
    UI.info(" 4 - Настроить КД навыков / бустеров")
    UI.info(" 5 - Удалить профиль")

    UI.success("\nАЛГОРИТМЫ")
    UI.info(" 6 - Создать алгоритм")
    UI.info(" 7 - Выбрать алгоритм")
    UI.info(" 8 - Редактировать алгоритм")
    UI.info(" 9 - Удалить алгоритм")

    UI.success("\nЗАПУСК")
    if selected_algorithm:
        UI.info(f" 10 - Запустить алгоритм [{selected_algorithm[1]}]")
    else:
        UI.warning(" 10 - Запустить алгоритм [не выбран]")

    UI.success("\nСТАТИСТИКА")
    UI.info("11 - Показать статистику")
    UI.info("12 - Сбросить ВСЮ статистику")

    UI.error("\n0 - Выход")
    UI.info("====================================")



def main():
    clickers = []
    selected_algorithm = None

    while True:
        show_menu(selected_algorithm)
        choice = input("\n> ").strip()

        if choice == "0":
            UI.info("Выход...")
            break

        elif choice == "1":
            clickers = action_assign_profiles()

        elif choice == "2":
            create_profile()

        elif choice == "3":
            profile = select_profile()
            if profile:
                edit_profile(profile[0])

        elif choice == "4":
            setup_profile_cooldowns()

        elif choice == "5":
            profile = select_profile()
            if profile:
                delete_profile(profile[0])

        elif choice == "6":
            create_algorithm()

        elif choice == "7":
            selected_algorithm = action_select_algorithm()

        elif choice == "8":
            algorithm = select_algorithm()
            if algorithm:
                UI.info("Редактирование алгоритма:")
                display_algorithm(algorithm[0])
                edit_algorithm(algorithm[0])

        elif choice == "9":
            algorithm = select_algorithm()
            if algorithm:
                delete_algorithm(algorithm[0])

        elif choice == "10":
            action_run_algorithm(clickers, selected_algorithm)

        elif choice == "11":
            action_show_stats()

        elif choice == "12":
            UI.warning("Вы уверены, что хотите удалить ВСЮ статистику? (ДА/НЕТ)")
            confirm = input("> ").strip().lower()

            if confirm == "да":
                reset_stats()
                UI.success("Статистика полностью сброшена.")
            else:
                UI.info("Отмена.")

        else:
            UI.warning("Неверный выбор")


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()

    init_db()
    main()