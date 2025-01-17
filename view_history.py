from tabulate import tabulate
import sqlite3

# Connect to the database
conn = sqlite3.connect("history.db")
cursor = conn.cursor()

# Fetch the data
cursor.execute("SELECT * FROM history")
rows = cursor.fetchall()

# Define column headers
headers = ["ID", "Amount", "From Currency", "To Currency", "Converted Amount", "Date"]

# Print the data in tabular format
print(tabulate(rows, headers, tablefmt="grid"))

# Close the connection
conn.close()
