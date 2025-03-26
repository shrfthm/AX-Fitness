import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_database():
    try:
        # Connect to MySQL server
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password=''  # Add your MySQL password here if you have one
        )
        
        cursor = connection.cursor()
        
        # Drop database if exists and create new one
        cursor.execute("DROP DATABASE IF EXISTS gym_system")
        cursor.execute("CREATE DATABASE gym_system")
        print("Database 'gym_system' created successfully!")
        
        # Switch to gym_system database
        cursor.execute("USE gym_system")
        
        # Create User table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128),
                name VARCHAR(100) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create Schedule table with status field
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                age INT NOT NULL,
                address VARCHAR(200) NOT NULL,
                schedule_date DATE NOT NULL,
                schedule_time TIME NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)
        
        # Create HealthDeclaration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_declaration (
                id INT AUTO_INCREMENT PRIMARY KEY,
                schedule_id INT NOT NULL,
                has_fever BOOLEAN DEFAULT FALSE,
                has_cough BOOLEAN DEFAULT FALSE,
                has_cold BOOLEAN DEFAULT FALSE,
                has_sore_throat BOOLEAN DEFAULT FALSE,
                has_breathing_problems BOOLEAN DEFAULT FALSE,
                has_diarrhea BOOLEAN DEFAULT FALSE,
                has_body_pains BOOLEAN DEFAULT FALSE,
                has_travelled BOOLEAN DEFAULT FALSE,
                has_contact_with_covid BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (schedule_id) REFERENCES schedule(id)
            )
        """)
        
        # Create admin user if not exists
        admin_email = 'admin@gym.com'
        cursor.execute("SELECT * FROM user WHERE email = %s", (admin_email,))
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            admin_password = 'admin123'  # Change this to your desired admin password
            password_hash = generate_password_hash(admin_password)
            
            cursor.execute("""
                INSERT INTO user (email, password_hash, name, is_admin)
                VALUES (%s, %s, %s, %s)
            """, (admin_email, password_hash, 'Admin User', True))
            
            print(f"Admin user created successfully!")
            print(f"Email: {admin_email}")
            print(f"Password: {admin_password}")
        
        connection.commit()
        print("All tables created successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    create_database()
    print("\nDatabase initialization completed!")
    print("You can now run app.py") 