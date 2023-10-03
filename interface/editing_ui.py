import logging
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFileSystemModel, QFont, QIcon, QKeyEvent, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QTreeView, QHBoxLayout, QGroupBox, QCheckBox,
                             QSizePolicy, QFileDialog, QAbstractItemView, QMessageBox)

from utilities.web_query import WebQuery

FOLDER_ICON_PATH = "../image/folder.png"
VIDEO_ICON_PATH = "../image/video.png"
SELECTED_SEASONS_LABEL_TEXT = "Selected seasons"
CHECK_ALL_BUTTON_TEXT = "Check All"
UNCHECK_ALL_BUTTON_TEXT = "UnCheck All"
LOAD_FILES_BUTTON_TEXT = "Load files"
BUTTON_FIXED_HEIGHT = 25
MAX_CHECKBOX_PER_ROW = 5


def _get_all_checkboxes_in_group(group_layout: QVBoxLayout) -> list[QCheckBox]:
    """Retrieves all QCheckBox widgets present in a QVBoxLayout."""
    checkboxes = []
    for i in range(group_layout.count()):
        layout_item = group_layout.itemAt(i)
        if layout_item is not None and isinstance(layout_item.layout(), QHBoxLayout):
            sub_layout = layout_item.layout()
            for j in range(sub_layout.count()):
                item = sub_layout.itemAt(j)
                if item is not None and isinstance(item.widget(), QCheckBox):
                    QCheckBox(checkboxes.append(item.widget()))
    return checkboxes


def _check_all_checkboxes(checkboxes: list[QCheckBox]) -> None:
    """Set all checkboxes to checked state."""
    for checkbox in checkboxes:
        checkbox.setChecked(True)
    logging.info(f"Checked all {len(checkboxes)} checkboxes.")


def _uncheck_all_checkboxes(checkboxes: list[QCheckBox]) -> None:
    """Set all checkboxes to unchecked state."""
    for checkbox in checkboxes:
        checkbox.setChecked(False)
    logging.info(f"Unchecked all {len(checkboxes)} checkboxes.")


def _list_ticked_checkboxes(layout: QVBoxLayout) -> list[str]:
    """Returns a list of text from checked QCheckBox widgets in a QVBoxLayout."""
    ticked_boxes = [box.text() for box in _get_all_checkboxes_in_group(layout) if box.isChecked()]
    return ticked_boxes


def _check_if_match(root_folder: str, episode_names: dict[str]) -> bool:
    """Checks if the file structure of episodes matches the expected structure and provides warnings
    if discrepancies are found."""
    warnings = []

    for season, episodes in episode_names.items():
        season_folder = root_folder + '/' + season
        season_folder_fr = root_folder + '/' + season.replace("Season", "Saison")

        if not os.path.exists(season_folder) and not os.path.exists(season_folder_fr):
            warnings.append(f"Warning: Missing " + season + ".")
            continue

        if os.path.exists(season_folder_fr):
            season_folder = season_folder_fr

        files_in_season = [f for f in os.listdir(season_folder) if os.path.isfile(season_folder + '/' + f)]

        if len(files_in_season) != len(episodes):
            warnings.append(
                f"Warning: Number of files in '{season}' folder does not match the number of episodes in the overview.")

    if warnings:
        logging.warning("Discrepancies found in file structures.")
        if len(warnings) == 1:
            warning_message = warnings[0]
        else:
            warning_message = "Warnings:\n- " + "\n- ".join(warnings)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Warning")
        msg_box.setText(warning_message)
        msg_box.exec()
        return True
    logging.info("File structure matches the expected structure.")
    return False


def _check_and_rename_files(root_folder: str, episode_names: dict[str]) -> None:
    """Renames the files in the specified folder according to the given episode names mapping."""
    if _check_if_match(root_folder, episode_names):
        return

    for season, episodes in episode_names.items():
        season_folder = root_folder + '/' + season
        season_folder_fr = root_folder + '/' + season.replace("Season", "Saison")

        if os.path.exists(season_folder_fr):
            season_folder = season_folder_fr

        files_in_season = [f for f in os.listdir(season_folder) if os.path.isfile(os.path.join(season_folder, f))]

        for i, episode in enumerate(episodes):
            old_file_path = season_folder + '/' + files_in_season[i]
            new_file_path = season_folder + '/' + episode + ".mkv"

            try:
                os.rename(old_file_path, new_file_path)
                logging.info(f"Renamed: {old_file_path} to {new_file_path}")
            except FileNotFoundError:
                logging.error(f"File not found: {old_file_path}")
            except FileExistsError:
                logging.error(f"File already exists: {new_file_path}")
            except Exception as e:
                logging.error(f"An error occurred while renaming: {e}")


def _get_tree_structure_as_dict(model: QStandardItemModel) -> dict[str, list[str]]:
    """Returns the structure of a QStandardItemModel as a dictionary."""
    tree_dict = {}

    for row in range(model.rowCount()):
        parent_item = model.item(row)
        parent_text = parent_item.text()

        child_texts = []
        for child_row in range(parent_item.rowCount()):
            child_item = parent_item.child(child_row)
            child_texts.append(child_item.text())

        tree_dict[parent_text] = child_texts

    logging.info(f"Processed {len(tree_dict)} parent items in the model.")
    return tree_dict


class SeriesEditorUI(QWidget):
    """A custom QWidget for editing series data."""

    def __init__(self, data: dict, main_interface) -> None:
        super().__init__()

        self.TITLE_FONT = QFont(QFont().defaultFamily(), 20, QFont.Weight.Bold)
        self.main_interface = main_interface

        # Initialize the primary components of the editor window
        self.name = next(iter(data))
        self.url = data[self.name]
        self.file_watcher = None
        self.folder_path = None
        self.episode_names = WebQuery.get_episode_names(self.url)
        self.filtered_list = self.episode_names
        self.nb_seasons = len(self.episode_names)

        # GUI components
        self.main_layout = None

        # Title and seasons Checkbox components
        self.title_label = None
        self.season_info_layout = None
        self.seasons_label = None
        self.check_all_button = None
        self.uncheck_all_button = None
        self.checkbox_container = None
        self.checkbox_layout = None
        self.checkbox_buttons_layout = None
        self.season_checkbox = None
        self.checkbox_sub_layout = None

        # TreeViews area components
        self.trees_layout = None
        self.selected_seasons_layout = None
        self.selected_seasons_label = None
        self.selected_seasons_model = None
        self.selected_seasons_tree = None
        self.folder_content_layout = None
        self.load_folder_button = None
        self.folder_content_model = None
        self.folder_content_tree = None

        # Bottom buttons components
        self.bottom_buttons_layout = None
        self.back_button = None
        self.rename_button = None

        self.setup_ui()
        logging.info(f"Initialized SeriesEditorUI for series: {self.name} with URL: {self.url}")
        logging.info(f"Retrieved {len(self.episode_names)} seasons for series: {self.name}")

    def setup_ui(self) -> None:
        """Sets up the main UI components."""
        self.main_layout = QVBoxLayout()

        self.setup_title()
        self.setup_seasons_and_checkboxes()
        self.setup_tree_views()
        self.setup_bottom_buttons()

        self.setLayout(self.main_layout)
        logging.info("UI setup completed for SeriesEditorUI.")

    def setup_title(self) -> None:
        """Initializes and configures the title label for the widget."""
        self.title_label = QLabel(self.name)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(self.TITLE_FONT)
        self.title_label.setStyleSheet("color: red")
        self.main_layout.addWidget(self.title_label)

    def setup_seasons_and_checkboxes(self) -> None:
        """Sets up the label displaying the number of seasons and initializes checkboxes for each season."""
        self.season_info_layout = QHBoxLayout()
        self.seasons_label = QLabel('Number of seasons available: {}'.format(self.nb_seasons) +
                                    '   (<a href="' + self.url + '">Epguides.com</a>)')
        self.seasons_label.setOpenExternalLinks(True)
        self.checkbox_container = QGroupBox()
        self.checkbox_layout = QVBoxLayout()
        self.checkbox_buttons_layout = QHBoxLayout()

        self.check_all_button = QPushButton(CHECK_ALL_BUTTON_TEXT)
        self.check_all_button.clicked.connect(
            lambda: _check_all_checkboxes(_get_all_checkboxes_in_group(self.checkbox_layout)))
        self.uncheck_all_button = QPushButton(UNCHECK_ALL_BUTTON_TEXT)
        self.uncheck_all_button.clicked.connect(
            lambda: _uncheck_all_checkboxes(_get_all_checkboxes_in_group(self.checkbox_layout)))
        self.checkbox_buttons_layout.addWidget(self.check_all_button)
        self.checkbox_buttons_layout.addWidget(self.uncheck_all_button)
        self.checkbox_layout.addLayout(self.checkbox_buttons_layout)

        self.checkbox_sub_layout = QHBoxLayout()
        for i in range(self.nb_seasons):
            self.season_checkbox = QCheckBox(f"Season {i + 1}")
            self.season_checkbox.setChecked(True)
            self.season_checkbox.stateChanged.connect(self.checkbox_state_changed)
            self.checkbox_sub_layout.addWidget(self.season_checkbox)
            self.checkbox_sub_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if (i + 1) % MAX_CHECKBOX_PER_ROW == 0:  # Every 5 checkboxes, create a new horizontal layout
                self.checkbox_layout.addLayout(self.checkbox_sub_layout)
                self.checkbox_sub_layout = QHBoxLayout()
                self.checkbox_sub_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.checkbox_layout.addLayout(self.checkbox_sub_layout)
        self.checkbox_container.setLayout(self.checkbox_layout)
        self.season_info_layout.addWidget(self.seasons_label)
        self.season_info_layout.addWidget(self.checkbox_container)
        self.main_layout.addLayout(self.season_info_layout)
        logging.info(f"Setup {self.nb_seasons} checkboxes for seasons.")

    def setup_tree_views(self) -> None:
        """Configures two tree views: one for selected seasons and another for folder contents."""
        self.trees_layout = QHBoxLayout()

        self.create_season_tree()
        self.create_folder_content_tree()

        self.trees_layout.addLayout(self.selected_seasons_layout)
        self.trees_layout.addLayout(self.folder_content_layout)
        self.main_layout.addLayout(self.trees_layout)

    def create_season_tree(self) -> None:
        """Initializes and configures the tree view for displaying the selected seasons."""
        self.selected_seasons_layout = QVBoxLayout()
        self.selected_seasons_label = QLabel(SELECTED_SEASONS_LABEL_TEXT)
        self.selected_seasons_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selected_seasons_label.setFixedHeight(BUTTON_FIXED_HEIGHT)
        self.selected_seasons_model = QStandardItemModel()
        self.selected_seasons_tree = QTreeView()
        self.selected_seasons_tree.setModel(self.selected_seasons_model)
        self.selected_seasons_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.selected_seasons_tree.keyPressEvent = self.handle_key_press_event
        self.set_tree_episodes(_list_ticked_checkboxes(self.checkbox_layout))
        self.selected_seasons_layout.addWidget(self.selected_seasons_label)
        self.selected_seasons_layout.addWidget(self.selected_seasons_tree)

    def create_folder_content_tree(self) -> None:
        """Initializes and configures the tree view for displaying contents of a folder."""
        self.folder_content_layout = QVBoxLayout()
        self.load_folder_button = QPushButton(LOAD_FILES_BUTTON_TEXT)
        self.load_folder_button.setFixedHeight(BUTTON_FIXED_HEIGHT)
        self.load_folder_button.clicked.connect(self.open_folder_dialog)
        self.load_folder_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.folder_content_tree = QTreeView()
        self.folder_content_tree.setModel(None)
        self.folder_content_model = QFileSystemModel()
        self.folder_content_model.setRootPath('')
        self.folder_content_layout.addWidget(self.load_folder_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.folder_content_layout.addWidget(self.folder_content_tree)

    def setup_bottom_buttons(self) -> None:
        """Sets up the bottom buttons (Back and Rename) for the widget."""
        self.bottom_buttons_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.load_main_interface)
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(
            lambda: _check_and_rename_files(self.folder_path, _get_tree_structure_as_dict(self.selected_seasons_model)))
        self.bottom_buttons_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.bottom_buttons_layout.addWidget(self.rename_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.bottom_buttons_layout)

    def checkbox_state_changed(self) -> None:
        """Updates the season tree view based on the checked seasons."""
        self.set_tree_episodes(_list_ticked_checkboxes(self.checkbox_layout))
        self.filtered_list = {key: values for key, values in self.episode_names.items() if
                              key in _list_ticked_checkboxes(self.checkbox_layout)}

    def set_tree_episodes(self, ticked_seasons: list) -> None:
        """Populates the season tree view with episodes from ticked seasons."""
        self.selected_seasons_model.clear()
        for season, episodes in self.episode_names.items():
            if season in ticked_seasons:
                season_item = QStandardItem(season)
                season_item.setIcon(QIcon(FOLDER_ICON_PATH))
                for episode in episodes:
                    episode_item = QStandardItem(episode)
                    episode_item.setIcon(QIcon(VIDEO_ICON_PATH))
                    season_item.appendRow(episode_item)
                self.selected_seasons_model.appendRow(season_item)

    def handle_key_press_event(self, event: QKeyEvent) -> None:
        """Handles the key press events, particularly the 'Delete' key to remove selected items."""
        if event.key() == Qt.Key.Key_Delete:
            model = self.selected_seasons_tree.model()
            selection_model = self.selected_seasons_tree.selectionModel()
            selected_indexes = selection_model.selectedIndexes()

            if selected_indexes:
                rows_to_delete = set(index.row() for index in selected_indexes)
                items_to_delete = [model.itemFromIndex(index) for index in selected_indexes]

                for row, item in zip(rows_to_delete, items_to_delete):
                    if item.parent() is None:
                        continue  # Skip top-level items (folders)
                    self.recursive_remove_item(item)

    def recursive_remove_item(self, item: QStandardItem) -> None:
        """Recursively removes a given item and its children from the tree."""
        if item is not None:
            for row in range(item.rowCount()):
                child_item = item.child(row)
                self.recursive_remove_item(child_item)
            parent = item.parent()
            if parent is not None:
                parent.removeRow(item.row())

    def open_folder_dialog(self) -> None:
        """Opens a dialog for the user to select a folder and sets the folder's path to the tree view."""
        folder_dialog = QFileDialog()
        self.folder_path = folder_dialog.getExistingDirectory(self, 'Open Folder')

        if self.folder_path:
            root_index = self.folder_content_model.setRootPath(self.folder_path)
            self.folder_content_tree.setModel(self.folder_content_model)
            self.folder_content_tree.setRootIndex(root_index)
            logging.info(f"Selected folder: {self.folder_path} for SeriesEditorUI.")

    def load_main_interface(self) -> None:
        """Reloads the main interface of the application."""
        self.main_interface.reload_main_interface()
        logging.info("Main interface reloaded from SeriesEditorUI.")
