import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, 
                           QTextEdit, QFrame, QStatusBar, QColorDialog,
                           QComboBox, QTabWidget, QGridLayout, QProgressBar,
                           QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                           QHeaderView)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
import requests
import threading
import time
import json
import csv
from bs4 import BeautifulSoup

class ScanThread(QThread):
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    complete_signal = pyqtSignal(list)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.results = []
        
    def run(self):
        self.update_signal.emit(f"بدء فحص الموقع: {self.url}\n")
        links = self.get_links(self.url)
        
        # إضافة الرابط الرئيسي إذا كانت قائمة الروابط فارغة
        if not links:
            links = [self.url]
        
        total_links = len(links)
        completed = 0
        
        for link in links:
            if not link.startswith("http"):
                link = self.url + link
            self.scan_website(link)
            completed += 1
            progress = int((completed / total_links) * 100)
            self.progress_signal.emit(progress)
            
        self.update_signal.emit("اكتمل الفحص!\n")
        self.complete_signal.emit(self.results)
    
    def get_links(self, url):
        try:
            self.update_signal.emit(f"استخراج الروابط من {url}...\n")
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = set()
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href.startswith('http'):
                    if href.startswith('/'):
                        href = url + href
                    else:
                        href = url + '/' + href
                links.add(href)
            
            self.update_signal.emit(f"تم العثور على {len(links)} رابط\n")
            return links
        except Exception as e:
            self.update_signal.emit(f"خطأ في استخراج الروابط: {str(e)}\n")
            return []
    
    def scan_website(self, url):
        self.update_signal.emit(f"فحص {url}...\n")
        
        # تحقق من وجود SQL Injection
        if self.check_sql_injection(url):
            self.update_signal.emit(f"تم العثور على ثغرة SQL Injection في {url}\n")
            self.results.append({"url": url, "vulnerability": "SQL Injection", "details": "High risk"})
        
        # تحقق من وجود XSS
        if self.check_xss(url):
            self.update_signal.emit(f"تم العثور على ثغرة XSS في {url}\n")
            self.results.append({"url": url, "vulnerability": "XSS", "details": "Medium risk"})
        
        # تحقق من وجود Command Injection
        if self.check_command_injection(url):
            self.update_signal.emit(f"تم العثور على ثغرة Command Injection في {url}\n")
            self.results.append({"url": url, "vulnerability": "Command Injection", "details": "Critical risk"})
        
        # تحقق من وجود Open Redirect
        if self.check_open_redirect(url):
            self.update_signal.emit(f"تم العثور على ثغرة Open Redirect في {url}\n")
            self.results.append({"url": url, "vulnerability": "Open Redirect", "details": "Low risk"})
        
        # تحقق من وجود CSRF
        if self.check_csrf(url):
            self.update_signal.emit(f"تم العثور على ثغرة CSRF في {url}\n")
            self.results.append({"url": url, "vulnerability": "CSRF", "details": "Medium risk"})
        
        # تحقق من وجود Directory Traversal
        if self.check_directory_traversal(url):
            self.update_signal.emit(f"تم العثور على ثغرة Directory Traversal في{url}\n")
            self.results.append({"url": url, "vulnerability": "Directory Traversal", "details": "High risk"})
    
    # -------------------- دوال فحص الثغرات --------------------
    def check_sql_injection(self, url):
        test_url = url + "'"
        try:
            response = requests.get(test_url, timeout=5)
            if "syntax" in response.text or "mysql" in response.text or "error" in response.text:
                return self.verify_sql_injection(url)
        except:
            pass
        return False

    def verify_sql_injection(self, url):
        payload = "' OR 1=1 -- "
        test_url = url + payload
        try:
            response = requests.get(test_url, timeout=5)
            if "error" in response.text:
                return True
        except:
            pass
        return False

    def check_xss(self, url):
        payload = "<script>alert('XSS')</script>"
        test_url = url + "?search=" + payload
        try:
            response = requests.get(test_url, timeout=5)
            if payload in response.text:
                return self.verify_xss(url)
        except:
            pass
        return False

    def verify_xss(self, url):
        payload = "<script>alert('Test XSS')</script>"
        test_url = url + "?search=" + payload
        try:
            response = requests.get(test_url, timeout=5)
            if payload in response.text:
                return True
        except:
            pass
        return False

    def check_command_injection(self, url):
        payload = "echo%20Hello%20World"
        test_url = url + "?command=" + payload
        try:
            response = requests.get(test_url, timeout=5)
            if "Hello World" in response.text:
                return self.verify_command_injection(url)
        except:
            pass
        return False

    def verify_command_injection(self, url):
        payload = "id"
        test_url = url + "?command=" + payload
        try:
            response = requests.get(test_url, timeout=5)
            if "uid" in response.text:
                return True
        except:
            pass
        return False

    def check_open_redirect(self, url):
        payload = "http://example.com"
        test_url = url + "?redirect=" + payload
        try:
            response = requests.get(test_url, timeout=5)
            if "example.com" in response.text:
                return self.verify_open_redirect(url)
        except:
            pass
        return False

    def verify_open_redirect(self, url):
        payload = "http://test.com"
        test_url = url + "?redirect=" + payload
        try:
            response = requests.get(test_url, timeout=5)
            if "test.com" in response.text:
                return True
        except:
            pass
        return False

    def check_csrf(self, url):
        try:
            response = requests.get(url, timeout=5)
            if "csrf" not in response.text:
                return True
        except:
            pass
        return False

    def check_directory_traversal(self, url):
        payload = "/../../../etc/passwd"
        test_url = url + payload
        try:
            response = requests.get(test_url, timeout=5)
            if "root" in response.text:
                return self.verify_directory_traversal(url)
        except:
            pass
        return False

    def verify_directory_traversal(self, url):
        payload = "/../../../../etc/passwd"
        test_url = url + payload
        try:
            response = requests.get(test_url, timeout=5)
            if "root" in response.text:
                return True
        except:
            pass
        return False


class SecurityScannerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("أداة فحص أمان تطبيقات الويب")
        self.setMinimumSize(1000, 700)
        
        # تعريف الألوان الرئيسية
        self.themes = {
            "بنفسجي داكن": {
                "primary": "#6A0DAD",     # بنفسجي داكن
                "secondary": "#9B30FF",   # بنفسجي فاتح
                "accent": "#E0B0FF",      # بنفسجي خفيف
                "dark": "#121212",        # أسود
                "light": "#FFFFFF",       # أبيض
                "text_dark": "#333333",   # نص داكن
                "text_light": "#FFFFFF",  # نص فاتح
                "success": "#4CAF50",     # أخضر للنجاح
                "warning": "#FF9800",     # برتقالي للتحذير
                "danger": "#F44336"       # أحمر للخطر
            },
            "بنفسجي فاتح": {
                "primary": "#9370DB",     # بنفسجي متوسط
                "secondary": "#BA55D3",   # بنفسجي زهري
                "accent": "#D8BFD8",      # بنفسجي خفيف جداً
                "dark": "#333333",        # رمادي داكن
                "light": "#F8F8F8",       # أبيض مائل للرمادي
                "text_dark": "#333333",
                "text_light": "#FFFFFF",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "danger": "#F44336"
            },
            "مخصص": {
                "primary": "#6A0DAD",
                "secondary": "#9B30FF",
                "accent": "#E0B0FF",
                "dark": "#121212",
                "light": "#FFFFFF",
                "text_dark": "#333333",
                "text_light": "#FFFFFF",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "danger": "#F44336"
            }
        }
        
        self.current_theme = "بنفسجي داكن"
        self.results = []
        
        # إنشاء الهيكل الرئيسي للواجهة
        self.create_ui()
        
        # تطبيق السمة الافتراضية
        self.apply_theme(self.current_theme)
    
    def create_ui(self):
        # إنشاء ويدجت مركزي
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # إنشاء الشريط الجانبي
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        # عنوان الأداة في الشريط الجانبي
        app_title = QLabel("فاحص أمان الويب")
        app_title.setObjectName("app_title")
        app_title.setAlignment(Qt.AlignCenter)
        
        # أزرار التنقل
        self.scan_button = QPushButton("فحص جديد")
        self.scan_button.setObjectName("nav_button")
        self.scan_button.setCheckable(True)
        self.scan_button.setChecked(True)
        self.scan_button.clicked.connect(lambda: self.switch_tab(0))
        
        self.results_button = QPushButton("النتائج")
        self.results_button.setObjectName("nav_button")
        self.results_button.setCheckable(True)
        self.results_button.clicked.connect(lambda: self.switch_tab(1))
        
        self.report_button = QPushButton("التقارير")
        self.report_button.setObjectName("nav_button")
        self.report_button.setCheckable(True)
        self.report_button.clicked.connect(lambda: self.switch_tab(2))
        
        self.settings_button = QPushButton("الإعدادات")
        self.settings_button.setObjectName("nav_button")
        self.settings_button.setCheckable(True)
        self.settings_button.clicked.connect(lambda: self.switch_tab(3))
        
        # مجموعة الأزرار للتنقل
        self.nav_buttons = [self.scan_button, self.results_button, self.report_button, self.settings_button]
        
        # إضافة العناصر إلى الشريط الجانبي
        sidebar_layout.addWidget(app_title)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(self.scan_button)
        sidebar_layout.addWidget(self.results_button)
        sidebar_layout.addWidget(self.report_button)
        sidebar_layout.addWidget(self.settings_button)
        sidebar_layout.addStretch()
        
        # إضافة قسم اختيار السمات
        theme_label = QLabel("تغيير السمة:")
        theme_label.setObjectName("theme_label")
        
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(list(self.themes.keys()))
        self.theme_selector.setCurrentText(self.current_theme)
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        
        sidebar_layout.addWidget(theme_label)
        sidebar_layout.addWidget(self.theme_selector)
        sidebar_layout.addSpacing(20)
        
        # إنشاء التبويبات الرئيسية
        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(True)  # إخفاء شريط التبويب
        
        # تبويب الفحص
        scan_tab = QWidget()
        scan_layout = QVBoxLayout(scan_tab)
        
        header = QLabel("فحص أمان تطبيقات الويب")
        header.setObjectName("page_header")
        
        description = QLabel("قم بإدخال رابط الموقع المراد فحصه للكشف عن الثغرات الأمنية المحتملة")
        description.setObjectName("description")
        
        # مربع إدخال الرابط
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("أدخل رابط الموقع... (مثال: http://example.com)")
        self.url_input.setObjectName("url_input")
        
        self.start_button = QPushButton("بدء الفحص")
        self.start_button.setObjectName("primary_button")
        self.start_button.clicked.connect(self.start_scan)
        
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.start_button)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        
        # منطقة عرض النتائج
        output_label = QLabel("سجل الفحص:")
        output_label.setObjectName("section_header")
        
        self.output_area = QTextEdit()
        self.output_area.setObjectName("output_area")
        self.output_area.setReadOnly(True)
        
        # أزرار حفظ النتائج
        actions_layout = QHBoxLayout()
        self.save_json_button = QPushButton("حفظ كـ JSON")
        self.save_json_button.setObjectName("secondary_button")
        self.save_json_button.clicked.connect(lambda: self.save_results("json"))
        
        self.save_csv_button = QPushButton("حفظ كـ CSV")
        self.save_csv_button.setObjectName("secondary_button")
        self.save_csv_button.clicked.connect(lambda: self.save_results("csv"))
        
        self.clear_button = QPushButton("مسح النتائج")
        self.clear_button.setObjectName("danger_button")
        self.clear_button.clicked.connect(self.clear_results)
        
        actions_layout.addWidget(self.save_json_button)
        actions_layout.addWidget(self.save_csv_button)
        actions_layout.addWidget(self.clear_button)
        
        # إضافة كل العناصر إلى تبويب الفحص
        scan_layout.addWidget(header)
        scan_layout.addWidget(description)
        scan_layout.addLayout(url_layout)
        scan_layout.addWidget(self.progress_bar)
        scan_layout.addWidget(output_label)
        scan_layout.addWidget(self.output_area)
        scan_layout.addLayout(actions_layout)
        
        # تبويب النتائج
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        results_header = QLabel("نتائج الفحص")
        results_header.setObjectName("page_header")
        
        # جدول النتائج
        self.results_table = QTableWidget(0, 3)
        self.results_table.setObjectName("results_table")
        self.results_table.setHorizontalHeaderLabels(["الرابط", "الثغرة", "التفاصيل"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        results_layout.addWidget(results_header)
        results_layout.addWidget(self.results_table)
        
        # تبويب التقارير
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        
        report_header = QLabel("التقارير والإحصائيات")
        report_header.setObjectName("page_header")
        
        # محتوى مؤقت لتبويب التقارير
        report_content = QLabel("سيتم إضافة إحصائيات ورسوم بيانية هنا في الإصدارات القادمة")
        report_content.setAlignment(Qt.AlignCenter)
        
        report_layout.addWidget(report_header)
        report_layout.addWidget(report_content)
        
        # تبويب الإعدادات
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        settings_header = QLabel("إعدادات التطبيق")
        settings_header.setObjectName("page_header")
        
        # إعدادات الألوان
        color_section = QLabel("تخصيص الألوان:")
        color_section.setObjectName("section_header")
        
        colors_grid = QGridLayout()
        
        # أزرار اختيار الألوان
        self.primary_color_btn = QPushButton("اختيار اللون الرئيسي")
        self.primary_color_btn.clicked.connect(lambda: self.pick_custom_color("primary"))
        
        self.secondary_color_btn = QPushButton("اختيار اللون الثانوي")
        self.secondary_color_btn.clicked.connect(lambda: self.pick_custom_color("secondary"))
        
        self.accent_color_btn = QPushButton("اختيار لون التمييز")
        self.accent_color_btn.clicked.connect(lambda: self.pick_custom_color("accent"))
        
        self.dark_color_btn = QPushButton("اختيار اللون الداكن")
        self.dark_color_btn.clicked.connect(lambda: self.pick_custom_color("dark"))
        
        colors_grid.addWidget(self.primary_color_btn, 0, 0)
        colors_grid.addWidget(self.secondary_color_btn, 0, 1)
        colors_grid.addWidget(self.accent_color_btn, 1, 0)
        colors_grid.addWidget(self.dark_color_btn, 1, 1)
        
        # إضافة العناصر إلى تبويب الإعدادات
        settings_layout.addWidget(settings_header)
        settings_layout.addWidget(color_section)
        settings_layout.addLayout(colors_grid)
        settings_layout.addStretch()
        
        # إضافة التبويبات إلى مدير التبويبات
        self.tabs.addTab(scan_tab, "الفحص")
        self.tabs.addTab(results_tab, "النتائج")
        self.tabs.addTab(report_tab, "التقارير")
        self.tabs.addTab(settings_tab, "الإعدادات")
        
        # إضافة العناصر إلى التخطيط الرئيسي
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.tabs)
        
        # إضافة شريط الحالة
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("جاهز")
        self.setStatusBar(self.status_bar)
        
        # تعيين الويدجت المركزي
        self.setCentralWidget(central_widget)
    
    def switch_tab(self, index):
        self.tabs.setCurrentIndex(index)
        
        # تحديث حالة أزرار التنقل
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
    
    def apply_theme(self, theme_name):
        theme = self.themes[theme_name]
        
        # تطبيق السمة على الواجهة بالكامل
        style_sheet = f"""
            QMainWindow {{
                background-color: {theme["light"]};
                color: {theme["text_dark"]};
            }}
            
            QLabel {{
                color: {theme["text_dark"]};
            }}
            
            QLabel#app_title {{
                font-size: 18px;
                font-weight: bold;
                color: {theme["text_light"]};
                padding: 10px;
            }}
            
            QLabel#page_header {{
                font-size: 24px;
                font-weight: bold;
                color: {theme["primary"]};
                padding: 10px 0;
            }}
            
            QLabel#section_header {{
                font-size: 16px;
                font-weight: bold;
                color: {theme["secondary"]};
                padding: 5px 0;
            }}
            
            QLabel#description {{
                color: {theme["text_dark"]};
                padding: 5px 0;
                margin-bottom: 10px;
            }}
            
            QLabel#theme_label {{
                color: {theme["text_light"]};
                padding: 5px 0;
            }}
            
            QFrame#sidebar {{
                background-color: {theme["dark"]};
                border-radius: 0px;
                padding: 20px 10px;
            }}
            
            QPushButton#nav_button {{
                background-color: transparent;
                color: {theme["text_light"]};
                border: none;
                padding: 12px;
                text-align: right;
                font-size: 14px;
                border-radius: 5px;
            }}
            
            QPushButton#nav_button:hover {{
                background-color: {theme["primary"]};
            }}
            
            QPushButton#nav_button:checked {{
                background-color: {theme["primary"]};
                font-weight: bold;
            }}
            
            QPushButton#primary_button {{
                background-color: {theme["primary"]};
                color: {theme["text_light"]};
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }}
            
            QPushButton#primary_button:hover {{
                background-color: {theme["secondary"]};
            }}
            
            QPushButton#secondary_button {{
                background-color: {theme["secondary"]};
                color: {theme["text_light"]};
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }}
            
            QPushButton#secondary_button:hover {{
                background-color: {theme["primary"]};
            }}
            
            QPushButton#danger_button {{
                background-color: {theme["danger"]};
                color: {theme["text_light"]};
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }}
            
            QPushButton#danger_button:hover {{
                background-color: #C62828;
            }}
            
            QLineEdit {{
                padding: 10px;
                border: 1px solid {theme["secondary"]};
                border-radius: 5px;
                background-color: {theme["light"]};
                color: {theme["text_dark"]};
                font-size: 14px;
            }}
            
            QLineEdit:focus {{
                border: 2px solid {theme["primary"]};
            }}
            
            QTextEdit {{
                background-color: {theme["light"]};
                color: {theme["text_dark"]};
                border: 1px solid {theme["accent"]};
                border-radius: 5px;
                padding: 5px;
                font-family: Consolas, Monaco, monospace;
            }}
            
            QProgressBar {{
                border: 1px solid {theme["accent"]};
                border-radius: 3px;
                text-align: center;
                background-color: {theme["light"]};
                color: {theme["text_dark"]};
                height: 20px;
            }}
            
            QProgressBar::chunk {{
                background-color: {theme["primary"]};
                width: 10px;
                margin: 0.5px;
            }}
            
            QComboBox {{
                padding: 5px;
                border: 1px solid {theme["accent"]};
                border-radius: 5px;
                background-color: {theme["light"]};
                color: {theme["text_dark"]};
                min-width: 100px;
            }}
            
            QTableWidget {{
                background-color: {theme["light"]};
                alternate-background-color: {theme["accent"]};
                border: 1px solid {theme["accent"]};
                border-radius: 5px;
            }}
            
            QHeaderView::section {{
                background-color: {theme["primary"]};
                color: {theme["text_light"]};
                padding: 5px;
                border: 1px solid {theme["accent"]};
                font-weight: bold;
            }}
        """
        
        self.setStyleSheet(style_sheet)
        self.current_theme = theme_name
    
    def change_theme(self, theme_name):
        self.apply_theme(theme_name)
    
    def pick_custom_color(self, color_key):
        color = QColorDialog.getColor()
        if color.isValid():
            self.themes["مخصص"][color_key] = color.name()
            if self.current_theme == "مخصص":
                self.apply_theme("مخصص")
            else:
                self.theme_selector.setCurrentText("مخصص")
    
    def start_scan(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال رابط موقع للفحص")
            return
        
        # إضافة http:// إذا لم يكن موجودًا
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            self.url_input.setText(url)
        
        # تفريغ النتائج السابقة
        self.output_area.clear()
        self.results = []
        self.progress_bar.setValue(0)
        
        # تعطيل زر البدء أثناء عملية الفحص
        self.start_button.setEnabled(False)
        self.start_button.setText("جاري الفحص...")
        self.status_bar.showMessage("جاري الفحص...")
        
        # بدء مهمة الفحص في خيط منفصل
        self.scan_thread = ScanThread(url)
        self.scan_thread.update_signal.connect(self.update_output)
        self.scan_thread.progress_signal.connect(self.update_progress)
        self.scan_thread.complete_signal.connect(self.scan_completed)
        self.scan_thread.start()
    
    def update_output(self, text):
        self.output_area.append(text)
        # التمرير إلى الأسفل
        self.output_area.verticalScrollBar().setValue(self.output_area.verticalScrollBar().maximum())
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def scan_completed(self, results):
        self.results = results
        
        # تحديث جدول النتائج
        self.update_results_table()
        
        # إعادة تفعيل زر البدء
        self.start_button.setEnabled(True)
        self.start_button.setText("بدء الفحص")
        
        # تحديث شريط الحالة
        self.status_bar.showMessage(f"اكتمل الفحص. تم العثور على {len(results)} ثغرة.")
        
        # رسالة إكمال الفحص
        if results:
            QMessageBox.information(self, "اكتمل الفحص", f"تم العثور على {len(results)} ثغرة أمنية.")
        else:
            QMessageBox.information(self, "اكتمل الفحص", "لم يتم العثور على ثغرات أمنية.")
    
    def update_results_table(self):
        # تفريغ الجدول
        self.results_table.setRowCount(0)
        
        # ملء الجدول بالنتائج
        for i, result in enumerate(self.results):
            self.results_table.insertRow(i)
            
            url_item = QTableWidgetItem(result["url"])
            vuln_item = QTableWidgetItem(result["vulnerability"])
            details_item = QTableWidgetItem(result.get("details", ""))
            
            # تلوين خلايا الجدول حسب درجة الخطورة
            if "Critical" in details_item.text() or "High" in details_item.text():
                details_item.setBackground(QColor(self.themes[self.current_theme]["danger"]))
                details_item.setForeground(QColor(self.themes[self.current_theme]["text_light"]))
            elif "Medium" in details_item.text():
                details_item.setBackground(QColor(self.themes[self.current_theme]["warning"]))
            
            self.results_table.setItem(i, 0, url_item)
            self.results_table.setItem(i, 1, vuln_item)
            self.results_table.setItem(i, 2, details_item)
    
    def save_results(self, format_type):
        if not self.results:
            QMessageBox.warning(self, "تنبيه", "لا توجد نتائج للحفظ.")
            return
        
        if format_type == "json":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "حفظ النتائج", "scan_results.json", "JSON Files (*.json)"
            )
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(self.results, f, indent=4, ensure_ascii=False)
                    QMessageBox.information(self, "تم الحفظ", f"تم حفظ النتائج في {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {str(e)}")
        
        elif format_type == "csv":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "حفظ النتائج", "scan_results.csv", "CSV Files (*.csv)"
            )
            if file_path:
                try:
                    with open(file_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=["url", "vulnerability", "details"])
                        writer.writeheader()
                        writer.writerows(self.results)
                    QMessageBox.information(self, "تم الحفظ", f"تم حفظ النتائج في {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {str(e)}")
    
    def clear_results(self):
        if not self.output_area.toPlainText() and not self.results:
            return
            
        reply = QMessageBox.question(
            self, "تأكيد المسح", 
            "هل أنت متأكد من مسح جميع نتائج الفحص؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.output_area.clear()
            self.results = []
            self.results_table.setRowCount(0)
            self.progress_bar.setValue(0)
            self.status_bar.showMessage("تم مسح النتائج")


# دالة لتشغيل التطبيق
def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)  # دعم اللغة العربية
    window = SecurityScannerUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()