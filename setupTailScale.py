import subprocess
import ctypes
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time

TAILSCALE_PATH = r'"C:\Program Files\Tailscale\tailscale.exe"'

# --------------------------
# Check if running as admin
# --------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# --------------------------
# Run command hidden
# --------------------------
def run_command(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

# --------------------------
# Convert IP to subnet
# --------------------------
def ip_to_subnet(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return None
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return None
    parts[3] = '0'
    return '.'.join(parts) + '/24'

# --------------------------
# Install and configure Tailscale
# --------------------------
def install_and_configure_thread():
    install_btn.config(state="disabled")
    progress_bar['value'] = 0
    root.update_idletasks()
    
    key_suffix = auth_entry.get().strip()
    enable_subnet = subnet_var.get()
    ip_input = plc_entry.get().strip()

    if not key_suffix:
        messagebox.showerror("Error", "Auth key is required")
        install_btn.config(state="normal")
        return

    full_key = f"tskey-auth-{key_suffix}"

    if enable_subnet:
        if not ip_input:
            messagebox.showerror("Error", "IP is required when subnet routing is enabled")
            install_btn.config(state="normal")
            return
        subnet = ip_to_subnet(ip_input)
        if subnet is None:
            messagebox.showerror("Error", "Invalid IP address format")
            install_btn.config(state="normal")
            return

    try:
        # --------------------------
        # Install Tailscale silently
        # --------------------------
        progress_label.config(text="Installing Tailscale...")
        progress_bar.start(10)
        # Accept agreements to avoid UI
        run_command(
            "winget install --id=Tailscale.Tailscale -e --source=winget "
            "--silent --accept-package-agreements --accept-source-agreements"
        )
        progress_bar.stop()
        progress_bar['value'] = 50
        root.update_idletasks()

        # --------------------------
        # Start Tailscale service
        # --------------------------
        progress_label.config(text="Starting Tailscale service...")
        run_command("powershell Start-Service Tailscale")
        time.sleep(3)
        progress_bar['value'] = 70
        root.update_idletasks()

        # --------------------------
        # Authenticate with Tailscale
        # --------------------------
        progress_label.config(text="Authenticating with Tailscale...")
        result = run_command(f'{TAILSCALE_PATH} up --auth-key {full_key}')
        if result.returncode != 0:
            messagebox.showerror("Invalid Key", "The Auth Key is invalid or expired.")
            install_btn.config(state="normal")
            progress_label.config(text="")
            progress_bar['value'] = 0
            return
        progress_bar['value'] = 90
        root.update_idletasks()

        # --------------------------
        # Advertise subnet if enabled
        # --------------------------
        if enable_subnet:
            progress_label.config(text="Advertising subnet...")
            run_command(f'{TAILSCALE_PATH} up --advertise-routes={subnet} --accept-dns=false')

        progress_bar['value'] = 100
        progress_label.config(text="Completed")
        messagebox.showinfo("Success", "Tailscale configured successfully!")

    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        install_btn.config(state="normal")
        progress_bar['value'] = 0
        progress_label.config(text="")

def install_and_configure():
    threading.Thread(target=install_and_configure_thread, daemon=True).start()

# --------------------------
# Relaunch as admin if needed
# --------------------------
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

# --------------------------
# GUI Setup
# --------------------------
root = tk.Tk()
root.title("Tailscale Setup")
root.geometry("450x300")

tk.Label(root, text="Enter Auth Key (suffix after 'tskey-auth-'):").pack(pady=5)

frame = tk.Frame(root)
frame.pack()

tk.Label(frame, text="tskey-auth-").pack(side="left")
auth_entry = tk.Entry(frame, width=35)
auth_entry.pack(side="left")

subnet_var = tk.BooleanVar()

def toggle_subnet_entry():
    if subnet_var.get():
        plc_entry.config(state="normal")
    else:
        plc_entry.delete(0, tk.END)
        plc_entry.config(state="disabled")

tk.Checkbutton(root, text="Enable Subnet Routing", variable=subnet_var, command=toggle_subnet_entry).pack(pady=10)

tk.Label(root, text="Enter any IP in subnet (e.g., 192.168.0.15):").pack()
plc_entry = tk.Entry(root, width=30, state="disabled")
plc_entry.pack()

install_btn = tk.Button(root, text="Install & Configure", command=install_and_configure)
install_btn.pack(pady=15)

# Progress bar
progress_label = tk.Label(root, text="")
progress_label.pack()
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(pady=10)

root.mainloop()