# LittleLIMS

## Description

LittleLIMS is a lightweight Laboratory Information Management System (LIMS) web application designed to manage projects and samples in a laboratory setting. It allows users to keep track of a database of customers, projects and samples.

### Features

- **User Authentication**: Users can register for an account, log in, and log out.
- **Customer Management**: Users can view a list of customers and create new customers.
- **Project Management**: Users can create, edit, and delete projects, specifying details such as workflow type, status, and associated customer.
- **Sample Management**: Users can create, edit, and delete samples within projects, providing sample names, customer labels, and statuses.
- **CSV Import**: Users can import project and sample data from CSV files for bulk data entry.

### Technologies Used

- **Flask**: Python-based web framework used for building the backend of the application. Building the backend with fastAPI was explored but ease of use and flexibility of Flask proved to be the best option for LittleLIMS.
- **SQLite**: Lightweight SQL database engine used for data storage.
- **HTML/CSS**: Frontend templates and stylesheets for rendering web pages.
- **JavaScript**: Used for client-side scripting, particularly for filtering tables, form validation, and confirmation dialogs.
- **CS50 Library**: Provided functionality for interacting with SQLite databases.
- **Pandas**: Python library used for data manipulation, particularly for reading and processing CSV files.

### Setup Instructions

1. Clone the repository to your local machine.
2. Install the required dependencies listed in the `requirements.txt` file.
3. Run the Flask application using the `python3 -m flask run` command.
4. Access the application through a web browser at `http://localhost:5000`.

### Usage

- **Register/Login**: Create a new account or log in with existing credentials.
- **Customers**: View a list of customers and create new customer entries.
- **Projects**: View, create, edit, or delete projects. Specify workflow type, status, and associated customer.
- **Samples**: View, create, edit, or delete samples within projects. Provide sample names, customer labels, and statuses.
- **CSV Import**: Import project and sample data from CSV files for bulk data entry.

## File Structure

- **flask_session/**: Directory containing session data.
- **templates/**: HTML templates for rendering web pages.
- **README.md**: This file, providing project documentation.
- **requirements.txt**: List of Python dependencies for the project.
- **lab.db**: SQLite database file storing 4 tables: users, customers, projects and samples.
- **csv_imports/**: Exemplary CSV files that can be imported into the system.
- **helpers.py**: Python module containing helper functions for the application.
- **static/**: Directory for static assets such as CSS files and favicon.
- **app.py**: Main Python file containing the Flask application and route definitions.
- **sql_code.txt**: Text file containing SQL code snippets used in the project.
