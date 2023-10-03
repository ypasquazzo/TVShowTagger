import json
import logging
import sys

from PyQt6.QtCore import QByteArray, pyqtSignal, Qt, QThread
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox,
                             QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from utilities.web_query import WebQuery
from utilities.db_handler import DbHandler
from interface.editing_ui import SeriesEditorUI
from interface.info_ui import ShowDetailsWidget

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 425
WINDOW_TITLE = "TVShowTagger"
WINDOW_ICON_PATH = '../image/epguides.png'
TV_SHOWS_JSON_PATH = '../utilities/tv_shows_list.json'
NO_SERIES_MSG = "No series found. Please refresh list."
WARNING_TITLE = "Warning"
NO_ITEM_SELECTED_MSG = "No item selected."


class UpdateShowsThread(QThread):
    update_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            WebQuery.update_shows()
            self.update_finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))


class TVShowSeekerMainWindow(QMainWindow):
    """Main window class for the TV Show Seeker application."""

    def __init__(self) -> None:
        super().__init__()
        logging.info("Initializing TVShowSeekerMainWindow...")

        self.setGeometry(200, 200, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(WINDOW_ICON_PATH))

        # Initialize the primary components of the main window
        self.details_widget = None
        self.web_query_handler = WebQuery()
        self.db = DbHandler()
        self.tv_show_data = {}

        self.update_thread = UpdateShowsThread()
        self.update_thread.update_finished.connect(self.load_tv_shows_to_list)
        self.update_thread.error_occurred.connect(self.handle_update_error)

        # GUI components
        self.main_layout = QVBoxLayout()

        # Search box components
        self.search_layout = None
        self.search_label = None
        self.search_input = None

        # Refresh button components
        self.refresh_button = None
        self.refresh_button_layout = None
        self.waiting_label = None

        # Show list and details button components
        self.show_list_layout = None
        self.show_list_widget = None
        self.show_details_button = None

        # Select button components
        self.select_show_button = None
        self.select_button_layout = None

        self.initialize_ui()

    def initialize_ui(self) -> None:
        """Sets up the main UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.setup_search_box_ui()
        self.setup_refresh_button_ui()
        self.setup_waiting_label_ui()

        self.setup_show_list_and_details_button_ui()
        self.setup_select_button_ui()

        central_widget.setLayout(self.main_layout)

        self.load_tv_shows_to_list()

    def setup_search_box_ui(self) -> None:
        """Sets up the search box components."""
        self.search_layout = QHBoxLayout()
        self.search_label = QLabel("Search for a TV SHOW:")
        self.search_input = QLineEdit()
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.filter_tv_show_list)
        self.search_layout.addStretch()
        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addStretch()
        self.main_layout.addLayout(self.search_layout)

    def setup_refresh_button_ui(self) -> None:
        """Sets up the refresh button."""
        self.refresh_button = QPushButton("Refresh list")
        self.refresh_button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed))
        self.refresh_button.clicked.connect(self.update_and_refresh_tv_shows)
        self.refresh_button_layout = QHBoxLayout()
        self.refresh_button_layout.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.refresh_button_layout)

    def setup_waiting_label_ui(self) -> None:
        """Sets up the waiting label with a message."""
        self.waiting_label = QLabel("Updating TV Shows...")
        self.waiting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.waiting_label.setHidden(True)
        self.main_layout.addWidget(self.waiting_label)

    def setup_show_list_and_details_button_ui(self) -> None:
        """Sets up the show list and its associated details button."""
        self.show_list_layout = QHBoxLayout()
        self.show_list_widget = QListWidget()
        self.show_details_button = QPushButton("Check TV Show")
        self.show_details_button.clicked.connect(self.open_show_details_ui)
        self.show_list_layout.addWidget(self.show_list_widget)
        self.show_list_layout.addWidget(self.show_details_button)
        self.main_layout.addLayout(self.show_list_layout)

    def setup_select_button_ui(self) -> None:
        """Sets up the select button."""
        self.select_show_button = QPushButton("Select")
        self.select_show_button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed))
        self.select_show_button.clicked.connect(self.display_selected_show)
        self.select_button_layout = QHBoxLayout()
        self.select_button_layout.addWidget(self.select_show_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.select_button_layout)

    def update_and_refresh_tv_shows(self) -> None:
        """Initiates the threaded process to update and refresh TV shows."""
        logging.info("Starting TV shows update...")

        self.toggle_buttons(False)
        self.waiting_label.setHidden(False)
        self.update_thread.start()

    def handle_update_error(self, error_msg: str) -> None:
        """Displays an error message and re-enables the UI buttons."""
        logging.error(f"Error occurred during shows update: {error_msg}")

        QMessageBox.warning(self, "Error", f"Unable to update shows: {error_msg}")
        self.toggle_buttons(True)

    def load_tv_shows_to_list(self) -> None:
        """Loads shows from the JSON file and populates the list widget."""
        logging.info("Loading TV shows from JSON file...")

        self.show_list_widget.clear()
        try:
            with open(TV_SHOWS_JSON_PATH, 'r', encoding='utf-8') as file:
                self.tv_show_data = json.load(file)
                for show_title in self.tv_show_data.keys():
                    self.show_list_widget.addItem(show_title)
        except FileNotFoundError:
            logging.warning("TV Shows file not found.")
            QMessageBox.warning(self, "Warning", "TV Shows file not found, please refresh list.")
        except json.JSONDecodeError:
            logging.error("Error decoding the TV Shows file.")
            QMessageBox.warning(self, "Error", "Error decoding the TV Shows file!")
        finally:
            self.toggle_buttons(True)
            self.waiting_label.setHidden(True)

    def toggle_buttons(self, state: bool) -> None:
        """Toggles the state of UI buttons between enabled and disabled."""
        self.refresh_button.setEnabled(state)
        self.show_details_button.setEnabled(state)
        self.select_show_button.setEnabled(state)

    def filter_tv_show_list(self) -> None:
        """Filters shows in the list widget based on the search input."""
        filter_text = self.search_input.text().lower()
        self.show_list_widget.clear()

        for show_title in self.tv_show_data.keys():
            if filter_text in show_title.lower():
                self.show_list_widget.addItem(show_title)

    def get_selected_show_title(self) -> str:
        """Returns the title of the currently selected show or None if no show is selected."""
        selected_items = self.show_list_widget.selectedItems()
        return selected_items[0].text() if selected_items else None

    def fetch_selected_show_data(self) -> dict[str, str, str, str, QByteArray, str]:
        """Fetches data for the selected show."""
        selected_show_title = self.get_selected_show_title()
        logging.info(f"Fetching data for selected show: {selected_show_title}")

        if selected_show_title:
            show_info = {selected_show_title: self.tv_show_data[selected_show_title]}
            data = self.db.select(show_info)
            if not data:
                data = WebQuery.get_info(show_info)
                self.db.insert(data["name"], data["date"], data["time"], data["synopsis"], bytes(data["poster"]))
            if data["name"]:
                return data

            return {"name": "", "date": "", "time": "", "synopsis": "", "poster": "", "url": data["URL"]}
        else:
            logging.warning("No show selected to fetch data.")
            QMessageBox.warning(self, WARNING_TITLE, NO_ITEM_SELECTED_MSG)
            return {}

    def open_show_details_ui(self) -> None:
        """Opens the ShowDetailsWidget for the selected show."""
        logging.info("Opening ShowDetailsWidget for selected show.")

        data = self.fetch_selected_show_data()
        if data:
            self.details_widget = ShowDetailsWidget(data)
            self.details_widget.show()

    def display_selected_show(self) -> None:
        """Displays the selected show in the editing interface."""
        selected_show_title = self.get_selected_show_title()
        logging.info(f"Displaying selected show in editing interface: {selected_show_title}")

        if selected_show_title:
            self.db.close()
            self.load_editing_interface(selected_show_title)
        else:
            logging.warning("No show selected for editing.")
            QMessageBox.warning(self, WARNING_TITLE, NO_ITEM_SELECTED_MSG)

    def load_editing_interface(self, selected_show_title) -> None:
        """Loads the EditingUI for the selected show."""
        logging.info(f"Loading EditingUI for selected show: {selected_show_title}")

        self.setCentralWidget(SeriesEditorUI({selected_show_title: self.tv_show_data[selected_show_title]}, self))

    def reload_main_interface(self) -> None:
        """Reloads the main interface."""
        self.setCentralWidget(TVShowSeekerMainWindow())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main_window = TVShowSeekerMainWindow()
    main_window.show()
    app.exec()
