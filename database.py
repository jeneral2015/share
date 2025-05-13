import sqlite3
import threading
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="expenses.db"):
        self.lock = threading.Lock()
        self.db_name = db_name
        self.conn = None
        self.reconnect()

    def reconnect(self):
        """إعادة الاتصال بقاعدة البيانات"""
        try:
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON;")  # تفعيل المفاتيح الأجنبية
            self.create_tables()
        except Exception as e:
            print(f"فشل إعادة الاتصال: {e}")

    def create_tables(self):
        """إنشاء الجداول إذا لم تكن موجودة"""
        try:
            cursor = self.conn.cursor()
            self.conn.execute("BEGIN TRANSACTION")

            # جدول المصاريف
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT,
                    quantity INTEGER,
                    price REAL,
                    total_price REAL,
                    consumption INTEGER DEFAULT 0,
                    remaining INTEGER DEFAULT 0,
                    is_miscellaneous INTEGER DEFAULT 0,
                    is_drink INTEGER DEFAULT 0,
                    date TEXT
                )
            """)

            # جدول المشتركين
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    rank TEXT,
                    contribution REAL,
                    total_due REAL DEFAULT 0,
                    date TEXT
                )
            """)

            # جدول سجلات الوجبات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meal_records (
                    meal_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meal_type TEXT,
                    date TEXT,
                    member_id INTEGER,
                    final_cost REAL,
                    FOREIGN KEY (member_id) REFERENCES members(member_id)
                )
            """)

            # جدول سجلات المشروبات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drink_records (
                    drink_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    drink_name TEXT,
                    member_id INTEGER,
                    quantity INTEGER,
                    total_cost REAL,
                    FOREIGN KEY (member_id) REFERENCES members(member_id)
                )
            """)

            # جدول المصاريف النثرية العام
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS miscellaneous_expenses (
                    misc_expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    amount REAL,
                    meal_type TEXT,
                    meal_record_id INTEGER,
                    member_id INTEGER,
                    FOREIGN KEY (meal_record_id) REFERENCES meal_records(meal_record_id),
                    FOREIGN KEY (member_id) REFERENCES members(member_id)
                )
            """)

            # جدول النثريات الخاص بالمشتركين
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS miscellaneous_contributions (
                    misc_contribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER,
                    misc_amount REAL,
                    meal_count INTEGER DEFAULT 0,
                    distribution_date TEXT,
                    FOREIGN KEY (member_id) REFERENCES members(member_id)
                )
            """)

            # جدول مفاتيح الأرشيف
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archive_keys (
                    archive_key_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    archive_name TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    archived_at TEXT
                )
            """)

            # جداول الأرشيف
            self._create_archive_tables(cursor)

            self.conn.commit()
            self._run_migrations(cursor)

        except Exception as e:
            self.conn.rollback()
            print(f"حدث خطأ أثناء إنشاء الجداول أو التعديلات: {e}")
        finally:
            pass

    def _create_archive_tables(self, cursor):
        """إنشاء جداول الأرشيف"""
        # أرشيف المصاريف
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses_archive (
                expense_id INTEGER,
                item_name TEXT,
                quantity INTEGER,
                price REAL,
                total_price REAL,
                consumption INTEGER DEFAULT 0,
                remaining INTEGER DEFAULT 0,
                is_miscellaneous INTEGER DEFAULT 0,
                is_drink INTEGER DEFAULT 0,
                date TEXT,
                archive_key_id INTEGER,
                PRIMARY KEY (expense_id, archive_key_id),
                FOREIGN KEY (archive_key_id) REFERENCES archive_keys(archive_key_id)
            )
        """)

        # أرشيف المشتركين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members_archive (
                member_id INTEGER,
                name TEXT,
                rank TEXT,
                contribution REAL,
                total_due REAL,
                date TEXT,
                archive_key_id INTEGER,
                PRIMARY KEY (member_id, archive_key_id),
                FOREIGN KEY (archive_key_id) REFERENCES archive_keys(archive_key_id)
            )
        """)

        # أرشيف سجلات الوجبات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_records_archive (
                meal_record_id INTEGER,
                meal_type TEXT,
                date TEXT,
                member_id INTEGER,
                final_cost REAL,
                archive_key_id INTEGER,
                PRIMARY KEY (meal_record_id, archive_key_id),
                FOREIGN KEY (archive_key_id) REFERENCES archive_keys(archive_key_id)
            )
        """)

        # أرشيف سجلات المشروبات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drink_records_archive (
                drink_record_id INTEGER,
                date TEXT,
                drink_name TEXT,
                member_id INTEGER,
                quantity INTEGER,
                total_cost REAL,
                archive_key_id INTEGER,
                PRIMARY KEY (drink_record_id, archive_key_id),
                FOREIGN KEY (archive_key_id) REFERENCES archive_keys(archive_key_id)
            )
        """)

        # أرشيف المصاريف النثرية
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS miscellaneous_expenses_archive (
                misc_expense_id INTEGER,
                date TEXT,
                amount REAL,
                meal_type TEXT,
                meal_record_id INTEGER,
                archive_key_id INTEGER,
                PRIMARY KEY (misc_expense_id, archive_key_id),
                FOREIGN KEY (archive_key_id) REFERENCES archive_keys(archive_key_id)
            )
        """)

        # أرشيف توزيعات النثريات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS miscellaneous_contributions_archive (
                misc_contribution_id INTEGER,
                member_id INTEGER,
                misc_amount REAL,
                meal_count INTEGER,
                distribution_date TEXT,
                archive_key_id INTEGER,
                PRIMARY KEY (misc_contribution_id, archive_key_id),
                FOREIGN KEY (archive_key_id) REFERENCES archive_keys(archive_key_id)
            )
        """)

    def _run_migrations(self, cursor):
        """التعديلات على الجداول (Migrations)"""
        try:
            # تعديل جدول miscellaneous_expenses
            cursor.execute("PRAGMA table_info(miscellaneous_expenses)")
            cols = [col[1] for col in cursor.fetchall()]
            if "meal_record_id" not in cols:
                cursor.execute("ALTER TABLE miscellaneous_expenses ADD COLUMN meal_record_id INTEGER")
            if "member_id" not in cols:
                cursor.execute("ALTER TABLE miscellaneous_expenses ADD COLUMN member_id INTEGER REFERENCES members(member_id)")

            # تعديل جدول miscellaneous_contributions
            cursor.execute("PRAGMA table_info(miscellaneous_contributions)")
            cols = [col[1] for col in cursor.fetchall()]
            if "meal_count" not in cols:
                cursor.execute("ALTER TABLE miscellaneous_contributions ADD COLUMN meal_count INTEGER DEFAULT 0")
            if "distribution_date" not in cols:
                cursor.execute("ALTER TABLE miscellaneous_contributions ADD COLUMN distribution_date TEXT")

            self.conn.commit()
        except Exception as e:
            print(f"حدث خطأ أثناء تنفيذ التعديلات: {e}")

    def execute_query(self, query, params=()):
        """تنفيذ استعلام مع قفل للسلامة في البيئات متعددة الخيوط"""
        with self.lock:
            try:
                if not self.conn:
                    self.reconnect()
                cursor = self.conn.cursor()
                cursor.execute(query, params)
                self.conn.commit()
                return cursor
            except Exception as e:
                print(f"حدث خطأ أثناء تنفيذ الاستعلام: {e}")
                return None

    def fetch_all(self, query, params=()):
        """استرجاع جميع البيانات من قاعدة البيانات"""
        try:
            if not self.conn:
                self.reconnect()
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"حدث خطأ أثناء استرجاع البيانات: {e}")
            return []

    def close_connection(self):
        """إغلاق اتصال قاعدة البيانات"""
        if self.conn:
            self.conn.close()
