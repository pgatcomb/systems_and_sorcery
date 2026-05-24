# FFXIV Recipe Finder

A command-line application to help Final Fantasy XIV players determine what they can craft with the items in their inventory.

## Features

- **Crafting Recommendations**: Suggests recipes you can craft based on the items you have.
- **Inventory Management**: Add or remove items from a virtual inventory.
- **Persistent Inventory**: Save your current inventory to a CSV file and load it automatically on startup.
- **Fuzzy Matching**: Smartly matches item names, even with minor typos.

## Files

- `app.py`: The main Python script for the application.
- `recipes.json`: A JSON file containing the crafting recipe data.
- `requirements.txt`: A list of Python dependencies required to run the application.
- `user_inventory.csv`: (Optional) A file to store your inventory. It will be created when you save.

## Setup and Installation

1.  **Prerequisites**: Ensure you have Python 3.6+ installed on your system.

2.  **Install Dependencies**: Navigate to the project directory in your terminal and install the required libraries using pip.

    ```bash
    pip install -r requirements.txt
    ```

## How to Use

1.  **Run the Application**:

    ```bash
    python app.py
    ```

2.  **Using the Menu**:
    The application uses a simple command-line interface. Use the arrow keys to navigate and `Enter` to select an option.

    - **Add Inventory**: Add an item and its quantity to your virtual inventory.
    - **View Recommendations**: See a list of all the items you can currently craft.
    - **Remove Inventory**: Remove a specific quantity of an item from your inventory.
    - **Save Inventory**: Saves your current inventory to `user_inventory.csv` so it can be loaded the next time you start the app.
    - **Exit**: Closes the application.

3.  **(Optional) Pre-loading Inventory**:
    You can create a `user_inventory.csv` file in the same directory as `app.py` before running the script. The application will automatically load any items from this file on startup. The CSV file should have two columns: `item` and `quantity`.

    **Example `user_inventory.csv`:**
    ```csv
    item,quantity
    "bronze ingot",50
    "fire shard",999
    ```