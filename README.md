# TVShowTagger

TVShowTagger is a PyQT6 based application designed to automate the renaming of video files, specifically TV shows. It leverages information fetched from "www.epguides.com" and provides a seamless interface for users to match their local TV show episodes with official naming conventions.

![App Screenshot](resources/interface.png)

## Features

- **TV Show Directory Matching:** Input a directory containing TV show seasons and view its structure.
- **Episodes List Viewer:** See a list of all existing episodes from a selected show. This data is fetched from "www.epguides.com".
- **Customizable Episode Listing:** Edit the list to view specific seasons or episodes.
- **Show Selection:** Users are presented with a comprehensive list of all available TV shows from "www.epguides.com". This list can be locally stored and refreshed for speedier access.
- **Local Cache and Storage:** Once show details are fetched, they're stored in a local database for faster retrieval in the future.

## Folder Structure Simulation

To make it easier for testing and understanding, a simulated folder structure has been provided under the [resources](https://github.com/ypasquazzo/TVShowTagger/tree/main/resources) directory. It gives a basic representation of how the application expects the folder hierarchy to be for optimal performance.

## Getting Started

1. **Select a TV Show:** Utilize the built list (needs to be constructed at least once and can be refreshed) to select a show.
2. **Verify TV Show Details:** Optionally, cross-check the selected show details to ensure it's the desired one.
3. **Load Local Folder:** Import a local directory with the actual TV show episodes.
4. **Match Episodes:** Sync episodes from the app's list with your local episodes. Edit or filter the list if required.
5. **Final Confirmation & Renaming:** Perform a final check to ensure both lists align perfectly, then let the application rename episodes to match official naming conventions.

## Dependencies

- PyQt6
- SQLite (for local storage)

## Project Structure

- **image:** Contains various icons used throughout the application.
- **interface:** Houses the user interface and part of the logic required to make the UI functional.
- **utilities:** Includes modules to manage database interactions and web queries.

