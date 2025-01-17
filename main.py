import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import requests
from tkinter import PhotoImage
import os
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta

# Database setup
conn = sqlite3.connect("currency_converter.db")
cursor = conn.cursor()

# Create tables for users and conversion history
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    phone TEXT UNIQUE
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS conversion_history (
    id INTEGER PRIMARY KEY,
    username TEXT,
    phone TEXT,
    from_currency TEXT,
    to_currency TEXT,
    amount REAL,
    converted_amount REAL
)
""")
conn.commit()

# Global variable for the logged-in user
logged_in_user = {"username": None, "phone": None}

# Function to register a new user
def register_user():
    username = reg_username_entry.get()
    password = reg_password_entry.get()
    confirm_password = reg_confirm_password_entry.get()
    phone = reg_phone_entry.get()

    if not username or not password or not confirm_password or not phone:
        messagebox.showerror("Error", "All fields are required!")
        return

    if password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match!")
        return

    try:
        cursor.execute("INSERT INTO users (username, password, phone) VALUES (?, ?, ?)", 
                       (username, password, phone))
        conn.commit()
        messagebox.showinfo("Success", "Account created successfully!")
        register_window.destroy()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username or phone number already exists!")

# Function to login a user
def login_user():
    username = username_entry.get()
    password = password_entry.get()

    cursor.execute("SELECT phone FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()

    if result:
        logged_in_user["username"] = username
        logged_in_user["phone"] = result[0]
        messagebox.showinfo("Success", "Login successful!")
        root.destroy()  # Close the login window
        open_dashboard()
    else:
        messagebox.showerror("Error", "Invalid username or password!")

# Function to fetch the exchange rate
def get_exchange_rate(from_currency, to_currency):
    api_url = f"https://v6.exchangerate-api.com/v6/c2b49a5597e5f82d808446c0/latest/{from_currency}"
    try:
        response = requests.get(api_url)
        data = response.json()
        if response.status_code == 200:
            if to_currency == from_currency:
                return 1 # Return 1 if currencies are the same
            elif to_currency in data["conversion_rates"]:
                return data["conversion_rates"][to_currency]
        messagebox.showerror("Error", "Error fetching exchange rate data.")
        return None
    except requests.exceptions.RequestException:
        messagebox.showerror("Error", "Failed to connect to the exchange rate API.")
        return None

# Function to perform currency conversion
def perform_conversion():
    from_currency = from_currency_combobox.get()
    to_currency = to_currency_combobox.get()
    amount = amount_entry.get() 
    
    if not from_currency or not to_currency:
        messagebox.showerror("Error", "Please select both 'From' and 'To' currencies.")
        return

    if from_currency == to_currency:
        result_label.config(text=f"Converted Amount: {amount}")
        return

    try:
        amount = float(amount)
        exchange_rate = get_exchange_rate(from_currency, to_currency)

        if exchange_rate:
            converted_amount = amount * exchange_rate
            result_label.config(text=f"Converted Amount: {converted_amount:.2f}")

            # Save conversion to database
            cursor.execute("""
            INSERT INTO conversion_history (username, phone, from_currency, to_currency, amount, converted_amount)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (logged_in_user["username"], logged_in_user["phone"], from_currency, to_currency, amount, converted_amount))
            conn.commit()

            # Update conversion history table
            fetch_conversion_history()

    except ValueError:
        messagebox.showerror("Error", "Invalid amount entered!")

# Function to fetch and display conversion history
def fetch_conversion_history():
    cursor.execute("""
    SELECT from_currency, to_currency, amount, converted_amount 
    FROM conversion_history 
    WHERE username = ? AND phone = ?
    """, (logged_in_user["username"], logged_in_user["phone"]))
    rows = cursor.fetchall()

    for row in history_table.get_children():
        history_table.delete(row)

    for row in rows:
        history_table.insert("", "end", values=row)

# Open registration window
def open_register():
    global register_window, reg_username_entry, reg_password_entry, reg_confirm_password_entry, reg_phone_entry
    register_window = tk.Toplevel(root)
    register_window.title("Register")
    register_window.geometry("800x600")  # Set size of the register window
    register_window.configure(bg="#000000")  # Set background color to black

    # Load background image
    bg_image = Image.open("ER2.png")  # Replace with your image file path
    bg_image_resized = bg_image.resize((2200, 1600), Image.Resampling.LANCZOS)  # Resize to window size
    bg_image_tk = ImageTk.PhotoImage(bg_image_resized)

    # Create a canvas to hold the background image
    canvas = tk.Canvas(register_window, width=2200, height=1600)
    canvas.pack(fill="both", expand=True)

    # Place the background image on the canvas
    canvas.create_image(0, 0, anchor="nw", image=bg_image_tk)

    # Create a frame for the registration form and center it
    frame = tk.Frame(register_window, bg="#000000", width=600, height=300)
    frame.place(relx=0.5, rely=0.5, anchor="center")  # Center the frame in the middle
    frame.grid_propagate(False)  # Prevent the frame from resizing

    # Labels and Entry widgets for registration form
    label_font = ("Arial", 14)
    entry_font = ("Arial", 12)

    # Center the labels and entries
    tk.Label(frame, text="Username", font=label_font, bg="#000000", fg="#ccffff").grid(row=0, column=0, padx=20, pady=10, sticky="e")
    reg_username_entry = tk.Entry(frame, font=entry_font,bg="#000000",fg="#ccffff", width=30,insertbackground='white')
    reg_username_entry.grid(row=0, column=1, padx=20, pady=10, sticky="w")

    tk.Label(frame, text="Password", font=label_font, bg="#000000", fg="#ccffff").grid(row=1, column=0, padx=20, pady=10, sticky="e")
    reg_password_entry = tk.Entry(frame, show="*", font=entry_font,bg="#000000",fg="#ccffff", width=30,insertbackground='white')
    reg_password_entry.grid(row=1, column=1, padx=20, pady=10, sticky="w")

    tk.Label(frame, text="Confirm Password", font=label_font, bg="#000000", fg="#ccffff").grid(row=2, column=0, padx=20, pady=10, sticky="e")
    reg_confirm_password_entry = tk.Entry(frame, show="*", font=entry_font,bg="#000000",fg="#ccffff", width=30,insertbackground='white')
    reg_confirm_password_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")

    tk.Label(frame, text="Phone no.", font=label_font, bg="#000000", fg="#ccffff").grid(row=3, column=0, padx=20, pady=10, sticky="e")
    reg_phone_entry = tk.Entry(frame, font=entry_font,bg="#000000",fg="#ccffff", width=30,insertbackground='white')
    reg_phone_entry.grid(row=3, column=1, padx=20, pady=10, sticky="w")

    # Register button (with blue color as requested)
    tk.Button(frame, text="Register", font=("Arial", 14), bg="#2196F3", fg="white", width=15, height=1, command=register_user).grid(row=4, columnspan=2, pady=20)

    # Keep the image reference alive
    register_window.mainloop()

def logout_user(dashboard):
    global logged_in_user
    logged_in_user = {"username": None, "phone": None}  # Reset logged-in user
    dashboard.destroy()  # Close the dashboard
    messagebox.showinfo("Logout", "You have been successfully logged out!")  # Show logout message
    root.deiconify()
   

# Open dashboard
def open_dashboard():
    global from_currency_combobox, to_currency_combobox, amount_entry, result_label, history_table

    dashboard = tk.Toplevel()
    dashboard.title("Dashboard")
    dashboard.geometry("600x400")
    dashboard.configure(bg="#000000")
    logout_button = tk.Button(
        dashboard,
        text="Logout",
        font=("Arial", 12),
        bg="red",
        fg="white",
        command=lambda: logout_user(dashboard)
    )
    logout_button.place(relx=0.9, rely=0.03, anchor="center")  # Top-right corner placement

    

    tk.Label(dashboard, text=f"Welcome, {logged_in_user['username']}!", font=("Arial", 16),bg="#000000",fg="#ccffff").pack()

    tk.Label(dashboard, text="From Currency", font=("Arial", 14),bg="#000000",fg="#ccffff").pack()
    from_currency_combobox = ttk.Combobox(dashboard, values=["USD", "EUR", "GBP", "INR", "JPY", "AUD", "CAD", "CHF", "CNY", "MXN"], font=("Arial", 12))
    from_currency_combobox.pack()

    tk.Label(dashboard, text="To Currency", font=("Arial", 14),bg="#000000",fg="#ccffff").pack()
    to_currency_combobox = ttk.Combobox(dashboard, values=["USD", "EUR", "GBP", "INR", "JPY", "AUD", "CAD", "CHF", "CNY", "MXN"], font=("Arial", 12))
    to_currency_combobox.pack()

    tk.Label(dashboard, text="Amount", font=("Arial", 14),bg="#000000",fg="#ccffff").pack()
    amount_entry = tk.Entry(dashboard, font=("Arial", 12))
    amount_entry.pack()

    tk.Button(dashboard, text="Convert", font=("Arial", 14),bg="#2196F3",fg="#ffffff", command=perform_conversion).pack()

    result_label = tk.Label(dashboard, text="", font=("Arial", 14),bg="#000000",fg="#ccffff")
    result_label.pack()

    history_table = ttk.Treeview(dashboard, columns=("From", "To", "Amount", "Converted"), show="headings", height=6)
    history_table.heading("From", text="From Currency")
    history_table.heading("To", text="To Currency")
    history_table.heading("Amount", text="Amount")
    history_table.heading("Converted", text="Converted Amount")
    history_table.pack(fill="both", expand=True)


    fetch_conversion_history()

    # Add a button for visualizations
    viz_button = tk.Button(dashboard, text="Visualize Exchange Rates", font=("Arial", 14), bg="#2196F3", fg="#ffffff", command=open_visualization_window)
    viz_button.pack(pady=10)

def fetch_historical_rates(base_currency, target_currencies, days=365):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    data = {currency: [] for currency in target_currencies}
    dates = []
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"https://v6.exchangerate-api.com/v6/c2b49a5597e5f82d808446c0/history/{base_currency}/{date_str}"
        response = requests.get(url)
        if response.status_code == 200:
            rates = response.json()['conversion_rates']
            for currency in target_currencies:
                if currency in rates:
                    data[currency].append(rates[currency])
                else:
                    data[currency].append(None)
            dates.append(date_str)
        current_date += timedelta(days=1)
    
    return data, dates

def plot_exchange_rate_trends(base_currency, target_currencies):
    data, dates = fetch_historical_rates(base_currency, target_currencies)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    for currency, rates in data.items():
        valid_rates = [rate for rate in rates if rate is not None]
        valid_dates = [datetime.strptime(date, "%Y-%m-%d") for date, rate in zip(dates, rates) if rate is not None]
        ax.plot(valid_dates, valid_rates, label=currency, marker='', linewidth=2)
    
    ax.set_title(f"Exchange Rate Trends (Base: {base_currency}) - Past Year", fontsize=16)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Exchange Rate", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Format x-axis to show months
    ax.xaxis.set_major_locator(plt.MonthLocator())
    ax.xaxis.set_major_formatter(plt.DateFormatter('%b %Y'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add some padding to the plot
    plt.tight_layout()
    
    return fig

def plot_currency_comparison(base_currency, target_currencies):
    url = f"https://v6.exchangerate-api.com/v6/c2b49a5597e5f82d808446c0/latest/{base_currency}"
    response = requests.get(url)
    if response.status_code == 200:
        rates = response.json()['conversion_rates']
        filtered_rates = {currency: rates[currency] for currency in target_currencies if currency in rates}
    else:
        messagebox.showerror("Error", "Failed to fetch latest exchange rates.")
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    currencies = list(filtered_rates.keys())
    values = list(filtered_rates.values())
    bars = ax.bar(currencies, values, color='skyblue', edgecolor='navy')
    
    ax.set_title(f"Currency Comparison (Base: {base_currency})")
    ax.set_ylabel("Exchange Rate")
    ax.set_ylim(0, max(values) * 1.1)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.4f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    
    return fig

def open_visualization_window():
    viz_window = tk.Toplevel()
    viz_window.title("Exchange Rate Visualizations")
    viz_window.geometry("1200x800")
    
    notebook = ttk.Notebook(viz_window)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    trends_frame = ttk.Frame(notebook)
    comparison_frame = ttk.Frame(notebook)
    
    notebook.add(trends_frame, text="Exchange Rate Trends (Past Year)")
    notebook.add(comparison_frame, text="Currency Comparison")
    
    base_currency = from_currency_combobox.get() or "USD"
    target_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"]
    if base_currency in target_currencies:
        target_currencies.remove(base_currency)
    
    # Exchange Rate Trends
    trends_fig = plot_exchange_rate_trends(base_currency, target_currencies)
    trends_canvas = FigureCanvasTkAgg(trends_fig, master=trends_frame)
    trends_canvas.draw()
    trends_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Currency Comparison
    comparison_fig = plot_currency_comparison(base_currency, target_currencies)
    if comparison_fig:
        comparison_canvas = FigureCanvasTkAgg(comparison_fig, master=comparison_frame)
        comparison_canvas.draw()
        comparison_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)



# Login window

# Define your login_user and open_register functions here...

root = tk.Tk()
root.title("Login")
root.geometry("800x600")
root.configure(bg="#000000")  # Make sure window has a black background

bg_image = Image.open("ER1.png")  # Replace with your image file path

# Resize the image manually if needed (e.g., setting to 800x600)
bg_image_resized = bg_image.resize((2200, 1600), Image.Resampling.LANCZOS)  # Manually set the size to fit the window
bg_image_tk = ImageTk.PhotoImage(bg_image_resized)

# Create a label for the background image and place it
canvas = tk.Canvas(root, width=800, height=600)
canvas.pack(fill="both", expand=True)

# Place the background image on the canvas
canvas.create_image(0, 0, anchor="nw", image=bg_image_tk)

# Draw text directly on the image
canvas.create_text(650, 400, text="Currency", font=("Arial", 120, "bold"), fill="#ccffff")
canvas.create_text(650, 600, text="Converter", font=("Arial", 120, "bold"), fill="#ccffff")



# Create a frame for login and register forms with transparent background
frame = tk.Frame(root, bg="#000000", width=600, height=575)
frame.place(relx=0.75, rely=0.5, anchor="center")
frame.grid_propagate(False)

header_label = tk.Label(frame, text="Login", font=("Arial", 20, "bold"), bg="#000000", fg="#ccffff")
header_label.pack(pady=20)

username_label = tk.Label(frame, text="Username", font=("Arial", 12), bg="#000000", fg="#ccffff")
username_label.pack(anchor="w", padx=40, pady=(10, 0))
username_entry = tk.Entry(frame, font=("Arial", 14),bg="#000000",fg="#ccffff", width=30,insertbackground='white')
username_entry.pack(padx=40, pady=5)

password_label = tk.Label(frame, text="Password", font=("Arial", 12), bg="#000000", fg="#ccffff")
password_label.pack(anchor="w", padx=40, pady=(10, 0))
password_entry = tk.Entry(frame, show="*", font=("Arial", 14),bg="#000000",fg="#ccffff", width=30,insertbackground='white')
password_entry.pack(padx=40, pady=5)

login_button = tk.Button(frame, text="Login", font=("Arial", 14), bg="#4CAF50", fg="white", width=20, height=1, command=login_user)
login_button.pack(pady=(20, 10))

register_button = tk.Button(frame, text="Register", font=("Arial", 14), bg="#2196F3", fg="white", width=20, height=1, command=open_register)
register_button.pack()

#currency_text_label = tk.Label(root, text="Currency", font=("Arial", 100, "bold"), fg="#0099FF", bg="#000000")
#currency_text_label.place(relx=0.3, rely=0.4, anchor="center")

#currency_text_label = tk.Label(root, text="Converter", font=("Arial", 100, "bold"), fg="#0099FF", bg="#000000")
#currency_text_label.place(relx=0.3, rely=0.575, anchor="center")

root.mainloop()
