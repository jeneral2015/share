import asyncio
import flet as ft
import pandas as pd
import os
import subprocess
import platform
import logging
from datetime import datetime
from pathlib import Path
import sys
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pages.distribute_miscellaneous import DistributeMiscellaneous
from utils.button_utils import create_button

class FinalizeMonth:
    def __init__(self, page, db):
        self.page = page
        self.db = db
        self.report_df = None
        self.file_picker = ft.FilePicker()
        self.page.overlay.append(self.file_picker)
        self.page.update()
        self.registered_font = self.register_arabic_font()
    
    def register_arabic_font(self):
        """Register an Arabic font for PDF export"""
        try:
            # 1. Check in the same directory as the main file
            if hasattr(sys, 'frozen'):
                # If running as a PyInstaller executable
                main_dir = sys._MEIPASS
            else:
                # Normal Python script
                main_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            
            font_path = os.path.join(main_dir, '1.ttf')
            
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('Arabic-Font', font_path))
                    logging.info(f"Successfully registered font from main directory: {font_path}")
                    return True
                except Exception as e:
                    logging.warning(f"Could not register font from main directory: {e}")
            
            # 2. Try project assets directory
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            font_path = os.path.join(project_dir, 'assets', 'fonts', '1.ttf')
            
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('Arabic-Font', font_path))
                    logging.info(f"Successfully registered font from project directory: {font_path}")
                    return True
                except Exception as e:
                    logging.warning(f"Could not register font from project directory: {e}")

            # 3. Try system fonts
            system_fonts = [
                # Linux
                "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                # Windows
                "C:/Windows/Fonts/tahoma.ttf",  # Tahoma supports Arabic
                "C:/Windows/Fonts/arial.ttf",
                # macOS
                "/Library/Fonts/Arial Unicode.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                # User fonts
                os.path.join(os.path.expanduser("~"), ".fonts", "arial.ttf"),
                os.path.join(os.path.dirname(sys.executable), "fonts", "arial.ttf")
            ]

            for font_path in system_fonts:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Arabic-Font', font_path))
                        logging.info(f"Successfully registered font from system path: {font_path}")
                        return True
                    except Exception as e:
                        logging.warning(f"Could not register font from {font_path}: {e}")
                        continue

            # 4. Fallback to system default (Helvetica works on most systems)
            logging.warning("Using system default font (Helvetica) for PDF export")
            return False
            
        except Exception as e:
            logging.error(f"Error registering Arabic font: {e}")
            return False
    
    def start_process(self):
        """Start the month finalization process after checking for necessary data"""
        if not self.check_all_data_exists():
            self.show_snackbar("لا توجد بيانات كافية لتقفيل الشهر (تحقق من وجود مشتركين ومصروفات ووجبات ومشروبات).")
            return
        
        self.show_confirmation(
            title="تقفيل الشهر",
            message="سيتم توزيع النثريات، أرشفة بيانات الشهر الحالي، تحديث أرصدة المشتروات، وإعداد التقرير النهائي. هل تريد الاستمرار؟",
            confirm_action=self._finalize_month
        )
    
    def check_all_data_exists(self):
        """Check if there is sufficient data to finalize the month"""
        try:
            queries = [
                "SELECT COUNT(*) FROM members",
                "SELECT COUNT(*) FROM expenses",
                "SELECT COUNT(*) FROM meal_records",
                "SELECT COUNT(*) FROM drink_records"
            ]
            results = []
            for query in queries:
                result = self.db.fetch_all(query)
                results.append(result[0][0] if result else 0)
            
            total_records = sum(results)
            logging.info(f"Found {total_records} total records across all tables")
            return total_records > 0
            
        except Exception as e:
            logging.error(f"Error checking data existence: {e}")
            return False
    
    def show_confirmation(self, title, message, confirm_action):
        """Show a confirmation dialog before performing a critical action"""
        def on_confirm(e):
            self.page.dialog.open = False
            self.page.update()
            confirm_action()
            
        confirm_dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("نعم", on_click=on_confirm),
                ft.TextButton("لا", on_click=self.close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()
    
    def _finalize_month(self):
        """Main function to finalize the month and generate reports"""
        try:
            # 1. Distribute miscellaneous items using the existing distribution code
            distributor = DistributeMiscellaneous(self.page, self.db)
            success_distribute, archive_key_id = distributor._distribute_and_archive_miscellaneous()
            
            if not success_distribute:
                self.show_snackbar("لا توجد مصروفات نثرية للتوزيع.")
            
            # 2. Generate comprehensive report
            self.report_df = self.generate_comprehensive_report()
            
            if self.report_df is None:
                self.show_snackbar("لا توجد بيانات كافية لإنشاء التقرير.")
                return
            
            # 3. Archive and update data
            success_archive = self._archive_and_update_data(archive_key_id)
            
            if not success_archive:
                return
            
            # 4. Show the final report
            self.show_report_dialog(self.report_df)
            self.show_snackbar("تم تقفيل الشهر بنجاح! التقرير جاهز للتصدير.")
            
        except Exception as e:
            logging.error(f"Error during month finalization: {str(e)}")
            self.show_snackbar(f"حدث خطأ فادح أثناء تقفيل الشهر: {str(e)}")
    
    def _archive_and_update_data(self, archive_key_id):
        """Archive data and update database"""
        if not archive_key_id:
            self.show_snackbar("خطأ: مفتاح الأرشيف غير متوفر.")
            return False
            
        try:
            with self.db.conn:
                cursor = self.db.conn.cursor()
                
                # Tables to archive
                tables_to_archive = [
                    ("meal_records", "meal_records_archive", "meal_record_id"),
                    ("drink_records", "drink_records_archive", "drink_record_id"),
                ]
                
                # Process each table
                for main_table, archive_table, primary_key in tables_to_archive:
                    # Count records in main table
                    cursor.execute(f"SELECT COUNT(*) FROM {main_table}")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        # Remove any existing archive records for this archive key
                        cursor.execute(f"""
                            DELETE FROM {archive_table} 
                            WHERE archive_key_id = ? AND 
                                  EXISTS (SELECT 1 FROM {main_table} 
                                          WHERE {main_table}.{primary_key} = {archive_table}.{primary_key})
                        """, (archive_key_id,))
                        
                        # Get column names for the main table
                        cursor.execute(f"PRAGMA table_info({main_table})")
                        columns = [info[1] for info in cursor.fetchall()]
                        cols_str = ", ".join(columns)
                        
                        # Insert into archive table
                        cursor.execute(f"""
                            INSERT OR REPLACE INTO {archive_table} 
                            ({cols_str}, archive_key_id) 
                            SELECT {cols_str}, ? FROM {main_table}
                        """, (archive_key_id,))
                        
                        # Delete from main table
                        cursor.execute(f"DELETE FROM {main_table}")
                        logging.info(f"Archived and cleared {count} records from {main_table}")
                
                # Handle non-miscellaneous expenses
                cursor.execute("SELECT expense_id, remaining FROM expenses WHERE is_miscellaneous = 0")
                non_misc_expenses = cursor.fetchall()
                
                if non_misc_expenses:
                    placeholders = ",".join("?" * len(non_misc_expenses))
                    expense_ids = [expense[0] for expense in non_misc_expenses]
                    
                    # Remove existing archive records for these expenses
                    cursor.execute(f"""
                        DELETE FROM expenses_archive 
                        WHERE expense_id IN ({placeholders}) AND archive_key_id = ?
                    """, (*expense_ids, archive_key_id))
                    
                    # Insert into archive table
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO expenses_archive 
                        (expense_id, item_name, quantity, price, total_price, consumption, remaining, 
                         is_miscellaneous, is_drink, date, archive_key_id)
                        SELECT expense_id, item_name, quantity, price, total_price, consumption, remaining, 
                               is_miscellaneous, is_drink, date, ? 
                        FROM expenses 
                        WHERE expense_id IN ({placeholders})
                    """, (archive_key_id, *expense_ids))
                    
                    # Update and reset remaining values
                    for expense_id, remaining in non_misc_expenses:
                        cursor.execute("""
                            UPDATE expenses 
                            SET remaining = 0 
                            WHERE expense_id = ? AND is_miscellaneous = 0
                        """, (expense_id,))
                        
                    logging.info(f"Archived and updated {len(non_misc_expenses)} non-miscellaneous expenses")
                    
            return True
            
        except Exception as e:
            self.db.conn.rollback()
            logging.error(f"Error during archiving and updating data: {str(e)}")
            self.show_snackbar(f"خطأ أثناء الأرشفة والتحديث: {str(e)}")
            return False
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive report of all data"""
        try:
            # Query to get member data
            query_members = """
                SELECT 
                    m.member_id,
                    m.name AS "الاسم", 
                    m.rank AS "الرتبة", 
                    m.contribution AS "المساهمة",
                    COALESCE(SUM(mr.final_cost), 0) AS "تكلفة_الوجبات",
                    COALESCE(SUM(dr.total_cost), 0) AS "تكلفة_المشروبات",
                    COALESCE(m.total_due, 0) AS "النثرية_الموزعة"
                FROM members m
                LEFT JOIN meal_records mr ON m.member_id = mr.member_id
                LEFT JOIN drink_records dr ON m.member_id = dr.member_id
                GROUP BY m.member_id, m.name, m.rank, m.contribution, m.total_due
            """
            
            df_members = pd.read_sql(query_members, self.db.conn)
            
            if df_members.empty:
                logging.warning("No member data found for report")
                return None
            
            # Calculate additional financial metrics
            numeric_cols = ["المساهمة", "تكلفة_الوجبات", "تكلفة_المشروبات", "النثرية_الموزعة"]
            df_members[numeric_cols] = df_members[numeric_cols].fillna(0).astype(float).round(1)
            
            df_members["إجمالي_الاستهلاك"] = (
                df_members["تكلفة_الوجبات"] + 
                df_members["تكلفة_المشروبات"] + 
                df_members["النثرية_الموزعة"]
            ).round(1)
            
            df_members["الرصيد_النهائي"] = (
                df_members["المساهمة"] - 
                df_members["إجمالي_الاستهلاك"]
            ).round(1)
            
            # Calculate summary statistics
            total_contributions = df_members["المساهمة"].sum().round(1)
            total_meal_cost = df_members["تكلفة_الوجبات"].sum().round(1)
            total_drink_cost = df_members["تكلفة_المشروبات"].sum().round(1)
            total_misc_distributed = df_members["النثرية_الموزعة"].sum().round(1)
            total_consumption = df_members["إجمالي_الاستهلاك"].sum().round(1)
            
            # Get value of remaining items
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT SUM(remaining * price) FROM expenses WHERE is_miscellaneous = 0")
            value_remaining_items = round(cursor.fetchone()[0] or 0, 1)
            
            # Create summary data
            summary_data = {
                "البند": [
                    "إجمالي المساهمات", 
                    "إجمالي تكلفة الوجبات", 
                    "إجمالي تكلفة المشروبات", 
                    "إجمالي النثرية الموزعة", 
                    "إجمالي الاستهلاك", 
                    "قيمة المخزون المتبقي", 
                    "الرصيد النقدي المتوقع (المساهمات - الاستهلاك)", 
                    "رأس المال المتبقي (المساهمات - الاستهلاك الكلي)",
                    "رصيد المشتركين النهائي"
                ],
                "المبلغ": [
                    total_contributions, 
                    total_meal_cost, 
                    total_drink_cost, 
                    total_misc_distributed, 
                    total_consumption, 
                    value_remaining_items, 
                    round(total_contributions - total_consumption, 1), 
                    df_members["الرصيد_النهائي"].sum().round(1),
                    df_members["الرصيد_النهائي"].sum().round(1)
                ]
            }
            
            # Validate that lengths are equal before creating DataFrame
            if len(summary_data["البند"]) != len(summary_data["المبلغ"]):
                raise ValueError(f"Mismatch in summary data lengths: "
                                 f"{len(summary_data['البند'])} vs "
                                 f"{len(summary_data['المبلغ'])}")
            
            df_summary = pd.DataFrame(summary_data)
            
            # Prepare member display data
            df_members_display = df_members[[
                "الاسم", "الرتبة", "المساهمة", "تكلفة_الوجبات", 
                "تكلفة_المشروبات", "النثرية_الموزعة", 
                "إجمالي_الاستهلاك", "الرصيد_النهائي"
            ]]
            
            # Add totals row
            totals_members = df_members_display.sum(numeric_only=True).to_frame().T.round(1)
            totals_members["الاسم"] = "الإجمالي"
            totals_members["الرتبة"] = ""
            
            # Combine member data with totals
            df_members_display = pd.concat([df_members_display, totals_members], ignore_index=True)
            
            return {
                "summary": df_summary,
                "members": df_members_display
            }
            
        except Exception as e:
            logging.error(f"Error generating comprehensive report: {e}")
            self.show_snackbar(f"حدث خطأ أثناء إنشاء التقرير الشامل: {e}")
            return None
    
    def show_report_dialog(self, report_data):
        """Display the final report dialog with options to export"""
        def format_number(value):
            if isinstance(value, (int, float)):
                return f"{value:,.1f}"
            return str(value)
        
        # Create summary table
        summary_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("البند", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("المبلغ", weight=ft.FontWeight.BOLD)),
            ],
            rows=[
                ft.DataRow([
                    ft.DataCell(ft.Text(str(row["البند"]))),
                    ft.DataCell(ft.Text(format_number(row["المبلغ"])))
                ]) for _, row in report_data["summary"].iterrows()
            ],
        )
        
        # Create members table
        members_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD)) for col in report_data["members"].columns],
            rows=[
                ft.DataRow([
                    ft.DataCell(ft.Text(format_number(row[col]))) 
                    for col in report_data["members"].columns
                ])
                for _, row in report_data["members"].iterrows()
            ],
            horizontal_margin=10,
            column_spacing=20,
        )
        
        async def pick_save_location(file_extension):
            """Choose a location to save the exported file"""
            try:
                file_type = {
                    "xlsx": (".xlsx", "ملف Excel"),
                    "pdf": (".pdf", "ملف PDF")
                }.get(file_extension, ".pdf")
                
                # Set default path to reports directory
                default_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
                
                # Create reports directory if it doesn't exist
                if not os.path.exists(default_dir):
                    os.makedirs(default_dir)
                    
                # Create default file name with current date
                default_name = f"تقرير_تقفيل_الشهر_{datetime.now().strftime('%Y-%m-%d')}{file_type[0]}"
                default_path = os.path.join(default_dir, default_name)
                
                # Show file picker dialog
                await self.file_picker.save_file_async(
                    file_name=default_name,
                    initial_directory=default_dir,
                    allowed_extensions=[file_type[0]],
                    file_type=ft.FilePickerFileType.CUSTOM
                )
                
                # Wait for user to select a file (with timeout)
                timeout = 10  # seconds
                start_time = datetime.now()
                while True:
                    if self.file_picker._dialog_result is not None:
                        result = self.file_picker._dialog_result
                        if result:
                            save_path = result.path
                            # Ensure correct file extension
                            if save_path and not save_path.endswith(file_type[0]):
                                save_path += file_type[0]
                            logging.info(f"Selected save path: {save_path}")
                            return save_path
                        break
                    
                    if (datetime.now() - start_time).seconds > timeout:
                        logging.warning("Save file dialog timeout")
                        return default_path
                        
                    await asyncio.sleep(0.1)
                    
                return default_path
                
            except Exception as e:
                logging.error(f"Error selecting save location: {e}")
                self.show_snackbar(f"حدث خطأ أثناء اختيار موقع الحفظ: {e}")
                return None

        async def export_excel_with_picker(e):
            """Export the report to Excel file"""
            save_path = await pick_save_location("xlsx")
            if save_path is None:
                return
                
            try:
                with pd.ExcelWriter(save_path) as writer:
                    report_data["summary"].to_excel(writer, sheet_name="ملخص", index=False)
                    report_data["members"].to_excel(writer, sheet_name="المشتركين", index=False)
                    
                self.show_snackbar(f"تم التصدير بنجاح إلى: {save_path}")
                self.open_file_directory(save_path)
                
            except Exception as e:
                logging.error(f"Excel export error: {e}")
                self.show_snackbar(f"خطأ في التصدير إلى Excel: {e}")

        async def export_pdf_with_picker(e):
            """Export the report to PDF file"""
            save_path = await pick_save_location("pdf")
            if save_path is None:
                return
                
            try:
                doc = SimpleDocTemplate(save_path, pagesize=A4, 
                                      rightMargin=30, leftMargin=30, 
                                      topMargin=30, bottomMargin=30)
                elements = []
                styles = getSampleStyleSheet()
                title_style = styles["Title"]
                
                # Set Arabic font if available
                if self.registered_font:
                    title_style.fontName = "Arabic-Font"
                else:
                    title_style.fontName = "Helvetica"
                    
                title_style.alignment = 2  # Right alignment
                
                # Add report title
                elements.append(Paragraph("التقرير الشامل لتقفيل الشهر", title_style))
                elements.append(Spacer(1, 20))
                
                # Add summary section
                elements.append(Paragraph("الملخص المالي:", styles["Heading2"]))
                
                # Prepare summary table for PDF
                summary_data = [report_data["summary"].columns.tolist()] + report_data["summary"].values.tolist()
                summary_table_pdf = Table(summary_data)
                summary_table_pdf.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), title_style.fontName),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                elements.append(summary_table_pdf)
                elements.append(Spacer(1, 20))
                
                # Add member details section
                elements.append(Paragraph("تفاصيل المشتركين:", styles["Heading2"]))
                
                # Prepare members table for PDF
                members_data = [report_data["members"].columns.tolist()] + report_data["members"].values.tolist()
                members_table_pdf = Table(members_data, repeatRows=1)
                members_table_pdf.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), title_style.fontName),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                elements.append(members_table_pdf)
                doc.build(elements)
                
                self.show_snackbar(f"تم التصدير بنجاح إلى: {save_path}")
                self.open_file_directory(save_path)
                
            except Exception as e:
                logging.error(f"PDF export error: {e}")
                self.show_snackbar(f"خطأ في التصدير إلى PDF: {e}")

        # Create content for the report dialog
        content = ft.Column([
            ft.Text("ملخص مالي", size=20, weight=ft.FontWeight.BOLD),
            ft.ListView([
                summary_table
            ], height=200),
            ft.Divider(),
            ft.Text("تفاصيل المشتركين", size=20, weight=ft.FontWeight.BOLD),
            ft.ListView([
                members_table
            ], height=300),
            ft.Row([
                create_button("تصدير PDF", export_pdf_with_picker, icon=ft.icons.PICTURE_AS_PDF),
                create_button("تصدير Excel", export_excel_with_picker, icon=ft.icons.TABLE_CHART),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # Create and show the dialog
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Text("التقرير الشامل", expand=True),
                ft.IconButton(icon=ft.icons.CLOSE, on_click=lambda e: self.close_dialog()),
            ]),
            content=ft.Container(
                content=content,
                width=800,
                height=600,
                margin=ft.margin.all(10),
                padding=ft.padding.all(10),
            ),
            actions=[
                ft.TextButton("إغلاق", on_click=lambda e: self.close_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
            bgcolor=ft.colors.BACKGROUND,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def open_file_directory(self, file_path):
        """Open the directory containing the exported file"""
        try:
            if platform.system() == "Windows":
                # Use shell=True to properly handle long paths
                subprocess.Popen(f'explorer /select,"{file_path}"', shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", file_path])
            else:  # Linux and others
                subprocess.Popen(["xdg-open", os.path.dirname(file_path)])
                
        except Exception as e:
            logging.error(f"Failed to open directory: {e}")
            self.show_snackbar(f"فشل فتح المجلد: {e}")

    def show_snackbar(self, message):
        """Display a snack bar message to the user"""
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def close_dialog(self, e=None):
        """Close the current dialog"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
