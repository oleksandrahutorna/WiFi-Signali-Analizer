import tkinter as tk
import os
import subprocess
import time
from tkinter import messagebox

log_file = "wifi_history.txt"


def get_wifi_data():
    try:
        # On Windows, running console tools can sometimes create a separate
        # console window. Use creationflags when available to avoid that.
        run_kwargs = {
            "capture_output": True,
            "check": False,
        }

        if os.name == "nt":
            # subprocess.CREATE_NO_WINDOW is available on Windows Python builds
            # and prevents a new console window from appearing.
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        completed = subprocess.run(["netsh", "wlan", "show", "interfaces"], **run_kwargs)
        result = completed.stdout.decode("cp866", errors="replace")
        result += completed.stderr.decode("cp866", errors="replace")
    except (FileNotFoundError, OSError):
        return "Відключено", 0

    ssid = "Відключено"
    signal = 0

    for line in result.splitlines():
        cleaned = line.strip()

        if ":" not in cleaned:
            continue

        key, value = [part.strip() for part in cleaned.split(":", 1)]
        key_lower = key.lower()

        if ("ssid" in key_lower and "bssid" not in key_lower) or (
            "назва" in key_lower and "мереж" in key_lower
        ):
            ssid = value or "Відключено"

        if (
            "signal" in key_lower
            or "сигнал" in key_lower
            or ("рівень" in key_lower and "сигнал" in cleaned.lower())
        ):
            try:
                signal = int(value.replace("%", "").replace(" ", "").strip())
            except ValueError:
                pass

    return ssid, signal


def save_to_file(ssid, signal):
    timestamp = time.strftime("%H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Мережа: {ssid} | Сигнал: {signal}%\n")


def update_loop():
    ssid, signal = get_wifi_data()

    label_ssid.config(text=f"SSID: {ssid}")
    label_percent.config(text=f"{signal}%")

    if signal > 75:
        color = "#2ecc71"
    elif signal > 40:
        color = "#f1c40f"
    else:
        color = "#e74c3c"

    canvas.coords(bar, 5, 5, 5 + (signal * 3.4), 35)
    canvas.itemconfig(bar, fill=color)

    log_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] Сигнал: {signal}%\n")
    log_box.see(tk.END)

    if int(time.time()) % 5 == 0:
        save_to_file(ssid, signal)

    if signal < 20 and ssid != "Відключено":
        label_warning.config(text="УВАГА: НИЗЬКИЙ СИГНАЛ!", fg="red")
    else:
        label_warning.config(text="")

    root.after(1000, update_loop)


def open_log_folder():
    try:
        os.startfile(os.getcwd())
    except AttributeError:
        os.system(f"explorer {os.getcwd()}")


def clear_logs():
    if os.path.exists(log_file):
        os.remove(log_file)
    log_box.delete(1.0, tk.END)
    messagebox.showinfo("Система", "Логи очищено!")


root = tk.Tk()
root.title("Wi-Fi Analizer Tool")
root.geometry("400x550")
root.config(bg="#121212")

tk.Label(root, text="Wi-Fi Monitor", font=("Arial", 18, "bold"), bg="#121212", fg="#00FF00").pack(pady=10)

label_ssid = tk.Label(root, text="SSID: Пошук...", font=("Arial", 12), bg="#121212", fg="white")
label_ssid.pack()

label_percent = tk.Label(root, text="0%", font=("Arial", 40, "bold"), bg="#121212", fg="white")
label_percent.pack()

canvas = tk.Canvas(root, width=350, height=40, bg="#333", highlightthickness=0)
canvas.pack(pady=10)
bar = canvas.create_rectangle(5, 5, 5, 35, fill="green", outline="")

label_warning = tk.Label(root, text="", font=("Arial", 10, "bold"), bg="#121212")
label_warning.pack()

tk.Label(root, text="Історія сигналу:", bg="#121212", fg="gray").pack()
log_box = tk.Text(root, width=40, height=8, bg="#222", fg="#00FF00", font=("Consolas", 9))
log_box.pack(pady=5)

btn_frame = tk.Frame(root, bg="#121212")
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Файли", command=open_log_folder, width=12).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Очистити", command=clear_logs, width=12).grid(row=0, column=1, padx=5)

update_loop()
root.mainloop()