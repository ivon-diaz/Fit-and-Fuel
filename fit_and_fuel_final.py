# Fit & Fuel - A Personal Fitness and Nutrition Tracker

#libraries

import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from openai import OpenAI
import json
import os
import hashlib

client = OpenAI(api_key=("sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"))

#importing SQLite
import sqlite3


# Keeps track of the currently logged-in user's ID 
current_user_id = None

conn = sqlite3.connect("fit_and_fuel.db")
cursor = conn.cursor()

# Users table - stores username, password, age, weight, height
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    age INTEGER,
    weight REAL,
    height REAL
)
""")
try:
    cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN weight REAL")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN height REAL")
except sqlite3.OperationalError:
    pass

# Workouts table - stores workout type, duration, calories burned, date, and links to user ID 
cursor.execute("""
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    workout_type TEXT,
    duration INTEGER,
    calories_burned INTEGER,
    workout_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

#Meals table - stores meal description, calories, protein, carbs, fats, date, and links to user ID
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


# Workout Entry - allows users to log their workouts, including type, duration, calories burned, and date. If calories burned is not provided
# it estimates based on workout type, duration, intensity, and user weight.

def estimate_calories(workout_type, duration, intensity, weight):
    workout_type = workout_type.lower()
    intensity = intensity.lower()

    if "walk" in workout_type:
        met = 3.5
    elif "run" in workout_type:
        met = 9.8
    elif "bike" in workout_type or "cycling" in workout_type:
        met = 7.5
    elif "strength" in workout_type or "weights" in workout_type:
        met = 6.0
    elif "yoga" in workout_type:
        met = 2.5
    else:
        met = 4.5

    if intensity == "low":
        met *= 0.85
    if intensity == "medium":
        met *= 1.0
    elif intensity == "high":
        met *= 1.15

    weight_kg = weight / 2.205
    calories = (met * weight_kg * 3.5 / 200) * duration

    return int(calories)
    
# Workout logging window - users can enter workout type, duration, calories burned (optional), date, and intensity.
# If calories burned is left blank, it will be estimated based on the workout type, duration, intensity, and user weight.
def log_workout():
    global current_user_id

    if current_user_id is None:
        messagebox.showerror("Error", "No user is logged in.")
        return

    workout_window = tk.Toplevel(root)
    workout_window.title("Log Workout")
    workout_window.geometry("400x500")
    workout_window.configure(bg="white")

    tk.Label(
        workout_window,
        text="Log Workout",
        font=("Arial", 16, "bold"),
        bg="white"
    ).pack(pady=15)

    tk.Label(workout_window, text="Workout Type", font=("Arial", 11), bg="white").pack(pady=(10, 5))
    workout_type_entry = tk.Entry(workout_window, font=("Arial", 11), width=30)
    workout_type_entry.pack(pady=5)

    tk.Label(workout_window, text="Duration in Minutes", font=("Arial", 11), bg="white").pack(pady=(10, 5))
    duration_entry = tk.Entry(workout_window, font=("Arial", 11), width=30)
    duration_entry.pack(pady=5)

    tk.Label(workout_window, text="Calories Burned (optional)", font=("Arial", 11), bg="white").pack(pady=(10, 5))
    calories_entry = tk.Entry(workout_window, font=("Arial", 11), width=30)
    calories_entry.pack(pady=5)

    tk.Label(workout_window, text="Workout Date (YYYY-MM-DD)", font=("Arial", 11), bg="white").pack(pady=(10, 5))
    workout_date_entry = tk.Entry(workout_window, font=("Arial", 11), width=30)
    workout_date_entry.pack(pady=5)

    from datetime import date
    workout_date_entry.insert(0, str(date.today()))

    tk.Label(workout_window, text="Intensity (low, medium, high)", font=("Arial", 11), bg="white").pack(pady=(10, 5))
    intensity_entry = tk.Entry(workout_window, font=("Arial", 11), width=30)
    intensity_entry.pack(pady=5)
    intensity_entry.insert(0, "medium")

    def save_workout():
        workout_type = workout_type_entry.get().strip()
        duration = duration_entry.get().strip()
        calories_burned = calories_entry.get().strip()
        workout_date = workout_date_entry.get().strip()
        intensity = intensity_entry.get().strip()

        if workout_type == "" or duration == "" or workout_date == "":
            messagebox.showerror("Error", "Please fill in workout type, duration, and date.")
            return

        try:
            duration = int(duration)

            if calories_burned == "":
                cursor.execute("SELECT weight FROM users WHERE id = ?", (current_user_id,))
                result = cursor.fetchone()

                if result is None or result[0] is None:
                    messagebox.showerror("Error", "User weight not found. Please update your profile.")
                    return

                user_weight = result[0]

                calories_burned = estimate_calories(workout_type, duration, intensity, user_weight)

            else:
                calories_burned = int(calories_burned)

        except ValueError:
            messagebox.showerror("Error", "Duration and calories must be numbers.")
            return

        cursor.execute("""
            INSERT INTO workouts (user_id, workout_type, duration, calories_burned, workout_date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            current_user_id,
            workout_type,
            duration,
            calories_burned,
            workout_date
        ))

        conn.commit()

        messagebox.showinfo("Saved", "Workout saved successfully!")
        workout_window.destroy()

    tk.Button(
        workout_window,
        text="Save Workout",
        font=("Arial", 12),
        width=18,
        height=2,
        command=save_workout
    ).pack(pady=30)

#read from the DB
cursor.execute("SELECT * FROM workouts WHERE user_id = ?", (1,))
workouts = cursor.fetchall()

for workout in workouts:
    print(workout)


# login function - checks username and password against the database, and if valid
# stores the user's ID in current_user_id and shows the dashboard. If invalid, shows an error message.

def handle_login():
    global current_user_id

    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if username == "" or password == "":
        messagebox.showerror("Login Error", "Please enter both username and password.")
        return

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    user = cursor.fetchone()

    if user:
        current_user_id = user[0]  # store logged-in user's ID
        messagebox.showinfo("Success", "Login successful!")
        login_frame.pack_forget()
        show_dashboard()
    else:
        messagebox.showerror("Login Error", "Invalid username or password.")



#-----------------Profile Update-----------------
def open_profile():
    if current_user_id is None:
        messagebox.showerror("Error", "No user is logged in.")
        return

    profile_window = tk.Toplevel(root)
    profile_window.title("Update Profile")
    profile_window.geometry("350x350")

    tk.Label(profile_window, text="Update Profile", font=("Arial", 16, "bold")).pack(pady=15)

    tk.Label(profile_window, text="Age").pack()
    age_entry = tk.Entry(profile_window)
    age_entry.pack(pady=5)

    tk.Label(profile_window, text="Weight (lbs)").pack()
    weight_entry = tk.Entry(profile_window)
    weight_entry.pack(pady=5)

    tk.Label(profile_window, text="Height (inches)").pack()
    height_entry = tk.Entry(profile_window)
    height_entry.pack(pady=5)

    def save_profile():
        age = age_entry.get().strip()
        weight = weight_entry.get().strip()
        height = height_entry.get().strip()

        try:
            age = int(age)
            weight = float(weight)
            height = float(height)
        except ValueError:
            messagebox.showerror("Error", "Age, weight, and height must be numbers.")
            return

        cursor.execute("""
            UPDATE users
            SET age = ?, weight = ?, height = ?
            WHERE id = ?
        """, (age, weight, height, current_user_id))

        conn.commit()
        messagebox.showinfo("Saved", "Profile updated successfully!")
        profile_window.destroy()

    tk.Button(profile_window, text="Save Profile", command=save_profile).pack(pady=20)


# Creating the create account window

def open_create_account():
    create_window = tk.Toplevel(root)
    create_window.title("Create Account")
    create_window.geometry("350x550")

    tk.Label(create_window, text="Create Account", font=("Arial", 16, "bold")).pack(pady=15)

    tk.Label(create_window, text="Username").pack(pady=(10, 5))
    new_username_entry = tk.Entry(create_window, width=25)
    new_username_entry.pack(pady=5)

    tk.Label(create_window, text="Password").pack(pady=(10, 5))
    new_password_entry = tk.Entry(create_window, width=25, show="*")
    new_password_entry.pack(pady=5)

    tk.Label(create_window, text="Confirm Password").pack(pady=(10, 5))
    confirm_password_entry = tk.Entry(create_window, width=25, show="*")
    confirm_password_entry.pack(pady=5)

    tk.Label(create_window, text="Age").pack(pady=(10, 5))
    age_entry = tk.Entry(create_window, width=25)
    age_entry.pack(pady=5)

    tk.Label(create_window, text="Weight (lbs)").pack(pady=(10, 5))
    weight_entry = tk.Entry(create_window, width=25)
    weight_entry.pack(pady=5)

    tk.Label(create_window, text="Height (inches)").pack(pady=(10, 5))
    height_entry = tk.Entry(create_window, width=25)
    height_entry.pack(pady=5)

    message_label = tk.Label(
    create_window,
    text="",
    font=("Arial", 10),
    fg="green",
    width=35
)
    message_label.pack(pady=5)


# nested function to save the new account to the database, with validation for empty fields,
# password match, and existing username. It also hashes the password before saving.

    def save_new_account():
        new_username = new_username_entry.get().strip()
        new_password = new_password_entry.get().strip()
        confirm_password = confirm_password_entry.get().strip()
        age = age_entry.get().strip()
        weight = weight_entry.get().strip()
        height = height_entry.get().strip()

        if new_username == "" or new_password == "" or confirm_password == "":
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        cursor.execute("SELECT * FROM users WHERE username = ?", (new_username,))
        existing_user = cursor.fetchone()

        if existing_user:
            messagebox.showerror("Error", "That username already exists, please create a different username.")
            return
        
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

        cursor.execute(
            "INSERT INTO users (username, password, age, weight, height) VALUES (?, ?, ?, ?, ?)",
            (new_username, new_password, int(age), float(weight), float(height))
        )
        conn.commit()

        message_label.config(
        text="Your account has been created! Welcome!",
        fg="green"
)

    tk.Button(
        create_window,
        text="Create Account",
        font=("Arial", 11),
        command=save_new_account
    ).pack(pady=20)

# function to show the dashboard frame after successful login, and hide the login frame.
def show_dashboard():
    dashboard_frame.pack(fill="both", expand=True)

# function to open the log meal window, where users can enter a meal description and date,
# AI will analyze the meal to estimate calories, protein, carbs, and fats. The user can then save the meal to their profile.
def open_log_meal():
    global current_user_id

    meal_window = tk.Toplevel(root)
    meal_window.title("Log Meal")
    meal_window.geometry("400x420")
    meal_window.configure(bg="white")

    tk.Label(
        meal_window,
        text="Describe Your Meal",
        font=("Arial", 16, "bold"),
        bg="white"
    ).pack(pady=15)

    tk.Label(
        meal_window,
        text="Example: 2 eggs, 2 pieces of toast, 1/2 avocado",
        font=("Arial", 10),
        bg="white",
        fg="gray"
    ).pack(pady=5)

    meal_entry = tk.Entry(meal_window, font=("Arial", 11), width=35)
    meal_entry.pack(pady=10)

    tk.Label(
    meal_window,
    text="Select Date (YYYY-MM-DD):",
    font=("Arial", 10),
    bg="white"
    ).pack(pady=5)

    meal_date_entry = tk.Entry(meal_window, font=("Arial", 11), width=25)
    meal_date_entry.pack(pady=5)

    from datetime import date
    meal_date_entry.insert(0, str(date.today()))

    result_label = tk.Label(
        meal_window,
        text="",
        font=("Arial", 11),
        bg="white",
        justify="left"
    )
    result_label.pack(pady=15)

    analyzed_data = {}

    def analyze_meal():
        meal_text = meal_entry.get().strip()

        if meal_text == "":
            messagebox.showerror("Error", "Please enter a meal description.")
            return

        try:
            response = client.responses.create(
                model="gpt-4o-mini",
                input=f"""
    Estimate the calories, protein, carbs, and fats for this meal:
    {meal_text}

    Return ONLY valid JSON like this:
    {{
        "calories": 400,
        "protein": 25,
        "carbs": 35,
        "fats": 15
    }}
    """
    )

            nutrition_text = response.output_text
            nutrition = json.loads(nutrition_text)

            analyzed_data["calories"] = int(nutrition["calories"])
            analyzed_data["protein"] = float(nutrition["protein"])
            analyzed_data["carbs"] = float(nutrition["carbs"])
            analyzed_data["fats"] = float(nutrition["fats"])

            result_label.config(
                text=(
                    "AI Estimated Nutrition:\n"
                    f"Calories: {analyzed_data['calories']}\n"
                    f"Protein: {analyzed_data['protein']} g\n"
                    f"Carbs: {analyzed_data['carbs']} g\n"
                    f"Fats: {analyzed_data['fats']} g"
                )
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("AI Error", f"Could not analyze meal.\n\n{e}")

    # nested function to save the meal to the database, with validation for empty fields
    # and ensuring the meal has been analyzed before saving.

    def save_meal():
        meal_text = meal_entry.get().strip()
        selected_date = meal_date_entry.get().strip()

        if current_user_id is None:
            messagebox.showerror("Error", "No user is logged in.")
            return

        if meal_text == "":
            messagebox.showerror("Error", "Please enter a meal.")
            return

        if selected_date == "":
            messagebox.showerror("Error", "Please enter a date.")
            return

        if not analyzed_data:
            messagebox.showerror("Error", "Please analyze the meal first.")
            return

        cursor.execute("""
            INSERT INTO meals (user_id, meal_name, calories, protein, carbs, fats, meal_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            current_user_id,
            meal_text,
            analyzed_data["calories"],
            analyzed_data["protein"],
            analyzed_data["carbs"],
            analyzed_data["fats"],
            selected_date
        ))

        conn.commit()
        messagebox.showinfo("Saved", "Meal saved successfully!")
        meal_window.destroy()

    analyze_button = tk.Button(
        meal_window,
        text="Analyze Meal",
        font=("Arial", 12),
        width=18,
        height=2,
        command=analyze_meal
    )
    analyze_button.pack(pady=10)

    save_button = tk.Button(
        meal_window,
        text="Save Meal",
        font=("Arial", 12),
        width=18,
        height=2,
        command=save_meal
    )
    save_button.pack(pady=10)


#------------------View Progress-----------------
def view_progress():
    if current_user_id is None:
        messagebox.showerror("Error", "No user is logged in.")
        return

    progress_window = tk.Toplevel(root)
    progress_window.title("View Progress")
    progress_window.geometry("450x550")
    progress_window.configure(bg="white")

    tk.Label(
        progress_window,
        text="Nutrition Progress",
        font=("Arial", 16, "bold"),
        bg="white"
    ).pack(pady=15)

    tk.Label(
        progress_window,
        text="Enter date (YYYY-MM-DD):",
        font=("Arial", 11),
        bg="white"
    ).pack(pady=5)

    date_entry = tk.Entry(progress_window, font=("Arial", 11), width=20)
    date_entry.pack(pady=5)
    date_entry.insert(0, "2026-04-26")

    results_frame = tk.Frame(progress_window, bg="white")
    results_frame.pack(fill="both", expand=True)
    # nested function to load the meal data for the selected date, calculate totals,
    # and display the results in the progress window. It also shows a list of meals logged for that date.
    def load_progress():
        selected_date = date_entry.get().strip()

        cursor.execute("""
            SELECT meal_name, calories, protein, carbs, fats
            FROM meals
            WHERE user_id = ? AND meal_date = ?
        """, (current_user_id, selected_date))

        meals = cursor.fetchall()

        for widget in results_frame.winfo_children():
            widget.destroy()

        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0

        for meal in meals:
            meal_name, calories, protein, carbs, fats = meal
            total_calories += calories
            total_protein += protein
            total_carbs += carbs
            total_fats += fats

        tk.Label(
            results_frame,
            text=(
                f"Calories Eaten: {total_calories}\n"
                f"Protein: {total_protein} g\n"
                f"Carbs: {total_carbs} g\n"
                f"Fats: {total_fats} g\n"
                f"Meals Logged: {len(meals)}"
            ),
            font=("Arial", 12),
            bg="white",
            justify="left"
        ).pack(pady=15)

        tk.Label(
            results_frame,
            text="Recent Meals",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(pady=10)

        if not meals:
            tk.Label(
                results_frame,
                text="No meals logged for this date.",
                font=("Arial", 11),
                bg="white",
                fg="gray"
            ).pack(pady=10)
        else:
            for meal in meals:
                meal_name, calories, protein, carbs, fats = meal

                tk.Label(
                    results_frame,
                    text=(
                        f"{meal_name}\n"
                        f"{calories} calories | "
                        f"P: {protein}g | C: {carbs}g | F: {fats}g"
                    ),
                    font=("Arial", 10),
                    bg="white",
                    justify="left",
                    wraplength=380
                ).pack(pady=6)

    tk.Button(
        progress_window,
        text="Load Results for Date Entered:",
        font=("Arial", 11),
        command=load_progress
    ).pack(pady=10)

    tk.Button(
    progress_window,
    text="Show Calorie Graph",
    font=("Arial", 11),
    command=view_calorie_graph
    ).pack(pady=5)

    load_progress()

#------------Workouts progress-----------------

def view_workout_graph():
    if current_user_id is None:
        messagebox.showerror("Error", "No user is logged in.")
        return

    cursor.execute("""
        SELECT workout_date, SUM(calories_burned)
        FROM workouts
        WHERE user_id = ?
        GROUP BY workout_date
        ORDER BY workout_date
    """, (current_user_id,))

    data = cursor.fetchall()

    if not data:
        messagebox.showinfo("No Data", "No workout data available to graph.")
        return

    dates = [row[0] for row in data]
    calories = [row[1] for row in data]

    plt.figure(figsize=(8, 5))
    plt.plot(dates, calories, marker="o")
    plt.title("Calories Burned Over Time")
    plt.xlabel("Date")
    plt.ylabel("Calories Burned")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def view_workout_progress():
    if current_user_id is None:
        messagebox.showerror("Error", "No user is logged in.")
        return

    progress_window = tk.Toplevel(root)
    progress_window.title("Workout Progress")
    progress_window.geometry("450x500")
    progress_window.configure(bg="white")

    tk.Label(
        progress_window,
        text="Workout Progress",
        font=("Arial", 16, "bold"),
        bg="white"
    ).pack(pady=15)

    tk.Label(
        progress_window,
        text="Enter date (YYYY-MM-DD):",
        font=("Arial", 11),
        bg="white"
    ).pack(pady=5)

    date_entry = tk.Entry(progress_window, font=("Arial", 11), width=20)
    date_entry.pack(pady=5)

    from datetime import date
    date_entry.insert(0, str(date.today()))

    results_frame = tk.Frame(progress_window, bg="white")
    results_frame.pack(fill="both", expand=True)

    def load_workouts():
        selected_date = date_entry.get().strip()

        cursor.execute("""
            SELECT workout_type, duration, calories_burned
            FROM workouts
            WHERE user_id = ? AND workout_date = ?
        """, (current_user_id, selected_date))

        workouts = cursor.fetchall()

        for widget in results_frame.winfo_children():
            widget.destroy()

        total_duration = 0
        total_calories = 0

        for workout in workouts:
            w_type, duration, calories = workout
            total_duration += duration
            total_calories += calories

        tk.Label(
            results_frame,
            text=(
                f"Total Minutes: {total_duration}\n"
                f"Calories Burned: {total_calories}\n"
                f"Workouts Logged: {len(workouts)}"
            ),
            font=("Arial", 12),
            bg="white",
            justify="left"
        ).pack(pady=15)

        if not workouts:
            tk.Label(
                results_frame,
                text="No workouts logged for this date.",
                font=("Arial", 11),
                bg="white",
                fg="gray"
            ).pack(pady=10)
        else:
            for workout in workouts:
                w_type, duration, calories = workout

                tk.Label(
                    results_frame,
                    text=f"{w_type} | {duration} min | {calories} cal",
                    font=("Arial", 10),
                    bg="white"
                ).pack(pady=5)

    tk.Button(
        progress_window,
        text="Load Workouts",
        font=("Arial", 11),
        command=load_workouts
    ).pack(pady=10)

    tk.Button(
    progress_window,
    text="Show Workout Graph",
    font=("Arial", 11),
    command=view_workout_graph
    ).pack(pady=5)



# Main window
root = tk.Tk()
root.title("Fit & Fuel")
root.geometry("400x510")
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


#CREATE account button
create_account_button = tk.Button(
    login_frame,
    text="Create Account",
    font=("Arial", 12),
    width=20,
    height=2,
    command=open_create_account
)
create_account_button.pack(pady=10, fill="x")

login_frame.pack(fill="both", expand=True)


#-----------------Keeping track of calories ate in a day-----------------
def view_today_food():
    if current_user_id is None:
        messagebox.showerror("Error", "No user is logged in.")
        return

    food_window = tk.Toplevel(root)
    food_window.title("Today's Food")
    food_window.geometry("420x450")

    tk.Label(
        food_window,
        text="Food Eaten Today",
        font=("Arial", 16, "bold")
    ).pack(pady=15)

    cursor.execute("""
        SELECT meal_name, calories, protein, carbs, fats
        FROM meals
        WHERE user_id = ? AND meal_date = date('now')
    """, (current_user_id,))

    meals = cursor.fetchall()

    if not meals:
        tk.Label(
            food_window,
            text="No meals logged today.",
            font=("Arial", 11)
        ).pack(pady=20)
        return

    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fats = 0

    for meal in meals:
        meal_name, calories, protein, carbs, fats = meal

        total_calories += calories
        total_protein += protein
        total_carbs += carbs
        total_fats += fats

        tk.Label(
            food_window,
            text=f"{meal_name}\nCalories: {calories} | Protein: {protein}g | Carbs: {carbs}g | Fats: {fats}g",
            font=("Arial", 10),
            justify="left",
            wraplength=360
        ).pack(pady=8)

    tk.Label(
        food_window,
        text=(
            f"\nDaily Total\n"
            f"Calories: {total_calories}\n"
            f"Protein: {total_protein}g\n"
            f"Carbs: {total_carbs}g\n"
            f"Fats: {total_fats}g"
        ),
        font=("Arial", 12, "bold"),
        justify="left"
    ).pack(pady=15)

#-----------------Calorie graph-----------------
def view_calorie_graph():
    if current_user_id is None:
        messagebox.showerror("Error", "No user is logged in.")
        return

    cursor.execute("""
        SELECT meal_date, SUM(calories)
        FROM meals
        WHERE user_id = ?
        GROUP BY meal_date
        ORDER BY meal_date
    """, (current_user_id,))

    data = cursor.fetchall()

    if not data:
        messagebox.showinfo("No Data", "No meal data available to graph.")
        return

    dates = [row[0] for row in data]
    calories = [row[1] for row in data]

    plt.figure(figsize=(8, 5))
    plt.plot(dates, calories, marker="o")
    plt.title("Calories Eaten Over Time")
    plt.xlabel("Date")
    plt.ylabel("Calories")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# ---------------- DASHBOARD FRAME ----------------
def logout():
    global current_user_id

    current_user_id = None

    dashboard_frame.pack_forget()
    login_frame.pack(fill="both", expand=True)

    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)



dashboard_frame = tk.Frame(root, bg="white")

dashboard_title = tk.Label(
    dashboard_frame,
    text="Fit & Fuel Dashboard",
    font=("Arial", 18, "bold"),
    bg="white"
)
dashboard_title.pack(pady=30)

profile_button = tk.Button(
    dashboard_frame,
    text="Profile",
    font=("Arial", 12),
    width=20,
    height=2,
    command=open_profile
)
profile_button.pack(pady=10)

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

#View Workout Progress Button
workout_progress_button = tk.Button(
    dashboard_frame,
    text="Workout Progress",
    font=("Arial", 12),
    width=20,
    height=2,
    command=view_workout_progress
)
workout_progress_button.pack(pady=10)

today_food_button = tk.Button(
    dashboard_frame,
    text="Today's Food",
    font=("Arial", 12),
    width=20,
    height=2,
    command=view_today_food
)

logout_button = tk.Button(
    dashboard_frame,
    text="Logout",
    font=("Arial", 12),
    width=20,
    height=2,
    command=logout
)
logout_button.pack(pady=10)
today_food_button.pack(pady=10)

root.mainloop()