
import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "jarvis.db"
SCHEMA_STATEMENTS = (
    "CREATE TABLE IF NOT EXISTS sys_command("
    "id INTEGER PRIMARY KEY, "
    "name VARCHAR(100), "
    "path VARCHAR(1000)"
    ")",
    "CREATE TABLE IF NOT EXISTS web_command("
    "id INTEGER PRIMARY KEY, "
    "name VARCHAR(100), "
    "url VARCHAR(1000)"
    ")",
    "CREATE TABLE IF NOT EXISTS contacts("
    "id INTEGER PRIMARY KEY, "
    "name VARCHAR(200), "
    "Phone VARCHAR(255), "
    "email VARCHAR(255) NULL"
    ")",
)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for query in SCHEMA_STATEMENTS:
    cursor.execute(query)

conn.commit()


# query = "INSERT INTO sys_command VALUES (null,'obs', 'C:\\Program Files\\obs-studio\\bin\\obs64.exe')"
# cursor.execute(query)
# conn.commit()

# query = "DELETE FROM sys_command WHERE name='obs'"
# cursor.execute(query)
# conn.commit()

# testing module
# app_name = "obs"
# cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (app_name,))
# results = cursor.fetchall()
# print(results[0][0])




# cursor.execute("DROP TABLE IF EXISTS contacts;")
# conn.commit()
# cursor.execute('''CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, name VARCHAR(200), Phone VARCHAR(255), email VARCHAR(255) NULL)''') 

 
# desired_columns_indices = [0, 20]
 
# with open('contacts.csv', 'r', encoding='utf-8') as csvfile:
#     csvreader = csv.reader(csvfile)
#     for row in csvreader:
#         selected_data = [row[i] for i in desired_columns_indices]
#         cursor.execute(''' INSERT INTO contacts (id, 'name', 'Phone') VALUES (null, ?,? );''', tuple(selected_data))

# # Commit changes and close connection
# conn.commit()
# conn.close()

# print("Data inserted successfully") 


# query = "INSERT INTO contacts VALUES (null,'pawan', '1234567890', 'null')"
# cursor.execute(query)
# conn.commit() 


# query = 'Ankit'
# query = query.strip().lower()  # Added parentheses to call the method

# cursor.execute("SELECT Phone FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", 
#                ('%' + query + '%', query + '%'))
# results = cursor.fetchall()
# print(results[0][0])
