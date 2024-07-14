import csv
import pytz
import requests
import urllib
import uuid

from datetime import datetime
from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function



def get_customer_id(db, customer_name):
    # Query the database to get the customer_id for the given customer_name
    customer = db.execute("SELECT id FROM customers WHERE name = ?", customer_name)

    # Check if customer exists
    if customer:
        return customer[0]["id"]
    else:
        return None

def get_next_sample_id(db, project_id):
    """Count samples in project_id and get next sample_id"""
    # Query the database to count the number of samples in the project
    nr_of_samples_in_project = db.execute("SELECT COUNT(*) FROM samples WHERE project_id = ?", project_id)[0]["COUNT(*)"]

    # Calculate the next sample_id by adding 1 to the number of samples in the project
    sample_id = f"{project_id}_{nr_of_samples_in_project + 1}"

    return sample_id




def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
