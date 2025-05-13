import flet as ft
from database import DatabaseManager
from utils.button_utils import create_button
from datetime import datetime

class MealPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image
        # استخدام الوحدة المركزية لإدارة قاعدة البيانات
        self.db = db
        self.selected_meals = {}
        self.member_selection = {}
        self.misc_var = None
        # إغلاق الاتصال بقاعدة البيانات عند إغلاق الصفحة
        self.page.on_close = self.close_connection
    
    def set_navigate(self, navigate):
        self.navigate = navigate
    
    def get_content(self):
        return self.show_initial_page()
    
    # الصفحة الأولى: اختيار نوع الوجبة
    def show_initial_page(self):
        self.selected_meals = {}
        self.member_selection = {}
        self.misc_var = None
        title = ft.Text(
            "تسجيل الوجبة",
            size=40,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )
        self.date_field = ft.TextField(
            label="التاريخ",
            value=datetime.now().strftime("%Y-%m-%d"),
            width=300,
            bgcolor=ft.colors.WHITE,
            label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)
        )
        self.meal_type_dropdown = ft.Dropdown(
            label="نوع الوجبة",
            options=[
                ft.dropdown.Option("فطار"),
                ft.dropdown.Option("غداء"),
                ft.dropdown.Option("عشاء"),
            ],
            width=300,
            bgcolor=ft.colors.WHITE,
            label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)
        )
        btn_next = create_button(
            "التالي",
            lambda e: self.validate_initial_page(e),
            bgcolor=ft.colors.GREEN
        )
        btn_back = create_button(
            "رجوع",
            lambda e: self.navigate("distribute_expenses"),
            bgcolor=ft.colors.RED
        )
        content = ft.Stack(
            [
                ft.Container(
                    image_src=self.background_image.src,
                    image_fit=ft.ImageFit.COVER,
                    expand=True
                ),
                ft.Column(
                    [
                        ft.Container(height=50),
                        title,
                        self.date_field,
                        self.meal_type_dropdown,
                        ft.Row([btn_back, btn_next], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                )
            ],
            expand=True
        )
        return ft.Container(content=content, expand=True)
    
    # التحقق من الصفحة الأولى
    def validate_initial_page(self, e):
        if not self.meal_type_dropdown.value:
            self.show_snackbar("يرجى اختيار نوع الوجبة!")
            return
        self.page.clean()
        self.page.add(self.show_meal_selection())
    
    # الصفحة الثانية: اختيار الأصناف
    def show_meal_selection(self, e=None):
        title = ft.Text(
            "اختيار الأصناف المستهلكة",
            size=40,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )
        self.meal_options = self.get_meal_options()
        self.selected_meals = {}
        meal_checkboxes = []
        for meal in self.meal_options:
            var = ft.Checkbox(value=False)
            self.selected_meals[meal] = var
            meal_checkboxes.append(
                ft.Row(
                    [
                        ft.Text(meal, size=18, color=ft.colors.WHITE, expand=True, text_align=ft.TextAlign.RIGHT),
                        var,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        self.misc_var = ft.Checkbox(value=False)
        meal_checkboxes.append(
            ft.Row(
                [
                    ft.Text("مصاريف أخرى", size=18, color=ft.colors.WHITE, expand=True, text_align=ft.TextAlign.RIGHT),
                    self.misc_var,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )
        scrollable_frame = ft.ListView(
            controls=meal_checkboxes,
            height=300,
            width=300,
            spacing=10,
        )
        btn_next = create_button(
            "التالي",
            lambda e: self.validate_meal_selection(e),
            bgcolor=ft.colors.GREEN
        )
        btn_back = create_button(
            "رجوع",
            lambda e: [
                self.page.controls.clear(),
                self.page.add(self.show_initial_page()),
                self.page.update()
            ],
            bgcolor=ft.colors.RED
        )
        content = ft.Stack(
            [
                ft.Container(
                    image_src=self.background_image.src,
                    image_fit=ft.ImageFit.COVER,
                    expand=True
                ),
                ft.Column(
                    [
                        ft.Container(height=50),
                        title,
                        scrollable_frame,
                        ft.Row([btn_back, btn_next], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                )
            ],
            expand=True
        )
        return ft.Container(content=content, expand=True)
    
    # التحقق من اختيار الأصناف
    def validate_meal_selection(self, e):
        if not any(var.value for var in self.selected_meals.values()) and not self.misc_var.value:
            self.show_snackbar("يرجى اختيار صنف واحد على الأقل!")
            return
        self.page.clean()
        self.page.add(self.show_quantity_input())
    
    # الصفحة الثالثة: إدخال الكميات
    def show_quantity_input(self, e=None):
        title = ft.Text(
            "حدد الكميات لكل صنف",
            size=40,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )
        self.meal_quantities = {}
        quantity_fields = []
        for meal, var in self.selected_meals.items():
            if var.value:
                quantity_var = ft.TextField(
                    label=f"كمية {meal}",
                    value="",
                    width=300,
                    bgcolor=ft.colors.WHITE
                )
                self.meal_quantities[meal] = quantity_var
                quantity_fields.append(quantity_var)
        if self.misc_var.value:
            self.misc_amount_var = ft.TextField(
                label="مبلغ المصاريف الأخرى",
                value="",
                width=300,
                bgcolor=ft.colors.WHITE
            )
            quantity_fields.append(self.misc_amount_var)
        btn_next = create_button(
            "التالي",
            lambda e: self.validate_quantities(e),
            bgcolor=ft.colors.GREEN
        )
        btn_back = create_button(
            "رجوع",
            lambda e: [
                self.page.controls.clear(),
                self.page.add(self.show_meal_selection()),
                self.page.update()
            ],
            bgcolor=ft.colors.RED
        )
        content = ft.Stack(
            [
                ft.Container(
                    image_src=self.background_image.src,
                    image_fit=ft.ImageFit.COVER,
                    expand=True
                ),
                ft.Column(
                    [
                        ft.Container(height=40),
                        title,
                        *quantity_fields,
                        ft.Row([btn_back, btn_next], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                )
            ],
            expand=True
        )
        return ft.Container(content=content, expand=True)
    
    def validate_quantities(self, e):
        error_messages = []
        # التحقق من حقول الوجبات
        for meal, field in self.meal_quantities.items():
            value = field.value.strip()
            if not value:
                error_messages.append(f"حقل كمية {meal} مطلوب!")
                field.error_text = "هذا الحقل مطلوب"
                field.update()
            else:
                try:
                    quantity = int(value)
                    cursor = self.db.conn.cursor()
                    cursor.execute("SELECT remaining FROM expenses WHERE item_name = ?", (meal,))
                    remaining = cursor.fetchone()[0]
                    if quantity > remaining:
                        self.show_snackbar(f"الكمية المطلوبة لـ {meal} غير متوفرة!")
                        return
                except ValueError:
                    error_messages.append(f"حقل كمية {meal} يجب أن يكون عددًا صحيحًا!")
        # التحقق من المصاريف الأخرى
        if self.misc_var.value:
            misc_value = self.misc_amount_var.value.strip()
            if not misc_value:
                error_messages.append("حقل مبلغ المصاريف الأخرى مطلوب!")
                self.misc_amount_var.error_text = "هذا الحقل مطلوب"
                self.misc_amount_var.update()
            else:
                try:
                    float(misc_value)
                except ValueError:
                    error_messages.append("حقل مبلغ المصاريف الأخرى يجب أن يكون رقمًا!")
        if error_messages:
            for message in error_messages:
                self.show_snackbar(message)
            return
        # إذا لم يكن هناك أخطاء، ننتقل إلى صفحة اختيار الأعضاء
        self.page.clean()
        self.page.add(self.show_member_selection())
    
    # الصفحة الرابعة: اختيار الأعضاء
    def show_member_selection(self):
        title = ft.Text(
            "اختيار الأعضاء",
            size=40,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )
        member_options = self.get_member_options()
        self.member_selection = {}
        member_checkboxes = []
        for member in member_options:
            var = ft.Checkbox(value=False)
            self.member_selection[member] = var
            member_checkboxes.append(
                ft.Row(
                    [
                        ft.Text(member, size=18, color=ft.colors.WHITE, expand=True, text_align=ft.TextAlign.RIGHT),
                        var,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        scrollable_frame = ft.ListView(
            controls=member_checkboxes,
            height=300,
            width=300,
            spacing=10,
        )
        btn_save = create_button(
            "حفظ",
            lambda e: self.save_data(e),
            bgcolor=ft.colors.GREEN
        )
        btn_back = create_button(
            "رجوع",
            lambda e: [
                self.page.controls.clear(),
                self.page.add(self.show_quantity_input()),
                self.page.update()
            ],
            bgcolor=ft.colors.RED
        )
        content = ft.Stack(
            [
                ft.Container(
                    image_src=self.background_image.src,
                    image_fit=ft.ImageFit.COVER,
                    expand=True
                ),
                ft.Column(
                    [
                        ft.Container(height=50),
                        title,
                        scrollable_frame,
                        ft.Row([btn_back, btn_save], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                )
            ],
            expand=True
        )
        return ft.Container(content=content, expand=True)
    
    # حفظ البيانات
    def save_data(self, e):
        total_cost = 0
        try:
            cursor = self.db.conn.cursor()
            
            # تحديث الكميات للأصناف
            for meal, field in self.meal_quantities.items():
                quantity = int(field.value)
                cursor.execute("UPDATE expenses SET consumption = consumption + ?, remaining = remaining - ? WHERE item_name = ?", 
                              (quantity, quantity, meal))
                cursor.execute("SELECT price FROM expenses WHERE item_name = ?", (meal,))
                price = cursor.fetchone()[0]
                total_cost += quantity * price
            
            # اختيار الأعضاء
            selected_members = [member for member, var in self.member_selection.items() if var.value]
            if not selected_members:
                self.show_snackbar("لم يتم اختيار أي أعضاء!")
                return
            
            # حساب التكلفة لكل عضو
            cost_per_member = total_cost / len(selected_members)
            
            # معالجة المصاريف النثرية
            misc_expense_id = None
            misc_amount_per_member = 0
            if self.misc_var.value:
                misc_total = float(self.misc_amount_var.value)
                misc_amount_per_member = misc_total / len(selected_members)
                total_cost += misc_total
            
            # إدراج المصاريف النثرية وسجلات الوجبات
            for member in selected_members:
                # تحديث إجمالي المدين للمشترك
                cursor.execute("UPDATE members SET total_due = total_due + ? WHERE rank || ' ' || name = ?",
                              (cost_per_member + misc_amount_per_member, member))
                
                # الحصول على معرف العضو
                cursor.execute("SELECT member_id FROM members WHERE rank || ' ' || name = ?", (member,))
                member_id = cursor.fetchone()[0]
                
                # إدراج سجل الوجبة
                cursor.execute("INSERT INTO meal_records (meal_type, date, member_id, final_cost) VALUES (?, ?, ?, ?)",
                              (self.meal_type_dropdown.value, self.date_field.value, member_id, cost_per_member))
                meal_record_id = cursor.lastrowid
                
                # إدراج المصروف النثري المرتبط بالعضو والوجبة
                if self.misc_var.value:
                    cursor.execute("INSERT INTO miscellaneous_expenses (date, amount, meal_type, meal_record_id, member_id) VALUES (?, ?, ?, ?, ?)",
                                  (self.date_field.value, misc_amount_per_member, self.meal_type_dropdown.value, meal_record_id, member_id))
            
            self.db.conn.commit()
            self.show_snackbar("تم حفظ البيانات بنجاح!")
            self.navigate("meal_page")
        except Exception as e:
            self.db.conn.rollback()
            self.show_snackbar(f"حدث خطأ: {str(e)}")
    
    # وظائف مساعدة
    def get_meal_options(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT item_name FROM expenses WHERE is_drink = 0 AND is_miscellaneous = 0")
        return [row[0] for row in cursor.fetchall()]
    
    def get_member_options(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT rank || ' ' || name FROM members")
        return [row[0] for row in cursor.fetchall()]
    
    def show_snackbar(self, message):
        snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()
    
    def close_connection(self, e):
        if self.db.conn:
            self.db.conn.close()
