import flet as ft
from database import DatabaseManager
from utils.button_utils import create_button
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

# Register Arabic font (assuming 1.ttf is an Arabic font)
try:
    pdfmetrics.registerFont(TTFont('Arabic-Font', '/home/ubuntu/project_review/1.ttf'))
except Exception as e:
    logging.warning(f"Could not register font /home/ubuntu/project_review/1.ttf for PDF export: {e}")
    # Fallback font if registration fails
    pdfmetrics.registerFont(TTFont('Arabic-Font', 'arial.ttf'))


class ReportsPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image
        self.db = db
        
        # تخزين مؤقت للتقارير
        self.current_archive_key = None
        self.archive_periods = []
        
        # عناصر واجهة المستخدم للتقارير التاريخية
        self.archive_dropdown = ft.Dropdown(
            label="اختر الفترة",
            width=300,
            on_change=self.on_archive_period_change
        )

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_content(self):
        # تحميل فترات الأرشيف عند فتح الصفحة
        self.load_archive_periods()
        
        # العنوان
        title = ft.Text(
            "التقارير",
            size=40,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )

        # قسم التقارير الحالية
        current_reports_title = ft.Text(
            "تقارير الشهر الحالي",
            size=24,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )
        
        current_reports_row = ft.Row(
            [
                create_button("تقرير المصروفات الحالية", self.show_expenses_report, bgcolor=ft.colors.GREEN),
                create_button("تقرير المشتركين الحالي", self.show_members_report, bgcolor=ft.colors.BLUE),
                create_button("تقرير مالي شامل", self.show_comprehensive_report, bgcolor=ft.colors.PURPLE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        # قسم التقارير التاريخية
        historical_reports_title = ft.Text(
            "التقارير التاريخية",
            size=24,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )
        
        historical_reports_controls = ft.Column([
            ft.Row(
                [self.archive_dropdown],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    create_button("تقرير المصروفات المؤرشفة", self.show_archived_expenses_report, bgcolor=ft.colors.AMBER),
                    create_button("تقرير المشتركين المؤرشف", self.show_archived_members_report, bgcolor=ft.colors.INDIGO),
                    create_button("تقرير الوجبات المؤرشف", self.show_archived_meals_report, bgcolor=ft.colors.TEAL),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
        ])

        # قسم التصدير والرسوم البيانية
        visualization_title = ft.Text(
            "الرسوم البيانية والتصدير",
            size=24,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )
        
        visualization_row = ft.Row(
            [
                create_button("رسم بياني للمصروفات", self.show_expenses_chart, bgcolor=ft.colors.ORANGE),
                create_button("رسم بياني للاستهلاك", self.show_consumption_chart, bgcolor=ft.colors.PINK),
                create_button("تصدير جميع التقارير", self.export_all_reports, bgcolor=ft.colors.CYAN),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        # زر الرجوع
        btn_back = create_button(
            "رجوع",
            lambda e: self.navigate("main_page"),
            bgcolor=ft.colors.RED
        )

        # تجميع العناصر
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    title,
                    ft.Container(height=20),
                    current_reports_title,
                    ft.Container(height=10),
                    current_reports_row,
                    ft.Container(height=20),
                    historical_reports_title,
                    ft.Container(height=10),
                    historical_reports_controls,
                    ft.Container(height=20),
                    visualization_title,
                    ft.Container(height=10),
                    visualization_row,
                    ft.Container(height=20),
                    btn_back,
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            image_src=self.background_image.src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
        )

        return content

    def load_archive_periods(self):
        try:
            # استعلام لجلب فترات الأرشيف المتاحة
            query = """
                SELECT archive_key_id, archive_name, start_date, end_date, archived_at
                FROM archive_keys
                ORDER BY archived_at DESC
            """
            rows = self.db.fetch_all(query)
            
            if not rows:
                self.archive_periods = []
                self.archive_dropdown.options = [
                    ft.dropdown.Option("لا توجد فترات مؤرشفة", disabled=True)
                ]
                return
            
            # تخزين بيانات الفترات
            self.archive_periods = rows
            
            # إنشاء خيارات القائمة المنسدلة
            options = []
            for row in rows:
                archive_id, archive_name, start_date, end_date, archived_at = row
                # استخدام اسم الأرشيف إذا كان موجودًا، وإلا استخدام الفترة الزمنية
                display_name = archive_name if archive_name else f"الفترة من {start_date} إلى {end_date}"
                options.append(ft.dropdown.Option(f"{display_name} (أرشفة: {archived_at})", key=str(archive_id)))
            
            self.archive_dropdown.options = options
            # تحديد أحدث فترة افتراضيًا
            if options:
                self.archive_dropdown.value = options[0].key
                self.current_archive_key = int(options[0].key)
            
        except Exception as e:
            logging.error(f"Error loading archive periods: {e}")
            self.show_snackbar(f"خطأ في تحميل فترات الأرشيف: {e}")
            self.archive_dropdown.options = [
                ft.dropdown.Option("خطأ في تحميل الفترات", disabled=True)
            ]

    def on_archive_period_change(self, e):
        if e.data and e.data != "null":
            self.current_archive_key = int(e.data)
            self.show_snackbar(f"تم اختيار الفترة المؤرشفة")

    # --- تقارير الشهر الحالي ---

    def show_expenses_report(self, e=None):
        try:
            query = """
                SELECT item_name, quantity, price, total_price, consumption, remaining, 
                       CASE WHEN is_miscellaneous = 1 THEN 'نعم' ELSE 'لا' END as is_misc,
                       CASE WHEN is_drink = 1 THEN 'نعم' ELSE 'لا' END as is_drink,
                       date
                FROM expenses
                ORDER BY date DESC, item_name
            """
            rows = self.db.fetch_all(query)

            if not rows:
                self.show_snackbar("لا توجد بيانات للمصروفات الحالية.")
                return

            # إنشاء الجدول
            columns = ["item_name", "quantity", "price", "total_price", "consumption", "remaining", "is_misc", "is_drink", "date"]
            column_names = {
                "item_name": "اسم الصنف",
                "quantity": "الكمية",
                "price": "سعر الوحدة",
                "total_price": "السعر الإجمالي",
                "consumption": "الاستهلاك",
                "remaining": "المتبقي",
                "is_misc": "نثرية",
                "is_drink": "مشروب",
                "date": "التاريخ",
            }

            # حساب الإجماليات
            total_value = sum(row[3] for row in rows)  # total_price
            total_remaining_value = sum(row[5] * row[2] for row in rows)  # remaining * price

            # إنشاء عنوان مع الإجماليات
            title_with_totals = ft.Column([
                ft.Text("تقرير المصروفات الحالية", weight=ft.FontWeight.BOLD, size=20),
                ft.Text(f"إجمالي قيمة المشتريات: {total_value:.2f}", weight=ft.FontWeight.BOLD),
                ft.Text(f"إجمالي قيمة المتبقي: {total_remaining_value:.2f}", weight=ft.FontWeight.BOLD),
            ])

            # إنشاء جدول العرض
            table = self.create_data_table(rows, columns, column_names)

            # إظهار التقرير في نافذة حوار
            self.show_report_dialog(
                title_with_totals, 
                table, 
                lambda: self.export_expenses_report(rows, columns, column_names, "تقرير_المصروفات_الحالية")
            )

        except Exception as e:
            logging.error(f"Error showing expenses report: {e}")
            self.show_snackbar(f"حدث خطأ أثناء عرض تقرير المصروفات: {e}")

    def show_members_report(self, e=None):
        try:
            query = """
                SELECT name, rank, contribution, total_due, date,
                       (contribution - total_due) as balance
                FROM members
                ORDER BY name
            """
            rows = self.db.fetch_all(query)

            if not rows:
                self.show_snackbar("لا توجد بيانات للمشتركين الحاليين.")
                return

            # إنشاء الجدول
            columns = ["name", "rank", "contribution", "total_due", "balance", "date"]
            column_names = {
                "name": "الاسم",
                "rank": "الرتبة",
                "contribution": "المساهمة",
                "total_due": "المستحق",
                "balance": "الرصيد",
                "date": "تاريخ التسجيل",
            }

            # حساب الإجماليات
            total_contribution = sum(row[2] for row in rows)  # contribution
            total_due = sum(row[3] for row in rows)  # total_due
            total_balance = sum(row[5] for row in rows)  # balance

            # إنشاء عنوان مع الإجماليات
            title_with_totals = ft.Column([
                ft.Text("تقرير المشتركين الحالي", weight=ft.FontWeight.BOLD, size=20),
                ft.Text(f"إجمالي المساهمات: {total_contribution:.2f}", weight=ft.FontWeight.BOLD),
                ft.Text(f"إجمالي المستحقات: {total_due:.2f}", weight=ft.FontWeight.BOLD),
                ft.Text(f"إجمالي الرصيد: {total_balance:.2f}", weight=ft.FontWeight.BOLD),
            ])

            # إنشاء جدول العرض
            table = self.create_data_table(rows, columns, column_names)

            # إظهار التقرير في نافذة حوار
            self.show_report_dialog(
                title_with_totals, 
                table, 
                lambda: self.export_members_report(rows, columns, column_names, "تقرير_المشتركين_الحالي")
            )

        except Exception as e:
            logging.error(f"Error showing members report: {e}")
            self.show_snackbar(f"حدث خطأ أثناء عرض تقرير المشتركين: {e}")

    def show_comprehensive_report(self, e=None):
        try:
            # استدعاء وظيفة إنشاء التقرير الشامل (مشابهة لما في صفحة تقفيل الشهر)
            report_data = self.generate_comprehensive_report()
            
            if not report_data:
                self.show_snackbar("لا يمكن إنشاء التقرير الشامل. تأكد من وجود بيانات كافية.")
                return
                
            # عرض التقرير
            self.show_comprehensive_report_dialog(report_data)
            
        except Exception as e:
            logging.error(f"Error showing comprehensive report: {e}")
            self.show_snackbar(f"حدث خطأ أثناء عرض التقرير الشامل: {e}")

    def generate_comprehensive_report(self):
        try:
            # 1. بيانات المشتركين والاستهلاك
            query_members = """
                SELECT 
                    m.member_id,
                    m.name AS "الاسم", 
                    m.rank AS "الرتبة", 
                    m.contribution AS "المساهمة",
                    COALESCE(SUM(mr.final_cost), 0) AS "تكلفة_الوجبات",
                    COALESCE(SUM(dr.total_cost), 0) AS "تكلفة_المشروبات",
                    m.total_due AS "النثرية_الموزعة"
                FROM members m
                LEFT JOIN meal_records mr ON m.member_id = mr.member_id
                LEFT JOIN drink_records dr ON m.member_id = dr.member_id
                GROUP BY m.member_id, m.name, m.rank, m.contribution, m.total_due
            """
            df_members = pd.read_sql(query_members, self.db.conn)
            
            if df_members.empty:
                return None
                
            # حساب إجمالي الاستهلاك لكل مشترك
            df_members["إجمالي_الاستهلاك"] = df_members["تكلفة_الوجبات"] + df_members["تكلفة_المشروبات"] + df_members["النثرية_الموزعة"]
            df_members["الرصيد_النهائي"] = df_members["المساهمة"] - df_members["إجمالي_الاستهلاك"]

            # 2. ملخص مالي
            total_contributions = df_members["المساهمة"].sum()
            total_meal_cost = df_members["تكلفة_الوجبات"].sum()
            total_drink_cost = df_members["تكلفة_المشروبات"].sum()
            total_misc_distributed = df_members["النثرية_الموزعة"].sum()
            total_consumption = df_members["إجمالي_الاستهلاك"].sum()
            final_balance_members = df_members["الرصيد_النهائي"].sum()

            # 3. قيمة المخزون المتبقي
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT SUM(remaining * price) FROM expenses WHERE is_miscellaneous = 0")
            value_remaining_items = cursor.fetchone()[0] or 0

            # 4. إنشاء قسم الملخص
            summary_data = {
                "البند": ["إجمالي المساهمات", "إجمالي تكلفة الوجبات", "إجمالي تكلفة المشروبات", "إجمالي النثرية الموزعة", 
                          "إجمالي الاستهلاك", "قيمة المخزون المتبقي", "الرصيد النقدي المتوقع (المساهمات - الاستهلاك)", "رصيد المشتركين النهائي"],
                "المبلغ": [total_contributions, total_meal_cost, total_drink_cost, total_misc_distributed, 
                           total_consumption, value_remaining_items, total_contributions - total_consumption, final_balance_members]
            }
            df_summary = pd.DataFrame(summary_data)

            # 5. تنسيق جدول المشتركين
            df_members_display = df_members[["الاسم", "الرتبة", "المساهمة", "تكلفة_الوجبات", "تكلفة_المشروبات", "النثرية_الموزعة", "إجمالي_الاستهلاك", "الرصيد_النهائي"]]
            # إضافة صف الإجماليات
            totals_members = df_members_display.sum(numeric_only=True).to_frame().T
            totals_members["الاسم"] = "الإجمالي"
            totals_members["الرتبة"] = ""
            df_members_display = pd.concat([df_members_display, totals_members], ignore_index=True)
            
            # تخزين كلا الجزأين للتصدير/العرض
            report_content = {
                "summary": df_summary,
                "members": df_members_display
            }
            return report_content
        except Exception as e:
            logging.error(f"Error generating comprehensive report: {e}")
            self.show_snackbar(f"حدث خطأ أثناء إنشاء التقرير الشامل: {e}")
            return None
