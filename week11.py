import sys
import csv
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QScrollArea, QDockWidget, QStatusBar
)
from PyQt5.QtCore import Qt

DB_NAME = "film.db"

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aplikasi Film")
        self.setGeometry(100, 100, 800, 600)

        self.editing_id = None
        self.is_updating_table = False

        self.setup_ui()
        self.setup_database()
        self.load_data()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        main_layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        self.judul_input = QLineEdit()
        self.judul_input.setPlaceholderText("Judul Film")
        self.sutradara_input = QLineEdit()
        self.sutradara_input.setPlaceholderText("Sutradara")
        self.tahun_input = QLineEdit()
        self.tahun_input.setPlaceholderText("Tahun Rilis")
        self.paste_clipboard_btn = QPushButton("Paste")
        self.paste_clipboard_btn.clicked.connect(self.paste_from_clipboard)

        form_layout.addWidget(self.judul_input)
        form_layout.addWidget(self.sutradara_input)
        form_layout.addWidget(self.tahun_input)
        form_layout.addWidget(self.paste_clipboard_btn)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Simpan")
        self.export_btn = QPushButton("Ekspor CSV")
        self.delete_btn = QPushButton("Hapus")
        self.save_btn.clicked.connect(self.simpan_data)
        self.export_btn.clicked.connect(self.ekspor_csv)
        self.delete_btn.clicked.connect(self.hapus_data)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.delete_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari Judul Film...")
        self.search_input.textChanged.connect(self.cari_judul)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Judul", "Sutradara", "Tahun"])
        self.table.itemChanged.connect(self.perbarui_data_di_database)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.search_input)
        main_layout.addWidget(self.table)

        self.central_widget.setLayout(main_layout)
        self.scroll.setWidget(self.central_widget)
        self.setCentralWidget(self.scroll)

        self.setup_dock_widget()
        self.setup_status_bar()

    def setup_database(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.db_cursor = self.conn.cursor()
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS film (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judul TEXT NOT NULL,
                sutradara TEXT NOT NULL,
                tahun TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def setup_dock_widget(self):
        dock = QDockWidget("Bantuan", self)
        label = QLabel("📌 Petunjuk:\n- Isi data film.\n- Klik simpan.\n- Edit langsung di tabel juga bisa.\n- Gunakan fitur cari.")
        label.setWordWrap(True)
        dock.setWidget(label)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def setup_status_bar(self):
        status_bar = QStatusBar()
        status_bar.showMessage("Andi Sibwayiq - F1D022002")
        self.setStatusBar(status_bar)

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        self.judul_input.setText(clipboard.text())

    def load_data(self):
        self.is_updating_table = True
        self.table.setRowCount(0)
        self.db_cursor.execute("SELECT * FROM film")
        for row_index, row_data in enumerate(self.db_cursor.fetchall()):
            self.table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(data)))
        self.is_updating_table = False

    def simpan_data(self):
        judul = self.judul_input.text()
        sutradara = self.sutradara_input.text()
        tahun = self.tahun_input.text()

        if not (judul and sutradara and tahun):
            QMessageBox.warning(self, "Input Error", "Semua field harus diisi!")
            return
        if not tahun.isdigit():
            QMessageBox.warning(self, "Input Error", "Tahun harus berupa angka!")
            return

        if self.editing_id is not None:
            self.db_cursor.execute(
                "UPDATE film SET judul = ?, sutradara = ?, tahun = ? WHERE id = ?",
                (judul, sutradara, tahun, self.editing_id)
            )
            QMessageBox.information(self, "Sukses", "Data berhasil diperbarui.")
        else:
            self.db_cursor.execute(
                "INSERT INTO film (judul, sutradara, tahun) VALUES (?, ?, ?)",
                (judul, sutradara, tahun)
            )
            QMessageBox.information(self, "Sukses", "Data berhasil disimpan.")

        self.conn.commit()
        self.load_data()
        self.judul_input.clear()
        self.sutradara_input.clear()
        self.tahun_input.clear()
        self.editing_id = None

    def ekspor_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        with open(path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            headers = ["ID", "Judul", "Sutradara", "Tahun"]
            writer.writerow(headers)
            for row in range(self.table.rowCount()):
                data_row = [self.table.item(row, col).text() if self.table.item(row, col) else '' for col in range(self.table.columnCount())]
                writer.writerow(data_row)

        QMessageBox.information(self, "Sukses", "Data berhasil diekspor ke CSV.")

    def cari_judul(self):
        keyword = self.search_input.text().strip().lower()
        self.table.setRowCount(0)
        if keyword == "":
            self.load_data()
            return
        self.db_cursor.execute("SELECT * FROM film WHERE LOWER(judul) LIKE ?", ('%' + keyword + '%',))
        for row_index, row_data in enumerate(self.db_cursor.fetchall()):
            self.table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(data)))

    def hapus_data(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            item = self.table.item(selected_row, 0)
            if item:
                reply = QMessageBox.question(
                    self, "Konfirmasi Hapus", "Apakah Anda yakin ingin menghapus data ini?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    film_id = int(item.text())
                    self.db_cursor.execute("DELETE FROM film WHERE id = ?", (film_id,))
                    self.conn.commit()
                    self.load_data()
        else:
            QMessageBox.warning(self, "Peringatan", "Pilih baris yang akan dihapus.")

    def perbarui_data_di_database(self, item):
        if self.is_updating_table:
            return  
        row = item.row()

        id_item = self.table.item(row, 0)
        judul_item = self.table.item(row, 1)
        sutradara_item = self.table.item(row, 2)
        tahun_item = self.table.item(row, 3)

        if not all([id_item, judul_item, sutradara_item, tahun_item]):
            return  

        try:
            film_id = int(id_item.text())
            judul = judul_item.text().strip()
            sutradara = sutradara_item.text().strip()
            tahun = tahun_item.text().strip()

            if not (judul and sutradara and tahun):
                QMessageBox.warning(self, "Validasi Gagal", "Semua kolom harus diisi.")
                return
            if not tahun.isdigit():
                QMessageBox.warning(self, "Validasi Gagal", "Tahun harus berupa angka.")
                return

            self.db_cursor.execute(
                "UPDATE film SET judul = ?, sutradara = ?, tahun = ? WHERE id = ?",
                (judul, sutradara, tahun, film_id)
            )
            self.conn.commit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memperbarui data: {str(e)}")

    def closeEvent(self, event):
        self.conn.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
