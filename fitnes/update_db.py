import pymysql

def update_database():
    try:
        # Connect to MySQL server
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',  # Add your MySQL password here if you have one
            database='gym_system'
        )
        
        cursor = connection.cursor()
        
        # Add updated_at column to schedule table if it doesn't exist
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns 
            WHERE table_schema = 'gym_system'
            AND table_name = 'schedule'
            AND column_name = 'updated_at'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("Adding updated_at column to schedule table...")
            cursor.execute("""
                ALTER TABLE schedule
                ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            """)
            print("Column added successfully!")
        else:
            print("updated_at column already exists!")
        
        connection.commit()
        print("\nDatabase update completed!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    update_database() 