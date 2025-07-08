import os, webbrowser
import customtkinter as ctk
from openai import OpenAI
from PIL import Image
from threading import Thread
import time
import json
import pickle
import zlib

CONFIG_PATH = "config.json"
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)
        
def launch_main_app():
    global app, current_session, client
    client = OpenAI(api_key=api_key)


def load_api_key():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            return config.get("api_key")
    return None

def save_api_key(key):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": key}, f)

api_key = load_api_key()

if not api_key:
    def save_key_and_continue():
        entered = api_entry.get().strip()
        if entered.startswith("sk-") or entered.startswith("sk-proj-"):
            save_api_key(entered)
            popup.destroy()
            global api_key
            api_key = entered
            launch_main_app() 
        else:
            error_label.configure(text="Invalid key")

    popup = ctk.CTk()
    popup.geometry("400x200")
    popup.title("Enter API Key")
    popup.configure(fg_color="#2c2c2c")

    ctk.CTkLabel(popup, text="Enter your OpenAI API Key:", font=("Segoe UI", 14)).pack(pady=(20,10))
    api_entry = ctk.CTkEntry(popup, width=300, placeholder_text="sk-...", show="*")
    api_entry.pack(pady=5)
    error_label = ctk.CTkLabel(popup, text="", text_color="red")
    error_label.pack()
    ctk.CTkButton(
        popup, text="Save",
        command=save_key_and_continue,
        fg_color="#888888", hover_color="#aaaaaa", text_color="white"
    ).pack(pady=20)

    popup.mainloop()
else:
    launch_main_app()


def get_colors():
    if ctk.get_appearance_mode() == "Light":
        return {
            "bg": "#ffffff",
            "mid": "#e0e0e0",
            "light": "#d0d0d0",
            "accent": "#a0a0a0",
            "text": "#111111",
            "border": "#cccccc"
        }
    else:
        return {
            "bg": "#1e1e1e",
            "mid": "#2c2c2c",
            "light": "#3a3a3a",
            "accent": "#5a5a5a",
            "text": "#e0e0e0",
            "border": "#444444"
        }

config = load_config()
SAVE_FILE = "chat_data.dat"
chat_sessions = {}

chat_buttons = {}

def save_sessions():
    try:
        with open(SAVE_FILE, "wb") as f:
            f.write(zlib.compress(pickle.dumps(chat_sessions)))
    except Exception as e:
        print("Failed to save sessions:", e)

def load_sessions():
    global chat_sessions
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "rb") as f:
                chat_sessions = pickle.loads(zlib.decompress(f.read()))
        except Exception as e:
            print("Failed to load sessions:", e)
            chat_sessions = {}
    if not chat_sessions:
        chat_sessions["Chat 1"] = []
ctk.set_appearance_mode(config.get("theme", "dark"))
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
current_session = ctk.StringVar(value="Chat 1")
app.geometry("800x600")
app.title("GPTLite")




current_session = ctk.StringVar(value="Chat 1")
chat_buttons = {}
def load_chat(name):
    header.configure(text=name if name else "New Chat")
    chat_display.configure(state="normal")
    chat_display.delete("1.0", "end")
    if name in chat_sessions:
        for role, msg in chat_sessions[name]:
            prefix = "You ▸" if role == "user" else "Bot ▸"
            chat_display.insert("end", f"\n{prefix}\n{msg}\n\n")
    chat_display.configure(state="disabled")

def update_theme():
    c = get_colors()
    app.configure(bg=c["bg"])
    try:
        main_area.configure(fg_color=c["mid"])
        chat_frame.configure(fg_color=c["bg"])
        input_frame.configure(fg_color=c["mid"])
        chat_display.configure(fg_color=c["bg"], text_color=c["text"], border_color=c["border"])
        user_input.configure(fg_color=c["light"], text_color=c["text"], border_color=c["border"])
        header.configure(text_color=c["text"])
        sidebar_container.configure(fg_color=c["bg"])
        sidebar.configure(fg_color=c["bg"])
        chat_buttons_frame.configure(fg_color=c["bg"])
        settings_btn.configure(hover_color=c["accent"], text_color=c["text"])

        for child in sidebar.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(fg_color=c["light"], hover_color=c["accent"], text_color=c["text"], border_color=c["border"])

        for btn in chat_buttons.values():
            btn.configure(fg_color="transparent", hover_color=c["light"], text_color=c["text"], border_color=c["border"])

        for row in chat_buttons_frame.winfo_children():
            for widget in row.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(hover_color=c["accent"], text_color=c["text"], border_color=c["border"])
    except Exception:
        pass

sidebar_container = ctk.CTkFrame(app, fg_color=get_colors()["bg"])
sidebar = ctk.CTkFrame(sidebar_container, width=200, fg_color=get_colors()["bg"])
sidebar.pack(side="left", fill="y")

chat_buttons_frame = ctk.CTkScrollableFrame(sidebar, width=180, label_text="Chats")
chat_buttons_frame.pack(fill="y", expand=True, pady=(10,10))

def inline_rename(row_frame, pencil_btn, old_name):
    btn = chat_buttons[old_name]
    btn.pack_forget()
    pencil_btn.pack_forget()

    entry = ctk.CTkEntry(row_frame, fg_color=get_colors()["light"], text_color=get_colors()["text"],
                         border_color=get_colors()["border"], height=30)
    entry.insert(0, old_name)
    entry.pack(side="left", fill="x", expand=True)
    entry.focus()

    def confirm(_=None):
        new_name = entry.get().strip()
        if not new_name or new_name == old_name:
            entry.destroy()
            btn.pack(side="left", fill="x", expand=True)
            pencil_btn.pack(side="right", padx=(5,0))
            return
        if new_name in chat_sessions:
            entry.configure(placeholder_text="Name exists")
            return
        chat_sessions[new_name] = chat_sessions.pop(old_name)
        if current_session.get() == old_name:
            current_session.set(new_name)
        entry.destroy()
        refresh_chat_list()

    entry.bind("<Return>", confirm)
    entry.bind("<FocusOut>", confirm)


def refresh_chat_list():
    for w in chat_buttons_frame.winfo_children(): w.destroy()
    chat_buttons.clear()
    for name in list(chat_sessions):
        row = ctk.CTkFrame(chat_buttons_frame, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)

        pencil = ctk.CTkButton(row, text="🖉", width=30, height=30, font=("Segoe UI", 14),
                               fg_color="transparent", hover_color=get_colors()["accent"],
                               text_color=get_colors()["text"],
                               command=lambda n=name, r=row: inline_rename(r, pencil, n))
        pencil.pack(side="right", padx=(5,0))
        pencil.pack_forget()

        def select_chat(n=name):
            current_session.set(n)
            load_sessions()
            refresh_chat_list()
            load_chat(current_session.get())

        btn = ctk.CTkButton(row, text=name, width=140, anchor="w",
                            fg_color=(get_colors()["accent"] if current_session.get()==name else "transparent"),
                            hover_color=get_colors()["light"], text_color=get_colors()["text"],
                            corner_radius=8, border_color=get_colors()["border"], command=select_chat)
        btn.pack(side="left", fill="x", expand=True)
        chat_buttons[name] = btn

        def show(_): pencil.pack(side="right", padx=(5,0))
        def hide(_):
            if not row.winfo_containing(app.winfo_pointerx(), app.winfo_pointery()):
                pencil.pack_forget()
        row.bind("<Enter>", show); row.bind("<Leave>", hide)
        btn.bind("<Enter>", show); btn.bind("<Leave>", hide)

def unique_chat_name():
    i = 1
    while f"Chat {i}" in chat_sessions: i += 1
    return f"Chat {i}"

def new_chat():
    name = unique_chat_name()
    chat_sessions[name] = []
    current_session.set(name)
    load_chat(name); refresh_chat_list(); save_sessions()

def delete_chat():
    name = current_session.get()
    if name in chat_sessions:
        del chat_sessions[name]
    current_session.set(next(iter(chat_sessions), "New Chat"))
    load_chat(current_session.get())
    refresh_chat_list()
    save_sessions()

def clear_chat():
    chat_sessions[current_session.get()] = []
    chat_display.configure(state="normal")
    chat_display.delete("1.0", "end")
    chat_display.configure(state="disabled")
    save_sessions()

toggle_var = ctk.BooleanVar(value=True)
def toggle_sidebar():
    if toggle_var.get():
        sidebar.pack_forget(); toggle_var.set(False); toggle_btn.configure(text="⏩")
    else:
        sidebar.pack(side="left", fill="y"); toggle_var.set(True); toggle_btn.configure(text="⏪")

toggle_btn = ctk.CTkButton(sidebar_container, text="⏪", width=30, height=30, font=("Segoe UI",16),
                           fg_color=get_colors()["light"], hover_color=get_colors()["accent"],
                           command=toggle_sidebar, corner_radius=8)
toggle_btn.pack(side="right", padx=(0,5), pady=5)

ctk.CTkButton(sidebar, text="➕ New Chat", command=new_chat,
              fg_color=get_colors()["light"], hover_color=get_colors()["accent"],
              corner_radius=8).pack(pady=5, fill="x")

ctk.CTkButton(sidebar, text="🧹 Clear Chat", command=clear_chat,
              fg_color=get_colors()["light"], hover_color=get_colors()["accent"],
              corner_radius=8).pack(pady=5, fill="x")

ctk.CTkButton(sidebar, text="❌ Delete Chat", command=delete_chat,
              fg_color=get_colors()["light"], hover_color=get_colors()["accent"],
              corner_radius=8).pack(pady=5, fill="x")


main_area = ctk.CTkFrame(app, fg_color=get_colors()["mid"])
top_nav = ctk.CTkFrame(main_area, fg_color="transparent")
top_nav.pack(fill="x", padx=20, pady=(10,0))

def open_settings():
    if hasattr(app, 'settings_popup') and app.settings_popup.winfo_exists():
        app.settings_popup.focus()
        return
    app.settings_popup = ctk.CTkToplevel(app)
    popup = app.settings_popup
    popup.title("Settings")
    popup.geometry("350x200")
    popup.configure(fg_color=get_colors()["bg"])
    popup.grab_set()
    top_bar = ctk.CTkFrame(popup, fg_color="transparent")
    top_bar.pack(fill="x", pady=10, padx=10)
    back_btn = ctk.CTkButton(top_bar, text="←", width=35, height=35, font=("Segoe UI", 16),
                             fg_color="transparent", hover_color=get_colors()["accent"],
                             command=popup.destroy)
    back_btn.pack(side="left")
    ctk.CTkLabel(popup, text="Appearance", font=("Segoe UI", 16, "bold"), text_color=get_colors()["text"]).pack(pady=(15,10))
    switch_var = ctk.BooleanVar(value=(ctk.get_appearance_mode() == "Dark"))
    def toggle_theme():
        theme = "dark" if switch_var.get() else "light"
        ctk.set_appearance_mode(theme)
        config = load_config()
        config["theme"] = theme
        save_config(config)
        update_theme()

    theme_switch = ctk.CTkSwitch(popup, text="Dark mode", variable=switch_var,
                                 onvalue=True, offvalue=False, command=toggle_theme,
                                 fg_color=get_colors()["light"],
                                 progress_color=get_colors()["accent"],
                                 text_color=get_colors()["text"])
    theme_switch.pack()

settings_btn = ctk.CTkButton(top_nav, text="⚙", width=35, height=35, font=("Segoe UI", 16),
                             fg_color="transparent", hover_color=get_colors()["accent"],
                             command=open_settings)
settings_btn.pack(side="left")

header = ctk.CTkLabel(main_area, text=current_session.get(), font=("Segoe UI", 22, "bold"),
                      anchor="center", text_color=get_colors()["text"])
header.pack(pady=(10,10))

chat_frame = ctk.CTkFrame(main_area, corner_radius=15, fg_color=get_colors()["bg"])
chat_frame.pack(padx=20, pady=10, fill="both", expand=True)

chat_display = ctk.CTkTextbox(chat_frame, state="disabled", font=("Segoe UI", 14),
                              wrap="word", text_color=get_colors()["text"],
                              fg_color=get_colors()["bg"], border_color=get_colors()["border"])
chat_display.pack(padx=10, pady=10, fill="both", expand=True)

input_frame = ctk.CTkFrame(main_area, fg_color=get_colors()["mid"])
input_frame.pack(padx=20, pady=(0,20), fill="x")

user_input = ctk.CTkEntry(input_frame, placeholder_text="Type your message here…",
                          height=40, font=("Segoe UI", 14),
                          fg_color=get_colors()["light"], text_color=get_colors()["text"],
                          border_color=get_colors()["border"])
user_input.pack(side="left", fill="x", expand=True, padx=(0,10))

def ask_openai(prompt):
    try:
        session = current_session.get()
        past = chat_sessions.get(session, [])
        messages = [{"role": r, "content": m} for r, m in past[-10:]]
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"


def send_message(_=None):
    prompt = user_input.get().strip()
    if not prompt: return
    session = current_session.get()
    if session not in chat_sessions: chat_sessions[session] = []
    chat_sessions[session].append(("user", prompt))
    chat_display.configure(state="normal")
    chat_display.insert("end", f"\nYou ▸\n{prompt}\n\n")
    chat_display.configure(state="disabled"); chat_display.see("end")
    user_input.delete(0,"end")

    response = ask_openai(prompt)
    chat_sessions[session].append(("assistant", response))
    chat_display.configure(state="normal")
    chat_display.insert("end", f"Bot ▸\n{response}\n\n")
    chat_display.configure(state="disabled"); chat_display.see("end")
    refresh_chat_list()

send_btn = ctk.CTkButton(input_frame, text="↑", width=40, height=40,
                         font=("Segoe UI",18,"bold"),
                         fg_color="white", text_color="#444",
                         hover_color="#ccc", corner_radius=20,
                         command=send_message)
send_btn.pack(side="right")
load_sessions()

welcome_frame = ctk.CTkFrame(app, fg_color=get_colors()["bg"])
welcome_frame.pack(fill="both", expand=True)

welcome_label = ctk.CTkLabel(welcome_frame, text="", font=("Segoe UI", 36, "bold"),
                             text_color=get_colors()["text"])
welcome_label.pack(pady=(150, 20))

def type_text(text):
    welcome_label.configure(text="")
    for i in range(len(text) + 1):
        welcome_label.configure(text=text[:i])
        time.sleep(0.1)

Thread(target=lambda: type_text("WELCOME...")).start()

def go_to_chat():
    welcome_frame.pack_forget()
    sidebar_container.pack(side="left", fill="y", padx=10, pady=10)
    main_area.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)
    refresh_chat_list()
    load_chat(current_session.get())
    update_theme()

go_btn = ctk.CTkButton(welcome_frame, text="Go to Chat →", font=("Segoe UI", 18, "bold"),
                       fg_color=get_colors()["light"], text_color=get_colors()["text"],
                       hover_color=get_colors()["accent"], command=go_to_chat)
go_btn.pack(pady=20)
footer_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
footer_frame.pack(side="bottom", pady=20)
footer_label = ctk.CTkLabel(footer_frame, text="GPT Lite by blitzdevdaddy", text_color=get_colors()["text"])
footer_label.pack(side="left")
github_icon_path = os.path.join("assets", "github.png")
github_img = ctk.CTkImage(light_image=Image.open(github_icon_path), size=(20, 20))
def open_github():
    webbrowser.open("https://github.com/Blitzdevdaddy")

github_btn = ctk.CTkButton(footer_frame, image=github_img, text="", width=30, height=30,
                            fg_color="transparent", hover_color=get_colors()["accent"],
                            command=open_github)
github_btn.pack(side="left", padx=5)

def on_close():
    save_sessions() 
    app.destroy()    

app.protocol("WM_DELETE_WINDOW", on_close)

app.mainloop()
