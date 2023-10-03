import logging

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

WINDOW_ICON_PATH = '../image/epguides.png'
WINDOW_TITLE = "Show Info"
NO_PICTURE_PATH = '../image/no_picture_available.png'


class ShowDetailsWidget(QWidget):
    """A custom QWidget for showing series data."""

    def __init__(self, show_info: dict[str, str]) -> None:
        super().__init__()

        self.TITLE_FONT = QFont(QFont().defaultFamily(), 20, QFont.Weight.Bold)
        self.SUBTITLE_FONT = QFont(QFont().defaultFamily(), 14)

        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(WINDOW_ICON_PATH))
        self.setup_ui(show_info)

    def setup_ui(self, show_info: dict[str, str]) -> None:
        """Initialize and setup main UI elements."""
        main_layout: QVBoxLayout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        show_name: str = show_info.get("name", "")

        if show_name:
            main_layout.addWidget(self.create_title_label(show_name))
            main_layout.addWidget(self.create_poster_label(show_info))
            main_layout.addLayout(self.create_date_and_time_layout(show_info))
            main_layout.addLayout(self.create_synopsis_layout(show_info))
        else:
            logging.warning('No show name found while setting up the UI.')
            main_layout.addWidget(self.create_error_label())

        main_layout.addWidget(self.create_external_link_label(show_info))

        self.setLayout(main_layout)

    def create_title_label(self, show_name: str) -> QLabel:
        """Create and return the title label."""
        show_title_label: QLabel = QLabel(show_name)
        show_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        show_title_label.setFont(self.TITLE_FONT)
        show_title_label.setStyleSheet("color: red")
        show_title_label.setToolTip(f"Title: {show_name}")
        return show_title_label

    @staticmethod
    def create_poster_label(show_info: dict[str, str]) -> QLabel:
        """Create and return the poster label."""
        show_poster_label: QLabel = QLabel()
        show_poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        show_poster_label.setToolTip("Poster of the series")
        poster_data: str = show_info.get("poster")
        if not poster_data:
            show_poster_label.setPixmap(QPixmap(NO_PICTURE_PATH))
        else:
            poster_pixmap: QPixmap = QPixmap()
            if not poster_pixmap.loadFromData(QByteArray(poster_data)):
                logging.error('Failed to load the provided poster. Displaying default image.')

                show_poster_label.setPixmap(QPixmap(NO_PICTURE_PATH))
                show_poster_label.setToolTip("Failed to load the provided poster. Displaying default image.")
            else:
                poster_pixmap = poster_pixmap.scaled(600, 300, Qt.AspectRatioMode.KeepAspectRatio)
                show_poster_label.setPixmap(poster_pixmap)
        return show_poster_label

    @staticmethod
    def create_date_and_time_layout(show_info: dict[str, str]) -> QVBoxLayout:
        """Create and return layout containing release date and running time labels."""
        layout: QVBoxLayout = QVBoxLayout()
        release_date_label: QLabel = QLabel("Release date: " + show_info.get("date", "Unknown date"))
        release_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        release_date_label.setToolTip("Release date of the series")

        run_time_label: QLabel = QLabel("Run time: " + show_info.get("time", "Unknown time"))
        run_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        run_time_label.setToolTip("Running time of the series")

        layout.addWidget(release_date_label)
        layout.addWidget(run_time_label)
        return layout

    def create_synopsis_layout(self, show_info: dict[str, str]) -> QVBoxLayout:
        """Create and return layout containing synopsis title and body labels."""
        layout: QVBoxLayout = QVBoxLayout()
        synopsis_title_label: QLabel = QLabel("<b><i>Synopsis</i></b>")
        synopsis_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        synopsis_title_label.setFont(self.SUBTITLE_FONT)
        synopsis_title_label.setToolTip("Synopsis of the series")

        synopsis_body_label: QLabel = QLabel(show_info.get("synopsis", "Synopsis not available."))
        synopsis_body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        synopsis_body_label.setWordWrap(True)
        synopsis_body_label.setMaximumWidth(600)
        synopsis_body_label.setToolTip("Synopsis details")

        layout.addWidget(synopsis_title_label)
        layout.addWidget(synopsis_body_label)
        return layout

    def create_error_label(self) -> QLabel:
        """Create and return the error label."""
        logging.error('Could not retrieve info on this Show!')

        error_title_label: QLabel = QLabel("Could not retrieve info on this Show!")
        error_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_title_label.setFont(self.TITLE_FONT)
        error_title_label.setStyleSheet("color: red")
        return error_title_label

    @staticmethod
    def create_external_link_label(show_info: dict[str, str]) -> QLabel:
        """Create and return the external link label."""
        epguides_link_label: QLabel = QLabel(f'Visit <a href="{show_info.get("url", "#")}"'
                                             f'>Epguides</a> for more details.')
        epguides_link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        epguides_link_label.setOpenExternalLinks(True)
        epguides_link_label.setToolTip("External link to Epguides for more details")
        return epguides_link_label
