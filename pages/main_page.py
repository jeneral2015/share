# main_page.txt
import flet as ft
from utils.button_utils import create_button

class MainPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_content(self):
        # عنوان البرنامج
        title = ft.Text(
            "برنامج توزيع المصاريف",
            size=40,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )

        # زر إدخال البيانات
        btn_data_entry = create_button(
            "📥 إدخال البيانات",
            lambda e: self.navigate("input_page"),
            bgcolor=ft.colors.BLUE_700
        )

        # زر عرض البيانات
        btn_view_data = create_button(
            "📊 عرض البيانات",
            lambda e: self.navigate("view_page"),
            bgcolor=ft.colors.GREEN_700
        )

        # زر توزيع المصروفات
        btn_distribute = create_button(
            "🍽️ توزيع المصروفات",
            lambda e: self.navigate("distribute_expenses"),
            bgcolor=ft.colors.ORANGE_700
        )

        # زر التقارير
        btn_reports = create_button(
            "📑 التقارير",
            lambda e: self.navigate("reports_page"),
            bgcolor=ft.colors.PURPLE_700
        )

        # زر تقفيل الشهر
        btn_end_month = create_button(
            "📅 تقفيل الشهر",
            lambda e: self.navigate("end_month_page"),
            bgcolor=ft.colors.RED_700
        )

        # زر الإغلاق
        btn_exit = create_button(
            "❌ اغلاق",
            lambda e: self.exit_clicked(self.page),
            bgcolor=ft.colors.GREY_700
        )

        # صف الأزرار الأول (إدخال البيانات وعرض البيانات)
        row1 = ft.Row(
            [btn_view_data, btn_data_entry],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        # صف الأزرار الثاني (توزيع المصروفات والتقارير وتقفيل الشهر)
        row2 = ft.Row(
            [btn_end_month, btn_reports, btn_distribute],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        # صف زر الإغلاق
        row3 = ft.Row(
            [btn_exit],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # إضافة العناصر إلى Container مع خلفية الصورة
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=50),  # مسافة أعلى العنوان
                    title,
                    ft.Container(height=50),  # مسافة بين العنوان والأزرار
                    row1,
                    ft.Container(height=20),  # مسافة بين الصفوف
                    row2,
                    ft.Container(height=20),  # مسافة بين الصفوف
                    row3,
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            image_src=self.background_image.src,  # استخدام الخلفية المشتركة
            image_fit=ft.ImageFit.COVER,  # الصورة تغطي الخلفية بالكامل
            expand=True,  # جعل العنصر يتكيف مع حجم النافذة
        )

        return content

    @staticmethod
    def exit_clicked(page):
        # إنشاء SnackBar إذا لم يكن موجودًا
        if not hasattr(page, 'snack_bar'):
            page.snack_bar = ft.SnackBar(content=ft.Text(" "))  # SnackBar فارغ

        # إنشاء Dialog إذا لم يكن موجودًا
        if not hasattr(page, 'dialog'):
            page.dialog = ft.AlertDialog(title=ft.Text(""))  # Dialog فارغ

        dialog = ft.AlertDialog(
            title=ft.Text("تأكيد الإغلاق"),
            content=ft.Text("هل أنت متأكد أنك تريد إغلاق البرنامج؟"),
            actions=[
                ft.TextButton("نعم", on_click=lambda e: MainPage.exit(page)),
                ft.TextButton("لا", on_click=lambda e: (setattr(dialog, "open", False), page.update()))
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    @staticmethod
    def exit(page):
        try:
            # إغلاق أي SnackBar مفتوح
            if hasattr(page, 'snack_bar') and page.snack_bar is not None and page.snack_bar.open:
                page.snack_bar.open = False

            # إغلاق أي Dialog مفتوح
            if hasattr(page, 'dialog') and page.dialog is not None and page.dialog.open:
                page.dialog.open = False

            # تحديث الصفحة قبل الإغلاق
            page.update()

            # إغلاق النافذة
            page.window_close()
        except AttributeError as e:
            print(f"حدث خطأ أثناء الإغلاق: {e}")
