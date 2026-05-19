import time
import tkinter as tk

from auth_server import authenticate
from password_auth import check_password
from totp_auth import generate_totp
from user_db import get_user, reset_used_codes


# Кольорова гама інтерфейсу
BG = "#f4f0ea"
CARD = "#ffffff"
CARD_SOFT = "#f8f6f2"
BORDER = "#d8cfc3"

TEXT = "#1f2937"
MUTED = "#6b7280"

BLUE = "#3b82a0"
BLUE_DARK = "#25677f"
GREEN = "#3f7d58"
RED = "#b24a4a"
ORANGE = "#b7791f"
PURPLE = "#6d5a9c"
TEAL = "#2f766f"
GRAY = "#7b8794"

SUCCESS_BG = "#e4f3ea"
ERROR_BG = "#f8e5e5"
WAIT_BG = "#fff4d6"


class TwoFADemoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Тестове середовище двофакторної автентифікації")
        self.root.geometry("1180x760")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.username_var = tk.StringVar(value="sofiia")
        self.password_var = tk.StringVar(value="Student123")
        self.otp_var = tk.StringVar(value="")

        self.expected_code_var = tk.StringVar(value="------")
        self.client_code_var = tk.StringVar(value="Код, введений користувачем: не введено")
        self.time_left_var = tk.StringVar(value="-- с")
        self.compare_result_var = tk.StringVar(value="Код ще не порівнювався")

        self.login_check_var = tk.StringVar(value="1. Перевірка логіна: очікування")
        self.password_check_var = tk.StringVar(value="2. Перевірка пароля: очікування")
        self.otp_check_var = tk.StringVar(value="3. Перевірка TOTP-коду: очікування")
        self.reuse_check_var = tk.StringVar(value="4. Перевірка повторного використання: очікування")

        self.build_interface()
        self.add_log("Система запущена.")
        self.add_log("Тестовий користувач: sofiia; пароль: Student123.")
        self.update_expected_code()

    # ---------- створення інтерфейсу ----------
    def build_interface(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=0)

        title = tk.Label(
            self.root,
            text="Тестове середовище двофакторної автентифікації",
            bg=BG,
            fg=TEXT,
            font=("Arial", 20, "bold")
        )
        title.grid(row=0, column=0, sticky="w", padx=22, pady=(14, 2))

        subtitle = tk.Label(
            self.root,
            text="Модель демонструє взаємодію користувача, застосунку-автентифікатора та сервера під час перевірки 2FA.",
            bg=BG,
            fg=MUTED,
            font=("Arial", 10)
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 10))

        main = tk.Frame(self.root, bg=BG)
        main.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 6))

        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)

        client_card = self.create_card(main)
        client_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        server_card = self.create_card(main)
        server_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.build_client_block(client_card)
        self.build_server_block(server_card)

        bottom = tk.Frame(self.root, bg=BG)
        bottom.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 12))

        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=2)

        result_card = self.create_card(bottom)
        result_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        log_card = self.create_card(bottom)
        log_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.build_result_block(result_card)
        self.build_log_block(log_card)

    def create_card(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=CARD,
            padx=16,
            pady=12,
            highlightbackground=BORDER,
            highlightthickness=1
        )

    def create_label(self, parent, text, size=10, color=TEXT, bold=False):
        return tk.Label(
            parent,
            text=text,
            bg=parent["bg"],
            fg=color,
            font=("Arial", size, "bold" if bold else "normal"),
            justify="left"
        )

    def create_entry(self, parent, textvariable, show=None):
        return tk.Entry(
            parent,
            textvariable=textvariable,
            show=show,
            bg=CARD_SOFT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Arial", 11),
            highlightbackground=BORDER,
            highlightthickness=1
        )

    def create_button(self, parent, text, command, bg=BLUE, fg="white"):
        button = tk.Label(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            font=("Arial", 9, "bold"),
            padx=7,
            pady=7,
            cursor="hand2",
            relief="flat"
        )

        button.bind("<Button-1>", lambda event: command())
        button.bind("<Enter>", lambda event: button.config(bg=self.darken_color(bg)))
        button.bind("<Leave>", lambda event: button.config(bg=bg))

        return button

    def darken_color(self, color: str) -> str:
        colors = {
            BLUE: BLUE_DARK,
            GREEN: "#326947",
            RED: "#963d3d",
            ORANGE: "#966316",
            PURPLE: "#5c4b84",
            TEAL: "#27655f",
            GRAY: "#66717d"
        }
        return colors.get(color, color)

    def build_client_block(self, parent: tk.Frame) -> None:
        self.create_label(parent, "1. Користувач", size=15, bold=True).pack(anchor="w")
        self.create_label(
            parent,
            "Користувач вводить логін, пароль і код із застосунку-автентифікатора.",
            size=9,
            color=MUTED
        ).pack(anchor="w", pady=(2, 10))

        self.create_label(parent, "Логін", color=MUTED).pack(anchor="w")
        self.create_entry(parent, self.username_var).pack(fill="x", ipady=5, pady=(3, 8))

        self.create_label(parent, "Пароль", color=MUTED).pack(anchor="w")
        self.create_entry(parent, self.password_var, show="*").pack(fill="x", ipady=5, pady=(3, 8))

        self.create_label(parent, "TOTP-код, введений користувачем", color=MUTED).pack(anchor="w")
        self.create_entry(parent, self.otp_var).pack(fill="x", ipady=5, pady=(3, 10))

        action_row = tk.Frame(parent, bg=CARD)
        action_row.pack(fill="x", pady=(0, 12))

        self.create_button(
            action_row,
            "1. Згенерувати TOTP",
            self.generate_client_code,
            bg=GRAY
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.create_button(
            action_row,
            "2. Надіслати на сервер",
            self.login_request,
            bg=BLUE
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.create_label(parent, "Швидкі сценарії експерименту", size=13, bold=True).pack(anchor="w", pady=(0, 8))

        row1 = tk.Frame(parent, bg=CARD)
        row1.pack(fill="x", pady=(0, 6))

        row2 = tk.Frame(parent, bg=CARD)
        row2.pack(fill="x", pady=(0, 6))

        row3 = tk.Frame(parent, bg=CARD)
        row3.pack(fill="x")

        self.create_button(row1, "Успішний вхід", self.scenario_success, bg=GREEN).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        self.create_button(row1, "Неправильний код", self.scenario_wrong_code, bg=RED).pack(
            side="left", fill="x", expand=True, padx=(5, 5)
        )
        self.create_button(row1, "Без TOTP", self.scenario_without_totp, bg=ORANGE).pack(
            side="left", fill="x", expand=True, padx=(5, 0)
        )

        self.create_button(row2, "Прострочений код", self.scenario_expired_code, bg=PURPLE).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        self.create_button(row2, "Повторне використання", self.scenario_reuse_code, bg=TEAL).pack(
            side="left", fill="x", expand=True, padx=(5, 0)
        )

        self.create_button(
            row3,
            "Очистити використані коди",
            self.clear_used_codes,
            bg=GRAY
        ).pack(side="left", fill="x", expand=True)

    def build_server_block(self, parent: tk.Frame) -> None:
        self.create_label(parent, "2. Сервер автентифікації", size=15, bold=True).pack(anchor="w")
        self.create_label(
            parent,
            "Сервер самостійно обчислює очікуваний TOTP-код і порівнює його з кодом користувача.",
            size=9,
            color=MUTED
        ).pack(anchor="w", pady=(2, 10))

        codes_frame = tk.Frame(parent, bg=CARD)
        codes_frame.pack(fill="x", pady=(0, 8))

        left = tk.Frame(codes_frame, bg=CARD)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(codes_frame, bg=CARD)
        right.pack(side="left", fill="both", expand=True, padx=(20, 0))

        self.create_label(left, "Очікуваний TOTP на сервері", color=MUTED).pack(anchor="w")
        tk.Label(
            left,
            textvariable=self.expected_code_var,
            bg=CARD,
            fg="#2f6f8f",
            font=("Consolas", 24, "bold")
        ).pack(anchor="w", pady=(2, 4))

        self.create_label(right, "Час до зміни коду", color=MUTED).pack(anchor="w")
        tk.Label(
            right,
            textvariable=self.time_left_var,
            bg=CARD,
            fg=ORANGE,
            font=("Arial", 22, "bold")
        ).pack(anchor="w", pady=(2, 4))

        compare_card = tk.Frame(
            parent,
            bg=CARD_SOFT,
            padx=12,
            pady=8,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        compare_card.pack(fill="x", pady=(0, 10))

        tk.Label(
            compare_card,
            text="Порівняння кодів",
            bg=CARD_SOFT,
            fg=TEXT,
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            compare_card,
            textvariable=self.client_code_var,
            bg=CARD_SOFT,
            fg=TEXT,
            font=("Arial", 11)
        ).pack(anchor="w")

        tk.Label(
            compare_card,
            textvariable=self.compare_result_var,
            bg=CARD_SOFT,
            fg=MUTED,
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(4, 0))

        self.create_label(parent, "Етапи перевірки", size=13, bold=True).pack(anchor="w", pady=(0, 6))

        self.login_check_label = self.step_label(parent, self.login_check_var)
        self.password_check_label = self.step_label(parent, self.password_check_var)
        self.otp_check_label = self.step_label(parent, self.otp_check_var)
        self.reuse_check_label = self.step_label(parent, self.reuse_check_var)

        note = tk.Label(
            parent,
            text="Примітка: у реальних системах очікуваний TOTP-код не показується користувачу. "
                 "Тут він відображений лише для пояснення механізму перевірки.",
            bg=CARD,
            fg=MUTED,
            font=("Arial", 9),
            wraplength=520,
            justify="left"
        )
        note.pack(anchor="w", pady=(8, 0))

    def step_label(self, parent, variable):
        label = tk.Label(
            parent,
            textvariable=variable,
            bg=CARD,
            fg=MUTED,
            font=("Arial", 10),
            justify="left"
        )
        label.pack(anchor="w", pady=1)
        return label

    def build_result_block(self, parent: tk.Frame) -> None:
        self.create_label(parent, "3. Рішення системи", size=14, bold=True).pack(anchor="w")

        self.result_frame = tk.Frame(
            parent,
            bg=WAIT_BG,
            height=52,
            highlightbackground="#e7d08a",
            highlightthickness=1
        )
        self.result_frame.pack(fill="x", pady=(8, 6))
        self.result_frame.pack_propagate(False)

        self.result_label = tk.Label(
            self.result_frame,
            text="ОЧІКУВАННЯ ПЕРЕВІРКИ",
            bg=WAIT_BG,
            fg=ORANGE,
            font=("Arial", 14, "bold")
        )
        self.result_label.pack(expand=True)

        self.reason_label = tk.Label(
            parent,
            text="Для перевірки потрібно згенерувати або ввести TOTP-код і надіслати запит на сервер.",
            bg=CARD,
            fg=MUTED,
            font=("Arial", 9),
            wraplength=330,
            justify="left"
        )
        self.reason_label.pack(anchor="w")

    def build_log_block(self, parent: tk.Frame) -> None:
        self.create_label(parent, "4. Журнал експерименту", size=14, bold=True).pack(anchor="w", pady=(0, 6))

        self.log_text = tk.Text(
            parent,
            height=5,
            bg=CARD_SOFT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Consolas", 9),
            padx=10,
            pady=7,
            wrap="word",
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.log_text.pack(fill="both", expand=True)

    # ---------- логіка ----------
    def add_log(self, message: str) -> None:
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')}  {message}\n")
        self.log_text.see(tk.END)

    def set_result(self, access: bool | None, reason: str) -> None:
        if access is True:
            self.result_frame.config(bg=SUCCESS_BG, highlightbackground="#9acdaf")
            self.result_label.config(text="ДОСТУП ДОЗВОЛЕНО", bg=SUCCESS_BG, fg=GREEN)
        elif access is False:
            self.result_frame.config(bg=ERROR_BG, highlightbackground="#d9aaaa")
            self.result_label.config(text="ДОСТУП ЗАБОРОНЕНО", bg=ERROR_BG, fg=RED)
        else:
            self.result_frame.config(bg=WAIT_BG, highlightbackground="#e7d08a")
            self.result_label.config(text="ОЧІКУВАННЯ ПЕРЕВІРКИ", bg=WAIT_BG, fg=ORANGE)

        self.reason_label.config(text=reason)

    def update_expected_code(self) -> None:
        username = self.username_var.get().strip()
        user = get_user(username)

        if user:
            current_time = int(time.time())
            code = generate_totp(user["totp_secret"], for_time=current_time)
            time_left = 30 - (current_time % 30)

            self.expected_code_var.set(code)
            self.time_left_var.set(f"{time_left} с")
        else:
            self.expected_code_var.set("------")
            self.time_left_var.set("-- с")

        self.root.after(1000, self.update_expected_code)

    def reset_steps(self) -> None:
        self.login_check_var.set("1. Перевірка логіна: очікування")
        self.password_check_var.set("2. Перевірка пароля: очікування")
        self.otp_check_var.set("3. Перевірка TOTP-коду: очікування")
        self.reuse_check_var.set("4. Перевірка повторного використання: очікування")

        self.login_check_label.config(fg=MUTED)
        self.password_check_label.config(fg=MUTED)
        self.otp_check_label.config(fg=MUTED)
        self.reuse_check_label.config(fg=MUTED)

    def fill_default_credentials(self) -> None:
        self.username_var.set("sofiia")
        self.password_var.set("Student123")

    def generate_client_code(self) -> None:
        username = self.username_var.get().strip()
        user = get_user(username)

        if not user:
            self.add_log("Код не згенеровано: користувача не знайдено.")
            return

        code = generate_totp(user["totp_secret"])
        self.otp_var.set(code)
        self.client_code_var.set(f"Код, введений користувачем: {code}")
        self.compare_result_var.set("Код згенеровано у застосунку-автентифікаторі.")
        self.add_log(f"Застосунок-автентифікатор згенерував TOTP-код: {code}")

    def clear_used_codes(self) -> None:
        username = self.username_var.get().strip()

        if not username:
            self.add_log("Неможливо очистити використані коди: логін не введено.")
            return

        user = get_user(username)

        if not user:
            self.add_log("Неможливо очистити використані коди: користувача не знайдено.")
            return

        reset_used_codes(username)
        self.otp_var.set("")
        self.client_code_var.set("Код, введений користувачем: не введено")
        self.compare_result_var.set("Список використаних TOTP-кодів очищено.")
        self.reset_steps()
        self.set_result(None, "Список використаних TOTP-кодів очищено. Можна повторити експеримент.")
        self.add_log(f"Для користувача {username} очищено список використаних TOTP-кодів.")

    def login_request(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()
        otp_code = self.otp_var.get().strip()

        self.reset_steps()
        self.client_code_var.set(f"Код, введений користувачем: {otp_code if otp_code else 'не введено'}")

        self.add_log("-" * 80)
        self.add_log(f"На сервер надіслано запит автентифікації користувача: {username}")

        user = get_user(username)

        if not user:
            self.login_check_var.set("1. Перевірка логіна: користувача не знайдено")
            self.login_check_label.config(fg=RED)
        else:
            self.login_check_var.set("1. Перевірка логіна: користувача знайдено")
            self.login_check_label.config(fg=GREEN)

            password_valid = check_password(password, user["password_hash"])

            if password_valid:
                self.password_check_var.set("2. Перевірка пароля: пароль правильний")
                self.password_check_label.config(fg=GREEN)
            else:
                self.password_check_var.set("2. Перевірка пароля: пароль неправильний")
                self.password_check_label.config(fg=RED)

        expected = self.expected_code_var.get()

        if otp_code:
            self.compare_result_var.set(f"Сервер очікує код {expected}, користувач ввів {otp_code}.")
        else:
            self.compare_result_var.set(f"Сервер очікує код {expected}, але користувач код не ввів.")

        result = authenticate(username, password, otp_code)

        if result["access"]:
            self.otp_check_var.set("3. Перевірка TOTP-коду: код правильний і не прострочений")
            self.otp_check_label.config(fg=GREEN)

            self.reuse_check_var.set("4. Перевірка повторного використання: код не використовувався раніше")
            self.reuse_check_label.config(fg=GREEN)

            self.set_result(True, f"Причина: {result['reason']}")
            self.add_log(f"Рішення сервера: доступ дозволено. {result['reason']}")
        else:
            reason_lower = result["reason"].lower()

            if user and check_password(password, user["password_hash"]):
                if "вже був використаний" in reason_lower:
                    self.otp_check_var.set("3. Перевірка TOTP-коду: код збігається з очікуваним")
                    self.otp_check_label.config(fg=ORANGE)

                    self.reuse_check_var.set("4. Перевірка повторного використання: код уже використовувався")
                    self.reuse_check_label.config(fg=RED)
                elif "не введено" in reason_lower:
                    self.otp_check_var.set("3. Перевірка TOTP-коду: код не введено")
                    self.otp_check_label.config(fg=RED)

                    self.reuse_check_var.set("4. Перевірка повторного використання: не виконувалась")
                    self.reuse_check_label.config(fg=MUTED)
                else:
                    self.otp_check_var.set("3. Перевірка TOTP-коду: код неправильний або прострочений")
                    self.otp_check_label.config(fg=RED)

                    self.reuse_check_var.set("4. Перевірка повторного використання: не виконувалась")
                    self.reuse_check_label.config(fg=MUTED)

            self.set_result(False, f"Причина: {result['reason']}")
            self.add_log(f"Рішення сервера: доступ заборонено. Причина: {result['reason']}")

    # ---------- сценарії ----------
    def scenario_success(self) -> None:
        self.fill_default_credentials()
        self.generate_client_code()
        self.login_request()

    def scenario_wrong_code(self) -> None:
        self.fill_default_credentials()
        self.otp_var.set("000000")
        self.add_log("Сценарій: введено неправильний TOTP-код.")
        self.login_request()

    def scenario_without_totp(self) -> None:
        self.fill_default_credentials()
        self.otp_var.set("")
        self.add_log("Сценарій: користувач має пароль, але не вводить TOTP-код.")
        self.login_request()

    def scenario_expired_code(self) -> None:
        self.fill_default_credentials()
        user = get_user("sofiia")
        expired_code = generate_totp(user["totp_secret"], for_time=int(time.time()) - 90)
        self.otp_var.set(expired_code)
        self.add_log(f"Сценарій: введено прострочений TOTP-код: {expired_code}.")
        self.login_request()

    def scenario_reuse_code(self) -> None:
        self.fill_default_credentials()
        user = get_user("sofiia")
        code = generate_totp(user["totp_secret"])
        self.otp_var.set(code)
        self.add_log("Сценарій: перше використання поточного TOTP-коду.")
        self.login_request()
        self.add_log("Сценарій: повторне використання того самого TOTP-коду.")
        self.login_request()


def main() -> None:
    root = tk.Tk()
    TwoFADemoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()