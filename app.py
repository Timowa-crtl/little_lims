import os
import pandas as pd

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, jsonify, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import *  # apology, login_required, get_customer_id, get_next_sample_id
from datetime import datetime
# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///lab.db")

# lists of allowed options in tables
allowed_options_projects = {
    'workflow': ['shotgun', 'targeted'],
    'status': ['open', 'closed', 'cancelled']
}
allowed_options_samples = {
    'status': ['open', 'closed', 'cancelled']
}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    username = (db.execute(
        "SELECT username from users WHERE id = ?", user_id))[0]["username"]

    return render_template("index.html", username=username)


@app.route("/customers", methods=["GET", "POST"])
@login_required
def show_customers():
    # Query the database to get all customers
    customers = db.execute("SELECT * FROM customers")

    # Render the template with the list of customers
    return render_template("customers.html", customers=customers)


@app.route("/customers/create", methods=["GET", "POST"])
@login_required
def create_customer():
    if request.method == "POST":
        # Retrieve form data
        name = request.form.get("name")
        creation_date = datetime.now().strftime("%Y-%m-%d")

        # Validate form data
        if not name:
            return apology("Please provide a name for the customer", 400)

        # Insert new customer into the database
        db.execute("INSERT INTO customers (name, creation_date) VALUES (?, ?)", name, creation_date )

        # Redirect to the customers page or any other appropriate page
        return redirect("/customers")
    else:
        # Render the template with the form to create a new customer
        return render_template("create_customer.html")


@app.route("/projects")
@login_required
def show_projects():
    # Query the database to get project information with customer name and number of samples
    projects = db.execute("""
        SELECT
            projects.id AS project_id,
            customers.name AS customer_name,
            projects.workflow,
            COUNT(samples.id) AS nr_samples,
            projects.creation_date,
            projects.completion_date,
            projects.status
        FROM
            projects
        JOIN
            customers ON projects.customer_id = customers.id
        LEFT JOIN
            samples ON projects.id = samples.project_id
        GROUP BY
            projects.id
    """)

    # Render the template with the list of projects
    return render_template("projects.html", projects=projects)


@app.route("/projects/create", methods=["GET", "POST"])
@login_required
def create_project():
    if request.method == "POST":
        # Retrieve form data
        customer_name = request.form.get("customer_name")
        project_id = request.form.get("project_id")
        workflow = request.form.get("workflow")
        creation_date = datetime.now().strftime("%Y-%m-%d")

        # Validate form data
        if not customer_name or not project_id or not workflow:
            return apology("Please fill out all required fields", 400)

        # Get customer_id from table customers
        customer_id = get_customer_id(db, customer_name)

        # Check if customer_id is valid
        if not customer_id:
            return apology("Invalid customer name", 400)

        # Insert project into the database
        db.execute("INSERT INTO projects (id, customer_id, creator_id, workflow, status, creation_date) VALUES (?, ?, ?, ?, ?, ?)",
                   project_id, customer_id, session["user_id"], workflow, 'open', creation_date)

        # Redirect to projects page or any other appropriate page
        return redirect("/projects")
    else:
        # Retrieve customers for dropdown
        customers = db.execute("SELECT * FROM customers")

        # Render the create project form
        return render_template("create_project.html", customers=customers)


@app.route("/projects/edit/<project_id>", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    if request.method == "POST":
        # Retrieve form data
        workflow = request.form.get("workflow")
        customer_id = request.form.get("customer_id")
        status = request.form.get("status")

        # Validate form data
        if not workflow or not customer_id or not status:
            return apology("Please fill out all required fields", 400)

        db.execute("""
            UPDATE projects
            SET workflow = ?, customer_id = ?, status = ?
            WHERE id = ?
        """, workflow, customer_id, status, project_id)

        # Redirect to projects page or any other appropriate page
        return redirect("/projects")
    else:
        # Query the database to get project information
        projects = db.execute("""
            SELECT
                projects.id AS project_id,
                projects.workflow,
                projects.customer_id,
                projects.status
            FROM
                projects
            WHERE
                projects.id = ?
        """, project_id)

        if not projects:
            return apology("Project not found", 404)

        # Get the first project (since project_id is unique)
        project = projects[0]

        # Retrieve customers for dropdown
        customers = db.execute("SELECT id, name FROM customers")

        # Retrieve distinct options for workflow from the database
        workflow_options = allowed_options_projects['workflow']

        # Retrieve distinct options for status from the database
        status_options = allowed_options_projects['status']

        # Render the edit project form
        return render_template("edit_project.html", project_id=project_id, project=project, customers=customers, workflow_options=workflow_options, status_options=status_options)


@app.route("/projects/delete/<project_id>", methods=["GET", "POST"])
@login_required
def delete_project(project_id):
    if request.method == "POST":
        # First delete all samples within project
        db.execute("DELETE FROM samples WHERE project_id = ?", project_id)
        # Delete the project from the database
        db.execute("DELETE FROM projects WHERE id = ?", project_id)

        return redirect("/projects")
    else:
        return redirect("/projects")


@app.route("/projects/create/csv", methods=["GET", "POST"])
@login_required
def create_projects_from_csv():
    if request.method == "GET":
        # Render the form for uploading CSV file
        return render_template("create_project_from_csv.html")
    elif request.method == "POST":
        try:
            # Check if a file was included in the request
            if 'file' not in request.files:
                return apology("No file part", 400)

            file = request.files['file']

            # Check if the file is a CSV file
            if file.filename == '' or not file.filename.endswith('.csv'):
                return apology("No selected file or file is not a CSV", 400)

            # Read CSV file using pandas
            df = pd.read_csv(file)

            # Extract project data
            projects_data = df[['project_id', 'customer_name']].drop_duplicates()

            # Insert projects into the database
            for index, project in projects_data.iterrows():
                project_id = project['project_id']
                customer_name = project['customer_name']
                customer_id = get_customer_id(db, customer_name)
                if not customer_id:
                    return apology(f"Invalid customer name: {customer_name}", 400)

                creation_date = datetime.now().strftime("%Y-%m-%d")

                # Check if the project ID already exists
                existing_project = db.execute("SELECT * FROM projects WHERE id = ?", project_id)
                if existing_project:
                    # If the project ID already exists, continue to the next project
                    print(f"project_id '{project_id}' already exists.")
                else:
                    db.execute("INSERT INTO projects (id, customer_id, creator_id, workflow, status, creation_date) VALUES (?, ?, ?, ?, ?, ?)",
                            project_id, customer_id, session["user_id"], 'shotgun', 'open', creation_date)

            # Insert or update samples into the database
            for index, row in df.iterrows():
                project_id = row['project_id']
                sample_id = row['sample_id']
                # Skip rows with empty or NaN sample_id
                if pd.isna(sample_id) or sample_id == "":
                    continue
                sample_name = row['sample_name']
                customer_label = row['customer_label']

                # Check if the sample ID already exists for the project
                existing_sample = db.execute("SELECT * FROM samples WHERE id = ? AND project_id = ?", sample_id, project_id)

                if existing_sample:
                    # If the sample ID exists, update the sample record
                    db.execute("UPDATE samples SET sample_name = ?, customer_label = ? WHERE id = ? AND project_id = ?",
                            sample_name, customer_label, sample_id, project_id)
                else:
                    # If the sample ID doesn't exist, insert a new sample record
                    db.execute("INSERT INTO samples (id, project_id, status, sample_name, customer_label) VALUES (?, ?, ?, ?, ?)",
                            sample_id, project_id, 'open', sample_name, customer_label)

            # Redirect to projects page or any other appropriate page
            return redirect("/projects")

        except Exception as e:
            # Handle any errors that might occur during processing
            return apology(str(e), 500)


@app.route("/samples")
@login_required
def show_samples():
    # Query the database to get all samples with project and customer information
    samples = db.execute("""
        SELECT
            samples.id AS sample_id,
            samples.sample_name,
            samples.customer_label,
            projects.id AS project_id,
            projects.customer_id,
            projects.status AS project_status,
            customers.name AS customer_name,
            samples.status AS sample_status
        FROM
            samples
        JOIN
            projects ON samples.project_id = projects.id
        JOIN
            customers ON projects.customer_id = customers.id
    """)

    # Render the template with the list of samples
    return render_template("samples.html", samples=samples)


@app.route("/samples/create", methods=["GET", "POST"])
@login_required
def create_sample():
    if request.method == "POST":
        # Retrieve form data
        project_id = request.form.get("project_id")
        sample_name = request.form.get("sample_name")
        customer_label = request.form.get("customer_label")

        # Validate form data
        if not project_id:
            return apology("Please provide the Project ID", 400)

        # Check if the project_id exists in the projects table
        project = db.execute("SELECT * FROM projects WHERE id = ?", project_id)

        if not project:
            return apology("Project ID does not exist", 400)

        # Get the customer_id for this project
        customer_id = project[0]["customer_id"]

        # Generate sample_id
        sample_id = get_next_sample_id(db, project_id)

        # Insert sample into the database
        db.execute("INSERT INTO samples (id, project_id, status, sample_name, customer_label) VALUES (?, ?, ?, ?, ?)",
                   sample_id, project_id, 'open', sample_name, customer_label)

        # Redirect to samples page or any other appropriate page
        return redirect("/samples")
    else:
        # Render the create samples table form
        projects = db.execute("SELECT * FROM projects")
        return render_template("create_samples.html", projects=projects)


@app.route("/samples/createfromtable", methods=["GET", "POST"])
@login_required
def create_samples_from_table():
    if request.method == "POST":
        # Retrieve form data
        project_id = request.form.get("project_id")
        sample_table = request.form.get("sample_table")

        # Validate form data
        if not project_id or not sample_table:
            return apology("Please fill out all required fields", 400)

        # Split the table into rows, removing empty lines
        rows = [row.strip() for row in sample_table.split("\n") if row.strip()]

        # Check if the table is comma-separated or tab-separated
        is_comma_separated = all(',' in row for row in rows)
        is_tab_separated = all('\t' in row for row in rows)

        # If both or neither are true, throw an error
        if is_comma_separated == is_tab_separated:
            return apology("Please ensure the table is either comma-separated or tab-separated", 400)

        # Determine delimiter based on the check results
        delimiter = ',' if is_comma_separated else '\t'

        # Iterate over rows and insert samples into the database
        for row in rows:
            # Split row into sample_name and customer_label
            data = row.split(delimiter)
            sample_name = data[0].strip()
            customer_label = data[1].strip()

            # Insert sample into the database
            sample_id = get_next_sample_id(db, project_id)
            db.execute("INSERT INTO samples (id, project_id, status, sample_name, customer_label) VALUES (?, ?, ?, ?, ?)",
                       sample_id, project_id, 'open', sample_name, customer_label)

        # Redirect to samples page or any other appropriate page
        return redirect("/samples")
    else:
        # Render the create samples table form
        projects = db.execute("SELECT * FROM projects")
        return render_template("create_samples_from_table.html", projects=projects)


@app.route("/samples/edit/<sample_id>", methods=["GET", "POST"])
@login_required
def edit_sample(sample_id):
    if request.method == "POST":
        # Retrieve form data
        sample_name = request.form.get("sample_name")
        customer_label = request.form.get("customer_label")
        status = request.form.get("status")

        # Validate form data
        if not sample_name or not customer_label or not status:
            return apology("Please fill out all required fields", 400)

        # Update the sample in the database
        db.execute("""
            UPDATE samples
            SET sample_name = ?, customer_label = ?, status = ?
            WHERE id = ?
        """, sample_name, customer_label, status, sample_id)

        # Redirect to samples page or any other appropriate page
        return redirect("/samples")
    else:
        # Query the database to get sample information
        sample_list = db.execute("""
            SELECT
                samples.id AS sample_id,
                samples.sample_name,
                samples.customer_label,
                samples.project_id,
                samples.status
            FROM
                samples
            WHERE
                samples.id = ?
        """, sample_id)

        sample = sample_list[0]

        if not sample:
            return apology("Sample not found", 404)

        # Retrieve distinct options for status from the allowed options
        status_options = allowed_options_samples['status']

        # Render the edit sample form
        return render_template("edit_sample.html", sample_id=sample_id, sample=sample, status_options=status_options)


@app.route("/samples/delete/<sample_id>", methods=["GET", "POST"])
@login_required
def delete_sample(sample_id):
    if request.method == "POST":
        # Delete the sample from the database
        db.execute("DELETE FROM samples WHERE id = ?", sample_id)

        return redirect("/samples")
    else:
        return redirect("/samples")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        # Ensure password was submitted
        elif not confirmation:
            return apology("must provide password confirmation", 400)

        # check password confirmation
        if password != confirmation:
            return apology("invalid username and/or password", 400)

        # add username and password to database
        password_hash = generate_password_hash(password)

        # check if username is already taken
        exists = db.execute(
            "SELECT EXISTS(SELECT 1 FROM users WHERE username = ?) AS user_exists", username)[0]['user_exists']

        if exists != 0:
            return apology("username already taken!", 400)

        # register user in database table "users"
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)", username, password_hash)

        # log user in
        session["user_id"] = db.execute(
            "SELECT id FROM users WHERE username = ?", username)[0]["id"]

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


# Context processor to make username available in all templates
@app.context_processor
def inject_username():
    try:
        if 'user_id' in session:
            user_id = session['user_id']
            username = db.execute(
                "SELECT username FROM users WHERE id = ?", user_id)
            return dict(username=username)
        else:
            return dict(username=None)
    except:
        pass
