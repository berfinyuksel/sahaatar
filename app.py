import psycopg2

# Connect to the database
conn = psycopg2.connect(
    host="your_host",
    database="your_database",
    user="your_user",
    password="your_password"
)

# Create a cursor object
cur = conn.cursor()

# Execute a query
cur.execute("SELECT * FROM your_table")

# Fetch the results
results = cur.fetchall()

print("Heartaches!")
# Print the results
for row in results:
    print(row)

# Close the cursor and connection
cur.close()
conn.close()

