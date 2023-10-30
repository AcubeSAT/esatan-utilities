import logging
from pathlib import Path

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import (
    QFileDialog, QGroupBox, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QWidget
)

from parse import read_csv, read_csv_meta
from plot import lineplot, setup_plots


class UtilsGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.csv = None
        setup_plots()
        self._init_ui()

    def _init_ui(self) -> None:
        self._create_io_group_box()
        self._create_plot_group_box()

        self.selected_csv_path = QLabel(self.tr("Selected CSV: "))

        main_layout = QVBoxLayout()
        main_layout.addWidget(self._io_group_box)
        main_layout.addWidget(self._plot_group_box)
        self.setLayout(main_layout)

        self.setWindowTitle(self.tr("ESATAN Utilities"))

        # To have widgets appear.
        dummy_widget = QWidget()
        dummy_widget.setLayout(main_layout)
        self.setCentralWidget(dummy_widget)

    def closeEvent(self, event: QEvent) -> None:
        logging.info("Application closed nominally.")
        super().closeEvent(event)

    def _create_io_group_box(self) -> None:
        self._io_group_box = QGroupBox(self.tr("IO"))
        layout = QHBoxLayout()

        browse_button = QPushButton(self.tr("Browse"))
        browse_button.clicked.connect(self._browse_csv)

        layout.addWidget(browse_button)

        self._io_group_box.setLayout(layout)

    def _create_plot_group_box(self) -> None:
        self._plot_group_box = QGroupBox(self.tr("Plot"))
        layout = QHBoxLayout()

        plot_button = QPushButton(self.tr("Plot"))
        plot_button.clicked.connect(self._plot_csv)

        layout.addWidget(plot_button)

        self._plot_group_box.setLayout(layout)

    def _browse_csv(self) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.List)
        dialog.setNameFilter(self.tr("CSV (*.csv)"))

        if dialog.exec():
            csv_filename = dialog.selectedFiles()[0]
            csv_filename = Path(csv_filename)

            self.selected_csv_path.setText(
                self.tr(f"Selected CSV: {csv_filename.name}")
            )

            meta_row_idx, meta_map = read_csv_meta(csv_filename)
            self.meta_map = meta_map
            self.csv = read_csv(csv_filename, meta_row_idx)

            logging.info(f"Loaded file {csv_filename.name} successfully.")

    def _plot_csv(self) -> None:
        if self.csv is None:
            logging.info("You have to load a CSV file first!")
        else:
            lineplot(
                self.csv, self.meta_map["Data Source"],
                self.meta_map["Element"], self.meta_map["Measurement Kind"]
            )
