import cv2
import requests
import ipaddress
import os
import socket
from onvif import ONVIFCamera
from urllib3.exceptions import InsecureRequestWarning

# ===== НАСТРОЙКИ =====
SCREENSHOTS_DIR = r"D:\temp\screenshots"  # Папка для скриншотов
RTSP_PORT = 554  # Стандартный порт RTSP
TIMEOUT = 2  # Таймаут подключения (сек)
# =====================

# Отключаем предупреждения HTTPS
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def load_credentials():
    """Загружает логины/пароли из файла (запрашивает путь)."""
    while True:
        file_path = input("Введите путь к файлу с паролями (например, C:\passwords.txt): ").strip()
        if os.path.exists(file_path):
            break
        print("❌ Файл не найден. Попробуйте ещё раз.")

    credentials = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split(":")
                if len(parts) == 2:
                    credentials.append((parts[0], parts[1]))
    return credentials


def is_port_open(ip, port):
    """Проверяет, открыт ли порт на IP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    try:
        result = sock.connect_ex((str(ip), port))
        return result == 0
    except Exception:
        return False
    finally:
        sock.close()


def try_rtsp(ip, username, password):
    """Пробует получить скриншот через RTSP."""
    rtsp_urls = [
        f"rtsp://{ip}:{RTSP_PORT}/live",
        f"rtsp://{ip}:{RTSP_PORT}/cam/realmonitor",
        f"rtsp://{ip}:{RTSP_PORT}/Streaming/Channels/1",
    ]

    for url in rtsp_urls:
        auth_url = url.replace("rtsp://", f"rtsp://{username}:{password}@")
        print(f"Пробуем RTSP: {auth_url}")
        cap = cv2.VideoCapture(auth_url)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{ip}_screenshot.jpeg")
                cv2.imwrite(screenshot_path, frame)
                print(f"✅ Скриншот сохранён: {screenshot_path}")
                return True
    return False


def scan_network(ip_range, credentials):
    """Сканирует сеть и проверяет RTSP-порт."""
    network = ipaddress.ip_network(ip_range, strict=False)
    print(f"\n🔍 Сканирую {ip_range} ({network.num_addresses} IP)...")

    for ip in network.hosts():
        ip_str = str(ip)
        print(f"\nПроверяю {ip_str}...")

        if not is_port_open(ip_str, RTSP_PORT):
            print(f"Порт {RTSP_PORT} закрыт, пропускаю.")
            continue

        print(f"Порт {RTSP_PORT} открыт! Пробую подключиться...")
        for username, password in credentials:
            if try_rtsp(ip_str, username, password):
                break  # Успех, переходим к следующему IP


if __name__ == "__main__":
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    print("=== Сканер IP-камер ===")
    credentials = load_credentials()
    ip_range = input("Введите IP-диапазон (например, 192.168.0.0/24): ").strip()

    scan_network(ip_range, credentials)
    print("\nГотово! Результаты в папке:", SCREENSHOTS_DIR)