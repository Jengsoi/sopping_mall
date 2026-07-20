from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QDateEdit,
    QHBoxLayout, QPushButton
)

from PySide6.QtCore import Qt, QDate
from admin.client.dashboard_client import NetworkClient

from PySide6.QtGui import QFont, QColor, QPainter
from PySide6.QtCharts import (QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis,
                              QValueAxis, QPieSeries, QPieSlice, QLegend)

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("매출현황")
        self.resize(950, 750)

        main_layout = QVBoxLayout(self)

        date_layout = QHBoxLayout()
        date_layout.addStretch()

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())

        mid_label = QLabel(" ~ ")

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        self.search_button = QPushButton("조회")

        date_layout.addWidget(self.start_date)
        date_layout.addWidget(mid_label)
        date_layout.addWidget(self.end_date)
        date_layout.addWidget(self.search_button)

        main_layout.addLayout(date_layout)

        # 서버에 연결하는 파트
        self.client = NetworkClient("127.0.0.1", 6001)
        self.client.start()

        self.client.data_receive.connect(self.on_data_receive)
        self.client.connection_error.connect(self.on_connection_error)
        self.search_button.clicked.connect(self.on_search_clicked)

        # 매출 총액 라벨
        self.total_label = QLabel("총 매출액: 날짜를 조회하세요.")

        # 글꼴 설정
        font = QFont("Mailgun Gothic", 36)
        font.setBold(True)
        self.total_label.setFont(font)

        # 가운데 정렬 및 테두리 꾸미기
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_label.setStyleSheet("border: 2px solid #DCDCDC; padding: 15px;")

        main_layout.addWidget(self.total_label)

        # 차트 2개 나란히 배치
        charts_layout = QHBoxLayout()
        charts_layout.addWidget(self.make_bar_chart())
        charts_layout.addWidget(self.make_pie_chart())

        main_layout.addLayout(charts_layout)

    def on_search_clicked(self):
        start = self.start_date.date().toString("yyyy-MM-dd") + " 00:00:00"
        end = self.end_date.date().toString("yyyy-MM-dd") + " 23:59:59"
        self.client.send_request(start, end)

    def on_connection_error(self, error):
        print(f"서버 연결 실패 : {error}")

    def on_data_receive(self, message):
        message_type = message.get("type", "")
        content = message.get("content", "")

        if message_type == "total_sales":
            self.update_total_sales(content)
        if message_type == "product_top5":
            self.update_product_top5(content)
        if message_type == "category_sales":
            self.update_category_sales(content)

    def update_total_sales(self, content):
        if not content[0]['total_sales']:
            return

        total_sales = int(content[0]['total_sales'])
        self.total_label.setText(f"총 매출액: {total_sales:,} 원")

    def update_product_top5(self, content):
        self.bar_set.remove(0, self.bar_set.count())
        self.axis_x.clear()

        products = []
        amount = []
        max_sales = 0

        for item in content:
            name = item.get("product_name", "unknown")
            sales = int(item.get("total_sales", 0))

            sales_div_10000 = sales / 10000

            products.append(name)
            amount.append(sales_div_10000)

            if sales_div_10000 > max_sales:
                max_sales = sales_div_10000

        self.axis_x.append(products)
        self.bar_set.append(amount)

        if max_sales > 0:
            self.axis_y.setRange(0, max_sales * 1.2)

    def update_category_sales(self, content):

        self.pie_series.clear()

        total_category_sales = 0
        parsed_data = []

        for item in content:
            name = item.get("name", "unknown")
            sales = int(item.get("total_sales", 0))

            total_category_sales += sales
            parsed_data.append((name, sales))

            if total_category_sales == 0:
                return

        colors = ["#0D47A1", "#1976D2", "#2196F3", "#42A5F5", "#64B5F6", "#90CAF9" ]

        for i, (name,sales) in enumerate(parsed_data):

            percentage = round((sales / total_category_sales) * 100, 1)

            color_index = i % len(colors)
            color = colors[color_index]

            slice_item = self.pie_series.append(name, sales)
            slice_item.setBrush(QColor(color))
            slice_item.setLabelVisible(True)

            slice_item.setLabel(f"{name} {percentage}")
            slice_item.setLabelArmLengthFactor(0.05)

            slice_item.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)

    def make_bar_chart(self):
        self.bar_set = QBarSet("매출액")
        self.bar_set.append([0, 0, 0, 0, 0])  # 초기 빈 데이터
        self.bar_set.setBrush(QColor("#42A5F5"))

        self.bar_series = QBarSeries()
        self.bar_series.append(self.bar_set)
        self.bar_series.setLabelsVisible(True)

        chart = QChart()
        chart.addSeries(self.bar_series)
        chart.setTitle("매출 TOP 5 (매출액 기준 / 단위: 만원)")

        title_font = QFont("Mailgun Gothic", 12)
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(False)

        self.axis_x = QBarCategoryAxis()
        self.axis_x.append(["-", "-", "-", "-", "-"])  # 초기 빈 카테고리
        chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.bar_series.attachAxis(self.axis_x)

        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 600)
        self.axis_y.setLabelFormat("%d")
        chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        self.bar_series.attachAxis(self.axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        return chart_view

    def make_pie_chart(self):
        self.pie_series = QPieSeries()
        self.pie_series.setHoleSize(0.35)
        self.pie_series.setPieSize(0.70)

        chart = QChart()
        chart.addSeries(self.pie_series)
        chart.setTitle("카테고리별 매출 비중")

        title_font = QFont("Mailgun Gothic", 12)
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setMarkerShape(QLegend.MarkerShape.MarkerShapeRectangle)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        return chart_view





