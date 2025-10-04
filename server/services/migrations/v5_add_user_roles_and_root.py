# server/services/migrations/v5_add_user_roles_and_root.py

from . import Migration
import sqlite3
import secrets
import string
from services.auth_service import get_password_hash

class V5AddUserRolesAndRoot(Migration):
    version = 5
    description = "Insert root user if not exists"

    def up(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()
        
        root_email = "sulfitry@icloud.com"
        root_username = "root"
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (root_email,))
        if cursor.fetchone() is None:
            # Membuat password acak 32 karakter. Tidak perlu lagi khawatir tentang batas byte.
            alphabet = string.ascii_letters + string.digits
            root_password = ''.join(secrets.choice(alphabet) for i in range(32))

            # Langsung hash password.
            hashed_password = get_password_hash(root_password)

            cursor.execute(
                """
                INSERT INTO users (username, email, hashed_password, role)
                VALUES (?, ?, ?, ?)
                """,
                (root_username, root_email, hashed_password, 'admin')
            )
            conn.commit()
            
            print("\n" + "="*80)
            print("✨ ROOT USER CREATED ✨")
            print(f"  Username: {root_username}")
            print(f"  Email:    {root_email}")
            print(f"  Password: {root_password}")
            print("\n⚠️ Harap simpan password ini di tempat yang aman. Ini hanya akan ditampilkan sekali.")
            print("="*80 + "\n")
        else:
            print("Root user with email 'sulfitry@icloud.com' already exists. Skipping creation.")

    def down(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email = ?", ("sulfitry@icloud.com",))
        conn.commit()
        print("Root user removed.")