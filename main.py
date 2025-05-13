import flet as ft
from screeninfo import get_monitors
from pages.main_page import MainPage
from pages.input_page import InputPage
from pages.view_page import ViewPage
from pages.input_subscribers import InputSubscribersPage
from pages.input_purchases import InputPurchasesPage
from pages.show_subscribers import ShowSubscribersPage
from pages.show_purchases import ShowPurchasesPage
from pages.show_over import ShowOverPage
from pages.distribute_expenses import DistributeExpensesPage
from pages.drink_page import DrinkPage
from pages.meal_page import MealPage
from pages.reports_page import ReportsPage
from pages.end_month_page import EndMonthPage
from database import DatabaseManager
import logging

# إعداد الـ Logging
logging.basicConfig(level=logging.INFO)

def main(page: ft.Page):
    # إعدادات الصفحة
    page.title = "برنامج توزيع المصاريات"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # تحديد حجم النافذة وإمكانية تغيير الحجم
    page.window.width = 800
    page.window.height = 600
    page.window.resizable = True

    # حساب موقع النافذة لفتحها في منتصف الشاشة
    try:
        monitors = get_monitors()
        if monitors:
            primary_monitor = monitors[0]
            screen_width = primary_monitor.width
            screen_height = primary_monitor.height

            window_left = (screen_width - 800) // 2
            window_top = (screen_height - 600) // 2

            page.window.left = window_left
            page.window.top = window_top
    except Exception as e:
        print(f"حدث خطأ أثناء تعيين موقع النافذة: {e}")

    # تعيين الخط اليدوي
    page.fonts = {
        "DancingScript": "1.ttf"
    }
    page.theme = ft.Theme(font_family="DancingScript")

    # تحميل الخلفية مرة واحدة
    background_image = ft.Image(src="3.jpg", fit=ft.ImageFit.COVER, expand=True)
    
    # إنشاء اتصال مركزي بقاعدة البيانات
    db = DatabaseManager()
    
    # --- إغلاق الاتصال عند إغلاق النافذة ---
    def on_window_close(e):
        if e.data == "close":
            db.close_connection()
            page.window.destroy()
    page.window.on_close = on_window_close

    # إنشاء الصفحات مع تمرير الاتصال المركزي
    pages = {
        "main_page": MainPage(page, background_image, db),
        "input_page": InputPage(page, background_image, db),
        "view_page": ViewPage(page, background_image, db),
        "input_subscribers": InputSubscribersPage(page, background_image, db),
        "input_purchases": InputPurchasesPage(page, background_image, db),
        "show_subscribers": ShowSubscribersPage(page, background_image, db),
        "show_purchases": ShowPurchasesPage(page, background_image, db),
        "show_over": ShowOverPage(page, background_image, db),
        "distribute_expenses": DistributeExpensesPage(page, background_image, db),
        "drink_page": DrinkPage(page, background_image, db),
        "reports_page": ReportsPage(page, background_image, db),
        "end_month_page": EndMonthPage(page, background_image, db),
        "meal_page": MealPage(page, background_image, db)
    }

    # تعيين الصفحة الرئيسية
    page.add(pages["main_page"].get_content())

    # وظيفة للتنقل بين الصفحات
    def navigate(page_name):
        page.clean()
        if page_name in pages:
            page.add(pages[page_name].get_content())
        page.update()

    # تمرير دالة التنقل إلى الصفحات
    for page_instance in pages.values():
        page_instance.set_navigate(navigate)

ft.app(target=main)