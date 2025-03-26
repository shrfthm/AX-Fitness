import pymysql

def check_database():
    try:
        # Connect to MySQL server
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',  # Add your MySQL password here if you have one
            database='gym_system'
        )
        
        cursor = connection.cursor()
        
        # Show all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("Connected to database successfully!")
        print("\nAvailable tables:")
        for table in tables:
            print(f"- {table[0]}")
            
            # Show table structure
            cursor.execute(f"DESCRIBE {table[0]}")
            columns = cursor.fetchall()
            print("  Columns:")
            for column in columns:
                print(f"    - {column[0]} ({column[1]})")
            print()
            
        # Check if admin user exists
        cursor.execute("SELECT email, name, is_admin FROM user WHERE is_admin = 1")
        admin = cursor.fetchone()
        if admin:
            print("\nAdmin user found:")
            print(f"Email: {admin[0]}")
            print(f"Name: {admin[1]}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    check_database() 