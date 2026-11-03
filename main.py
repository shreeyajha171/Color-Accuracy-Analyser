import tkinter as tk
from tkinter import messagebox
import random, time, hashlib, os, csv
from datetime import datetime

USERS_FILE = "users.txt"
RESULTS_FILE = "color_results.csv"
ROUNDS = 10


def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            for line in f:
                if "," in line:
                    name, hashed = line.strip().split(",", 1)
                    users[name] = hashed
    return users


def register_user(name, password):
    if not name or not password:
        return "Please fill both fields"
    if name in load_users():
        return "Username already exists"
    with open(USERS_FILE, "a") as f:
        f.write(f"{name},{hash_pw(password)}\n")
    return "ok"


def check_login(name, password):
    return load_users().get(name) == hash_pw(password)


def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))


def to_hex(c):
    return "#%02x%02x%02x" % c


def make_options(correct):
    """Return 4 colors: the correct one plus 3 similar-looking decoys, shuffled."""
    options = [correct]
    while len(options) < 4:
        decoy = tuple(min(255, max(0, v + random.randint(-70, 70))) for v in correct)
        if decoy not in options:
            options.append(decoy)
    random.shuffle(options)
    return options


def save_result(user, score, accuracy, avg_time):
    with open(RESULTS_FILE, "a", newline="") as f:
        csv.writer(f).writerow([user, score, accuracy, avg_time, datetime.now().strftime("%d-%m-%Y %H:%M")])


def load_results(user):
    rows = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            for r in csv.reader(f):
                if r and r[0] == user:
                    rows.append(r)
    return rows


class LoginPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        tk.Label(self, text="Color Accuracy Analyzer", font=("Arial", 22, "bold")).pack(pady=25)
        tk.Label(self, text="Username").pack()
        self.user_entry = tk.Entry(self, width=28)
        self.user_entry.pack(pady=4)
        tk.Label(self, text="Password").pack()
        self.pass_entry = tk.Entry(self, width=28, show="*")
        self.pass_entry.pack(pady=4)
        tk.Button(self, text="Login", width=14, command=self.login).pack(pady=8)
        tk.Button(self, text="Register", width=14, command=self.register).pack()

    def login(self):
        name, pw = self.user_entry.get().strip(), self.pass_entry.get()
        if check_login(name, pw):
            self.app.user = name
            self.pass_entry.delete(0, "end")
            self.app.show("HomePage")
        else:
            messagebox.showerror("Error", "Wrong username or password")

    def register(self):
        msg = register_user(self.user_entry.get().strip(), self.pass_entry.get())
        if msg == "ok":
            messagebox.showinfo("Done", "Registered! You can log in now.")
        else:
            messagebox.showwarning("Oops", msg)


class HomePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.welcome = tk.Label(self, font=("Arial", 18, "bold"))
        self.welcome.pack(pady=30)
        tk.Button(self, text="Start Color Test", width=22, command=lambda: app.show("TestPage")).pack(pady=6)
        tk.Button(self, text="My Report", width=22, command=lambda: app.show("ReportPage")).pack(pady=6)
        tk.Button(self, text="Logout", width=22, command=self.logout).pack(pady=6)

    def on_show(self):
        self.welcome.config(text=f"Welcome, {self.app.user}!")

    def logout(self):
        self.app.user = None
        self.app.show("LoginPage")


class TestPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.info = tk.Label(self, font=("Arial", 13))
        self.info.pack(pady=10)
        self.code_label = tk.Label(self, font=("Courier", 20, "bold"))
        self.code_label.pack(pady=6)
        tk.Label(self, text="Click the box that matches this color").pack()
        row = tk.Frame(self)
        row.pack(pady=15)
        self.boxes = []
        for i in range(4):
            box = tk.Label(row, width=12, height=5, relief="raised", bd=3)   
            box.grid(row=0, column=i, padx=8)
            box.bind("<Button-1>", lambda e, idx=i: self.pick(idx))
            self.boxes.append(box)
        self.feedback = tk.Label(self, font=("Arial", 13, "bold"))
        self.feedback.pack(pady=6)
        tk.Button(self, text="Quit Test", width=12, command=lambda: app.show("HomePage")).pack(pady=6)

    def on_show(self):
        self.round, self.score, self.times = 0, 0, []
        self.feedback.config(text="")
        self.next_round()

    def next_round(self):
        self.target = random_color()
        self.options = make_options(self.target)
        self.info.config(text=f"Round {self.round + 1} of {ROUNDS}     Score: {self.score}")
        r, g, b = self.target
        self.code_label.config(text=f"RGB({r}, {g}, {b})   {to_hex(self.target)}")
        for box, color in zip(self.boxes, self.options):
            box.config(bg=to_hex(color))
        self.start = time.time()

    def pick(self, idx):
        self.times.append(time.time() - self.start)
        if self.options[idx] == self.target:
            self.score += 1
            self.feedback.config(text="Correct!", fg="green")
        else:
            self.feedback.config(text="Wrong!", fg="red")
        self.round += 1
        if self.round == ROUNDS:
            self.finish()
        else:
            self.next_round()

    def finish(self):
        accuracy = round(self.score / ROUNDS * 100, 1)
        avg_time = round(sum(self.times) / len(self.times), 2)
        save_result(self.app.user, self.score, accuracy, avg_time)
        messagebox.showinfo("Test over", f"Score: {self.score}/{ROUNDS}\nAccuracy: {accuracy}%\nAvg time: {avg_time}s")
        self.app.show("ReportPage")


class ReportPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        tk.Label(self, text="My Performance Report", font=("Arial", 18, "bold")).pack(pady=15)
        self.summary = tk.Label(self, font=("Arial", 12), fg="darkgreen")
        self.summary.pack(pady=5)
        self.listbox = tk.Listbox(self, width=62, height=10)
        self.listbox.pack(pady=10)
        tk.Button(self, text="Back", width=12, command=lambda: app.show("HomePage")).pack()

    def on_show(self):
        self.listbox.delete(0, "end")
        rows = load_results(self.app.user)
        if not rows:
            self.summary.config(text="No tests taken yet")
            return
        accs = [float(r[2]) for r in rows]
        times = [float(r[3]) for r in rows]
        self.summary.config(text=f"Tests: {len(rows)}   Best accuracy: {max(accs)}%   "
                                 f"Avg accuracy: {round(sum(accs)/len(accs), 1)}%   "
                                 f"Avg time: {round(sum(times)/len(times), 2)}s")
        for r in reversed(rows):
            self.listbox.insert("end", f"{r[4]}   {r[1]}/{ROUNDS}   {r[2]}%   {r[3]}s per color")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Color Perception & Accuracy Analyzer")
        self.geometry("700x470")
        self.user = None
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.pages = {}
        for P in (LoginPage, HomePage, TestPage, ReportPage):
            page = P(container, self)
            self.pages[P.__name__] = page
            page.grid(row=0, column=0, sticky="nsew")
        self.show("LoginPage")

    def show(self, name):
        page = self.pages[name]
        if hasattr(page, "on_show"):
            page.on_show()
        page.tkraise()


if __name__ == "__main__":
    App().mainloop()
