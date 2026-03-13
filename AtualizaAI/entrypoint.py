import subprocess
import os
import sys
import time
import signal

def start_streamlit():
    print("🚀 Iniciando Streamlit Dashbord (Port 8080)...")
    return subprocess.Popen([
        "streamlit", "run", "src/dashboard/Home.py",
        "--server.port", os.getenv("PORT", "8080"),
        "--server.address", "0.0.0.0"
    ])

def start_bot():
    print("🤖 Iniciando Telegram Bot Bridge...")
    return subprocess.Popen([sys.executable, "run_telegram_bot.py"])

def main():
    # Inicia ambos os processos
    streamlit_proc = start_streamlit()
    bot_proc = start_bot()

    def signal_handler(sig, frame):
        print("\n🛑 Encerrando plataforma...")
        streamlit_proc.terminate()
        bot_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        # Verifica se os processos ainda estão rodando
        if streamlit_proc.poll() is not None:
            print("⚠️ Streamlit parou! Reiniciando...")
            streamlit_proc = start_streamlit()
        
        if bot_proc.poll() is not None:
            print("⚠️ Telegram Bot parou! Reiniciando...")
            bot_proc = start_bot()
            
        time.sleep(15)

if __name__ == "__main__":
    main()
