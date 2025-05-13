import flet as ft
from datetime import datetime
import logging

class DistributeMiscellaneous:
    def __init__(self, page, db):
        self.page = page
        self.db = db

    def show_confirmation(self):
        """عرض نافذة التأكيد قبل التوزيع"""
        def on_confirm(e):
            self.page.dialog.open = False
            self.page.update()
            self._confirm_distribution()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("توزيع النثريات"),
            content=ft.Text("سيتم توزيع النثريات، هل تريد الاستمرار؟"),
            actions=[
                ft.TextButton("نعم", on_click=on_confirm),
                ft.TextButton("لا", on_click=self.close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def _confirm_distribution(self):
        """تنفيذ التوزيع مع التعامل مع الأخطاء"""
        try:
            success, archive_key_id = self._distribute_and_archive_miscellaneous()
            if success:
                self.show_snackbar("تم توزيع النثريات والأرشفة بنجاح!")
            else:
                self.show_snackbar("فشل توزيع النثريات.")
        except Exception as e:
            logging.error(f"Error in distribution: {e}", exc_info=True)
            self.show_snackbar(f"خطأ أثناء التوزيع: {str(e)}")

    def _distribute_and_archive_miscellaneous(self):
        """الوظيفة الأساسية لتوزيع النثريات وأرشفتها"""
        try:
            with self.db.conn:
                cursor = self.db.conn.cursor()

                # 1. جلب النثريات (miscellaneous) من expenses
                cursor.execute(
                    "SELECT expense_id, total_price FROM expenses WHERE is_miscellaneous = 1"
                )
                misc_expenses = cursor.fetchall()
                if not misc_expenses:
                    self.show_snackbar("لا توجد أصناف نثريات للتوزيع!")
                    return False, None

                total_misc_value = sum(item[1] for item in misc_expenses)

                # 2. جلب عدد الوجبات لكل مشترك دفعة واحدة
                cursor.execute(
                    "SELECT member_id, COUNT(*) as meal_count FROM meal_records GROUP BY member_id"
                )
                meal_counts = cursor.fetchall()
                if not meal_counts:
                    self.show_snackbar("لا توجد سجلات وجبات لتوزيع النثريات!")
                    return False, None

                total_meals = sum(count for _, count in meal_counts)

                # 3. حساب تكلفة النثريات لكل وجبة
                misc_cost_per_meal = total_misc_value / total_meals

                # 4. تحديث كل مشترك وتسجيل التوزيع في جدول contributions
                distribution_date = datetime.now().strftime("%Y-%m-%d")
                for member_id, meal_count in meal_counts:
                    amount = meal_count * misc_cost_per_meal
                    # تحديث الدين في جدول members
                    cursor.execute(
                        "UPDATE members SET total_due = total_due + ? WHERE member_id = ?",
                        (amount, member_id)
                    )
                    # تسجيل التوزيع
                    cursor.execute(
                        "INSERT INTO miscellaneous_contributions (member_id, misc_amount, meal_count, distribution_date) VALUES (?, ?, ?, ?)",
                        (member_id, amount, meal_count, distribution_date)
                    )

                # 5. الحصول على مفتاح الأرشفة
                first_date = self.get_first_transaction_date() or distribution_date
                archive_key_id = self._get_or_create_archive_key(cursor, first_date)
                if not archive_key_id:
                    raise Exception("Failed to get or create archive key.")

                # 6. أرشفة توزيعات النثريات
                cursor.execute(
                    "SELECT misc_contribution_id FROM miscellaneous_contributions WHERE distribution_date = ?",
                    (distribution_date,)
                )
                new_ids = [row[0] for row in cursor.fetchall()]
                if new_ids:
                    ph = ",".join("?" * len(new_ids))
                    # حذف أي أرشيف سابق لنفس الدفعة
                    cursor.execute(
                        f"DELETE FROM miscellaneous_contributions_archive WHERE misc_contribution_id IN ({ph}) AND archive_key_id = ?",
                        (*new_ids, archive_key_id)
                    )
                    # إدراج في جدول الأرشيف
                    cursor.execute(
                        f"INSERT OR REPLACE INTO miscellaneous_contributions_archive "
                        "(misc_contribution_id, member_id, misc_amount, meal_count, distribution_date, archive_key_id) "
                        f"SELECT misc_contribution_id, member_id, misc_amount, meal_count, distribution_date, ? "
                        f"FROM miscellaneous_contributions WHERE misc_contribution_id IN ({ph})",
                        (archive_key_id, *new_ids)
                    )

                # 7. أرشفة وحذف النثريات الأصلية من expenses
                misc_ids = [item[0] for item in misc_expenses]
                ph2 = ",".join("?" * len(misc_ids))
                cursor.execute(
                    f"DELETE FROM expenses_archive WHERE expense_id IN ({ph2}) AND archive_key_id = ?",
                    (*misc_ids, archive_key_id)
                )
                cursor.execute(
                    f"INSERT OR REPLACE INTO expenses_archive "
                    "(expense_id, item_name, quantity, price, total_price, consumption, remaining, is_miscellaneous, is_drink, date, archive_key_id) "
                    f"SELECT expense_id, item_name, quantity, price, total_price, consumption, remaining, is_miscellaneous, is_drink, date, ? "
                    f"FROM expenses WHERE expense_id IN ({ph2})",
                    (archive_key_id, *misc_ids)
                )
                cursor.execute(
                    f"DELETE FROM expenses WHERE expense_id IN ({ph2})",
                    misc_ids
                )

                logging.info(f"Distributed and archived {len(misc_ids)} items. Total value: {total_misc_value}")
                return True, archive_key_id

        except Exception as e:
            self.db.conn.rollback()
            logging.error(f"Error distributing miscellaneous: {e}", exc_info=True)
            self.show_snackbar(f"خطأ أثناء توزيع النثريات: {e}")
            return False, None

    def _get_or_create_archive_key(self, cursor, first_date):
        """إنشاء أو جلب مفتاح الأرشفة لفترة معينة"""
        cursor.execute(
            "SELECT archive_key_id FROM archive_keys WHERE start_date <= ? AND (end_date IS NULL OR end_date >= ?)",
            (first_date, first_date)
        )
        existing = cursor.fetchone()
        now_date = datetime.now().strftime("%Y-%m-%d")
        now_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if existing:
            key_id = existing[0]
            cursor.execute(
                "UPDATE archive_keys SET end_date = ?, archived_at = ? WHERE archive_key_id = ? AND end_date IS NULL",
                (now_date, now_dt, key_id)
            )
        else:
            archive_name = f"Dist_{first_date}_to_{now_date}"
            cursor.execute(
                "INSERT INTO archive_keys (archive_name, start_date, end_date, archived_at) VALUES (?, ?, ?, ?)",
                (archive_name, first_date, now_date, now_dt)
            )
            key_id = cursor.lastrowid
        return key_id

    def get_first_transaction_date(self):
        """أقل تاريخ سجل موجود في الجداول الثلاث"""
        queries = [
            "SELECT MIN(date) FROM meal_records",
            "SELECT MIN(date) FROM drink_records",
            "SELECT MIN(date) FROM expenses"
        ]
        dates = []
        for q in queries:
            cur = self.db.conn.execute(q)
            d = cur.fetchone()[0]
            if d:
                dates.append(d)
        return min(dates) if dates else None

    def show_snackbar(self, message):
        """عرض رسالة للمستخدم"""
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def close_dialog(self, e=None):
        """إغلاق نافذة الحوار"""
        if hasattr(self.page, "dialog") and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
