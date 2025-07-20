#!/usr/bin/env python3
"""
GRBL G-code Sender Script
Отправляет G-code файлы на GRBL контроллер через последовательный порт
"""

import serial
import time
import sys
import os
import argparse
from typing import Optional, List
import logging

class GRBLSender:
    """Класс для отправки G-code на GRBL контроллер"""

    def __init__(self, port: str, baud_rate: int = 115200, timeout: float = 1.0, logfile: str = None):
        """
        Инициализация подключения к GRBL

        Args:
            port: Последовательный порт (например, 'COM3' на Windows)
            baud_rate: Скорость передачи данных
            timeout: Таймаут для операций чтения/записи
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        if logfile is not None:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(logfile),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                handlers=[
                    logging.NullHandler()
                ]
            )

        self.logger = logging.getLogger(__name__)
    def connect(self) -> bool:
        """Подключение к GRBL контроллеру"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )

            # Ждем инициализации GRBL
            time.sleep(2)

            # Очищаем буфер
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

            # Проверяем подключение
            self.send_command("$I")
            response = self.read_response(10)

            if "[VER:1.1h.20190825:]" in response:
                self.logger.info(f"Успешно подключен к GRBL на порту {self.port}")
                return True
            else:
                self.logger.error("Не удалось подключиться к GRBL")
                return False

        except serial.SerialException as e:
            self.logger.error(f"Ошибка подключения к порту {self.port}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при подключении: {e}")
            return False

    def disconnect(self):
        """Отключение от GRBL контроллера"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.is_connected = False
            self.logger.info("Отключен от GRBL контроллера")

    def send_command(self, command: str) -> bool:
        """Отправка команды на GRBL"""
        if not self.serial_connection:
            self.logger.error("Нет подключения к GRBL")
            return False

        try:
            # Добавляем символ новой строки
            full_command = command.strip() + '\n'
            self.serial_connection.write(full_command.encode())
            self.serial_connection.flush()
            self.logger.info(f"Отправлена команда '{command}'")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка отправки команды '{command}': {e}")
            return False

    def read_response(self, timeout: float = 1.0) -> str:
        """Чтение ответа от GRBL"""
        if not self.serial_connection:
            return ""

        try:
            response = ""
            start_time = time.time()

            while time.time() - start_time < timeout:
                if self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        response += line + "\n"
                        if line.startswith("ok") or line.startswith("error"):
                            break
                time.sleep(0.01)

            return response.strip()
        except Exception as e:
            self.logger.error(f"Ошибка чтения ответа: {e}")
            return ""

    def wait_for_ok(self, timeout: float = 30.0) -> bool:
        """Ожидание ответа 'ok' от GRBL"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.read_response(0.1)
            if "ok" in response:
                return True
            elif "error" in response:
                self.logger.error(f"GRBL вернул ошибку: {response}")
                return False
            time.sleep(0.01)

        self.logger.error("Таймаут ожидания ответа 'ok'")
        return False

    def send_gcode_file(self, file_path: str, feed_rate: Optional[float] = None) -> bool:
        """
        Отправка G-code файла на печать

        Args:
            file_path: Путь к G-code файлу
            feed_rate: Скорость подачи (если нужно изменить)

        Returns:
            True если успешно, False в случае ошибки
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Файл не найден: {file_path}")
            return False

        if not self.serial_connection:
            self.logger.error("Нет подключения к GRBL")
            return False

        try:
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            self.logger.info(f"Начинаем отправку файла: {file_path}")
            self.logger.info(f"Количество строк: {len(lines)}")

            # Устанавливаем скорость подачи если указана
            if feed_rate:
                feed_command = f"F{feed_rate}"
                self.logger.info(f"Устанавливаем скорость подачи: {feed_rate}")
                if not self.send_command(feed_command):
                    return False
                if not self.wait_for_ok():
                    return False

            # Отправляем команды построчно
            line_count = 0
            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # Пропускаем пустые строки и комментарии
                if not line or line.startswith(';') or line.startswith('('):
                    continue

                # Удаляем комментарии в конце строки
                if ';' in line:
                    line = line.split(';')[0].strip()

                if not line:
                    continue

                # Отправляем команду
                self.logger.debug(f"Отправка строки {line_num}: {line}")
                if not self.send_command(line):
                    self.logger.error(f"Ошибка отправки строки {line_num}: {line}")
                    return False

                # Ждем подтверждения
                if not self.wait_for_ok():
                    self.logger.error(f"Нет подтверждения для строки {line_num}: {line}")
                    return False

                line_count += 1

                # Прогресс каждые 100 строк
                if line_count % 100 == 0:
                    self.logger.info(f"Отправлено строк: {line_count}")

            self.logger.info(f"Печать завершена. Всего отправлено строк: {line_count}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при отправке файла: {e}")
            return False

    def get_status(self) -> str:
        """Получение статуса GRBL"""
        self.send_command("?")
        return self.read_response()

    def emergency_stop(self):
        """Экстренная остановка"""
        self.send_command("!")
        self.logger.warning("Выполнена экстренная остановка")

    def soft_reset(self):
        """Мягкий сброс GRBL"""
        self.send_command("$X")
        self.logger.info("Выполнен мягкий сброс GRBL")

    def hard_reset(self):
        """Жесткий сброс GRBL"""
        self.send_command("$RST=*")
        self.logger.info("Выполнен жесткий сброс GRBL")


def list_available_ports():
    """Список доступных последовательных портов"""
    import serial.tools.list_ports

    ports = serial.tools.list_ports.comports()
    if not ports:
        print("Доступные порты не найдены")
        return

    print("Доступные последовательные порты:")
    for port in ports:
        print(f"  {port.device} - {port.description}")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="GRBL G-code Sender")
    parser.add_argument("file", help="Путь к G-code файлу")
    parser.add_argument("-p", "--port", default="COM3", help="Последовательный порт (по умолчанию: COM3)")
    parser.add_argument("-b", "--baudrate", type=int, default=115200,
                        help="Скорость передачи данных (по умолчанию: 115200)")
    parser.add_argument("-f", "--feed-rate", type=float, help="Скорость подачи")
    parser.add_argument("-t", "--timeout", type=float, default=1.0, help="Таймаут (по умолчанию: 1.0)")
    parser.add_argument("--list-ports", action="store_true", help="Показать доступные порты")
    parser.add_argument("--status", action="store_true", help="Показать статус GRBL")
    parser.add_argument("--emergency-stop", action="store_true", help="Экстренная остановка")
    parser.add_argument("--soft-reset", action="store_true", help="Мягкий сброс")
    parser.add_argument("--hard-reset", action="store_true", help="Жесткий сброс")
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный вывод")

    args = parser.parse_args()

    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Показать доступные порты
    if args.list_ports:
        list_available_ports()
        return

    # Создание отправителя
    sender = GRBLSender(args.port, args.baudrate, args.timeout)

    try:
        # Подключение
        if not sender.connect():
            sender.logger.error("Не удалось подключиться к GRBL")
            return 1

        # Выполнение команд
        if args.status:
            status = sender.get_status()
            print(f"Статус GRBL: {status}")
            return 0

        if args.emergency_stop:
            sender.emergency_stop()
            return 0

        if args.soft_reset:
            sender.soft_reset()
            return 0

        if args.hard_reset:
            sender.hard_reset()
            return 0

        # Отправка файла
        if not sender.send_gcode_file(args.file, args.feed_rate):
            sender.logger.error("Ошибка при отправке файла")
            return 1

        sender.logger.info("Файл успешно отправлен")
        return 0

    except KeyboardInterrupt:
        sender.logger.info("Прервано пользователем")
        sender.emergency_stop()
        return 1
    except Exception as e:
        sender.logger.error(f"Неожиданная ошибка: {e}")
        return 1
    finally:
        sender.disconnect()


if __name__ == "__main__":
    sys.exit(main())