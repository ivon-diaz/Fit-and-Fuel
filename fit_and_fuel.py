import tkinter as tk
from tkinter import messagebox

#importing SQLite
import sqlite3

#connecting to the database
import sqlite3

conn = sqlite3.connect("fit_and_fuel.db")
cursor = conn.cursor()

#users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

#Workouts table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

#Meals table
cursor.execute("""
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_name TEXT NOT NULL,
    calories INTEGER,
    protein REAL,
    carbs REAL,
    fats REAL,
    meal_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

conn.commit() 

#Adding a user
username = "ivon"
password = "mypassword123"

cursor.execute("""
INSERT INTO users (username, password)
VALUES (?, ?)
""", (username, password))

conn.commit()

# adding a workout
cursor.execute("""
INSERT INTO workouts (user_id, workout_type, duration, calories_burned, workout_date)
VALUES (?, ?, ?, ?, ?)
""", (1, "Running", 30, 250, "2026-04-13"))

conn.commit()

#adding a meal
cursor.execute("""
INSERT INTO meals (user_id, meal_name, calories, protein, carbs, fats, meal_date)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", (1, "Chicken Salad", 400, 35, 20, 15, "2026-04-13"))

conn.commit()

#read from the DB
cursor.execute("SELECT * FROM workouts WHERE user_id = ?", (1,))
workouts = cursor.fetchall()

for workout in workouts:
    print(workout)


#Show all meals for one user:
cursor.execute("SELECT * FROM meals WHERE user_id = ?", (1,))
meals = cursor.fetchall()

for meal in meals:
    print(meal)

#Connecting to TKinter
#def save_workout():
    #workout_type = workout_entry.get()
    #duration = duration_entry.get()
    
#



def handle_login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if username == "" or password == "":
        messagebox.showerror("Login Error", "Please enter both username and password.")
    else:
        login_frame.pack_forget()
        show_dashboard()


def show_dashboard():
    dashboard_frame.pack(fill="both", expand=True)


def open_log_meal():
    meal_window = tk.Toplevel(root)
    meal_window.title("Log Meal")
    meal_window.geometry("300x300")

    tk.Label(meal_window, text="Enter Meal Name:").pack(pady=5)
    meal_entry = tk.Entry(meal_window)
    meal_entry.pack(pady=5)

    tk.Label(meal_window, text="Calories:").pack(pady=5)
    calories_entry = tk.Entry(meal_window)
    calories_entry.pack(pady=5)

    def save_meal():
        meal = meal_entry.get().strip()
        calories = calories_entry.get().strip()

        if meal == "" or calories == "":
            messagebox.showerror("Error", "Please fill all fields.")
        else:
            messagebox.showinfo("Saved", f"{meal} saved with {calories} calories.")
            meal_window.destroy()

    tk.Button(meal_window, text="Save Meal", command=save_meal).pack(pady=15)


def log_workout():
    messagebox.showinfo("Log Workout", "Workout logging coming soon!")


def view_progress():
    messagebox.showinfo("View Progress", "Progress screen coming soon!")


# Main window
root = tk.Tk()
root.title("Fit & Fuel")
root.geometry("400x500")
root.configure(bg="white")

# ---------------- LOGIN FRAME ----------------
login_frame = tk.Frame(root, bg="white")

title_label = tk.Label(
    login_frame,
    text="Fit & Fuel",
    font=("Arial", 22, "bold"),
    bg="white",
    fg="black"
)
title_label.pack(pady=30)

subtitle_label = tk.Label(
    login_frame,
    text="Login to continue",
    font=("Arial", 12),
    bg="white",
    fg="gray"
)
subtitle_label.pack(pady=5)

tk.Label(login_frame, text="Username", font=("Arial", 11), bg="white").pack(pady=(20, 5))
username_entry = tk.Entry(login_frame, font=("Arial", 11), width=25)
username_entry.pack(pady=5)

tk.Label(login_frame, text="Password", font=("Arial", 11), bg="white").pack(pady=(15, 5))
password_entry = tk.Entry(login_frame, font=("Arial", 11), width=25, show="*")
password_entry.pack(pady=5)

login_button = tk.Button(
    login_frame,
    text="Login",
    font=("Arial", 12),
    width=18,
    height=2,
    command=handle_login
)
login_button.pack(pady=30)

login_frame.pack(fill="both", expand=True)

# ---------------- DASHBOARD FRAME ----------------
dashboard_frame = tk.Frame(root, bg="white")

dashboard_title = tk.Label(
    dashboard_frame,
    text="Fit & Fuel Dashboard",
    font=("Arial", 18, "bold"),
    bg="white"
)
dashboard_title.pack(pady=30)

meal_button = tk.Button(
    dashboard_frame,
    text="Log Meal",
    font=("Arial", 12),
    width=20,
    height=2,
    command=open_log_meal
)
meal_button.pack(pady=10)

workout_button = tk.Button(
    dashboard_frame,
    text="Log Workout",
    font=("Arial", 12),
    width=20,
    height=2,
    command=log_workout
)
workout_button.pack(pady=10)

progress_button = tk.Button(
    dashboard_frame,
    text="View Progress",
    font=("Arial", 12),
    width=20,
    height=2,
    command=view_progress
)
progress_button.pack(pady=10)

root.mainloop()