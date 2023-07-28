import time
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_file
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
from helpers import usd, apology, check, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def homepage():
    return render_template("homepage.html")

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("username or password is invalid")

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to homepage
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    #When request via GET, display registration form
    if request.method == "GET":
        return render_template("register.html")

    #When form is submitted via POST, check for possible errors and insert the new user into users table
    if request.method == "POST":
        user_name = request.form.get("username")
        password1 = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")
        country_phone = request.form.get("country_phone")
        phone = request.form.get("phone")

    #raise exception if user is already in the db
    username_db = db.execute("SELECT username FROM users")
    for dict in username_db:
        for val in dict.values():
            if user_name == val:
                 return apology("user name has been used")

    if len(user_name) < 2:
        return apology("user name must be atleast 1 character")

    elif password1 != confirmation:
        return apology("password not match")

    elif len(password1) < 6:
        return apology("password must be atleast 6 characters!")

    elif len(email) < 2:
        return apology("please retype your email")

    elif check(email) == False:
        return apology("Email is invlaid")

    elif country_phone.isdigit() == False:
        return apology("the country code must be digit")

    elif phone.isdigit() == False:
        return apology("the phone must be digit")

    else:
        try:
            password = generate_password_hash(password1, method = "sha256")
            new_user = db.execute("INSERT INTO users (username, hash, email, country_code, phone) VALUES (?, ?, ?, ?, ?)", user_name, password, email, country_phone, phone)
            session["user_id"] = new_user
            #redirect to index
            return redirect("/")

        except:
            return apology("user already exist")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    if request.method == "GET":
        return render_template("post.html")

    else:
        title = request.form.get("title")
        location = request.form.get("location")
        commencement_date = request.form.get("commencement_date")
        completion_date = request.form.get("completion_date")
        deadline = request.form.get("deadline")
        quantity = request.form.get("quantity")
        unit = request.form.get("unit")
        remarks = request.form.get("remarks")

        commencement_date_a = time.strptime(str(commencement_date), "%Y-%m-%d")
        completion_date_a = time.strptime(str(completion_date), "%Y-%m-%d")
        today = time.strptime(str(date.today()), "%Y-%m-%d")
        deadline_a = time.strptime(str(deadline), "%Y-%m-%d")


        if commencement_date_a > completion_date_a :
            return apology("commencement date must be earlier than completion date!")

        if today > deadline_a:
             return apology("deadline must be later than today!")

        if deadline_a > commencement_date_a :
             return apology("deadline must be earlier than commencement date!")

        if deadline_a > completion_date_a :
             return apology("deadline must be earlier than completion date!")

        if "user_id" in session:
            user_id = session ["user_id"]

        db.execute("INSERT INTO project (user_id, title, location, commencement_date, completion_date, deadline, quantity, unit, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", user_id, title, location, commencement_date, completion_date, deadline, quantity, unit, remarks)
        flash("project post is successful", category = "success")
        return redirect("/post")

@app.route("/project", methods=["GET", "POST"])
@login_required
def project():
    if "user_id" in session:
        user_id = session ["user_id"]

    project_db = db.execute("SELECT project_id, title, location, commencement_date, completion_date, status FROM project WHERE project.user_id = ? AND status = 'pending'", user_id)
    project = []
    for row in project_db:
        project.append({
            "title" : row["title"],
            "location" : row["location"],
            "commencement_date" : row["commencement_date"],
            "completion_date" : row["completion_date"],
            "project_id" : row["project_id"],
            "status" : row["status"]})

    if request.method == "GET":
        return render_template("project.html", project = project)

@app.route("/delete-post/<id>")
@login_required
def delete_post(id):

    post = db.execute("SELECT * FROM project WHERE project_id = ?", id)

    if not post:
        apology("post does not exist")
    else:
        db.execute("DELETE FROM project WHERE project_id = ?", id)

    return redirect("/")


@app.route("/index")
@login_required
def index():
    a_project_db = db.execute("SELECT title, location, commencement_date, completion_date, project_id, timestamp, deadline, remarks FROM project WHERE status = 'pending'")
    index = []
    for row in a_project_db:
        index.append({
            "title" : row["title"],
            "location" : row["location"],
            "commencement_date" : row["commencement_date"],
            "completion_date" : row["completion_date"],
            "project_id" : row["project_id"],
            "timestamp": row["timestamp"],
            "deadline" : row["deadline"],
            "remarks" : row["remarks"],
            })

    if request.method == "GET":
        return render_template("index.html", index = index)


@app.route("/view-post/<project_id>", methods=["GET", "POST"])
@login_required
def view(project_id):
#quote_user, price, total, remarks
    view_db = db.execute("SELECT quote_id, project.project_id, price, MAX(timestamp_quote) AS timestamp_quote, remarks_quote, project.quantity AS quantity, project.unit AS unit, username AS quote_user FROM quote INNER JOIN project ON project.project_id INNER JOIN users ON users.user_id = quote.user_id WHERE quote.project_id = ? AND project.project_id = ? GROUP BY quote.user_id ORDER BY timestamp_quote DESC", project_id, project_id)
    view = []
    for row in view_db:
        view.append({
            "quote_user" : row["quote_user"],
            "timestamp_quote" : row["timestamp_quote"],
            "remarks_quote" : row["remarks_quote"],
            "price" : usd(row["price"]),
            "quote_id" : row["quote_id"],
            "quantity" : row["quantity"],
            "unit" : row["unit"],
            "total" : usd(float(row["quantity"]) * float(row["price"]))})

    if request.method == "GET":
        return render_template("view.html", view = view)

@app.route("/quote-post/<id>", methods=["GET","POST"])
@login_required
def quote(id):
    if "user_id" in session:
        user_id = session ["user_id"]

    post_quote_db = db.execute("SELECT title, quantity, unit, remarks, project_id FROM project WHERE project_id = ?", id)

    if not post:
        apology("post does not exist")

    post_quote = []
    for row in post_quote_db:
        post_quote.append({
            "title" : row["title"],
            "quantity" : row["quantity"],
            "unit" : row["unit"],
            "remarks" : row["remarks"],
            "project_id" : row["project_id"]
        })

    if request.method == "GET":
        return render_template("quote.html", post_quote = post_quote)
    try:
        if request.method == "POST":
            price = float(request.form.get("price"))
            remarks = request.form.get("remarks")

        if price <= 0:
            return apology("price must be greater than 0")

    except ValueError:
        return apology("price must be digit")

    else:
        db.execute("INSERT INTO quote (user_id, project_id, price, remarks_quote) VALUES (?, ?, ?, ?)", user_id, id, price, remarks)
        flash("quote is success!")
        return redirect("/index")

@app.route("/yourquote", methods=["GET", "POST"])
@login_required
def yourquote():
    if "user_id" in session:
        user_id = session ["user_id"]

    quote_db = db.execute("SELECT project.project_id, title, price, MAX(timestamp_quote) AS timestamp_quote, remarks_quote, status_quote, quantity, quote_id FROM quote INNER JOIN project ON project.project_id = quote.project_id WHERE quote.user_id = ? GROUP BY project.project_id ORDER BY timestamp_quote DESC", user_id)
    quote = []
    for row in quote_db:
        quote.append({
            "title" : row["title"],
            "timestamp_quote" : row["timestamp_quote"],
            "remarks_quote" : row["remarks_quote"],
            "price" : usd(row["price"]),
            "quantity" : row["quantity"],
            "quote_id" : row["quote_id"],
            "total" : usd(float(row["quantity"]) * float(row["price"])),
            "status_quote" : row["status_quote"]})

    if request.method == "GET":
        return render_template("yourquote.html", quote = quote)

@app.route("/delete-quote/<id>")
@login_required
def delete_quote(id):

    quote = db.execute("SELECT * FROM quote WHERE quote_id = ?", id)

    if not quote:
        apology("quote does not exist")
    else:
        db.execute("DELETE FROM quote WHERE quote_id = ?", id)

    return redirect("/")


@app.route("/confirm-post/<quote_id>")
@login_required
def confirm_post(quote_id):
    project_id_db = db.execute("SELECT project_id FROM quote WHERE quote_id = ?", quote_id)

    for dict in project_id_db:
        for val in dict.values():
            project_id = val

#update project table
    db.execute("UPDATE project SET status = 'awarded' WHERE project_id = ?", project_id)

#update user_id to the project table under awarded column
    award_id_db = db.execute("SELECT user_id FROM quote WHERE quote_id = ?", quote_id)
    for dict in award_id_db:
        for val in dict.values():
            award_id = val

    db.execute("UPDATE project SET awarded_userid = ? WHERE project_id =?", award_id, project_id)

#update quote table
    db.execute("UPDATE quote SET status_quote = 'success' WHERE (SELECT awarded_userid FROM project WHERE project_id = ?) = quote.user_id AND project_id = ?", project_id,  project_id)
    db.execute("UPDATE quote SET status_quote = 'fail' WHERE (SELECT awarded_userid FROM project WHERE project_id = ?) != quote.user_id AND project_id = ?", project_id,  project_id)
    flash("the project is awarded")

#return to home page when finished
    return redirect("/project")


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if "user_id" in session:
        user_id = session ["user_id"]

        history_db = db.execute("SELECT project_id, title, location, commencement_date, completion_date, status, awarded_userid, username FROM project INNER JOIN users on project.awarded_userid = users.user_id WHERE project.user_id = ? AND status = 'awarded'", user_id)

        history = []
        for row in history_db:
            history.append({
                "title" : row["title"],
                "location" : row["location"],
                "commencement_date" : row["commencement_date"],
                "completion_date" : row["completion_date"],
                "project_id" : row["project_id"],
                "status" : row["status"],
                "awarded_username" : row["username"],
                "awarded_userid" : row["awarded_userid"]})

        if request.method == "GET":
            return render_template("history.html", history = history)

@app.route("/user/<id>", methods=["GET", "POST"])
@login_required
def user(id):
    #select username, email country_code and phone number
    users_db = db.execute("SELECT username, email, country_code, phone FROM users WHERE user_id = ?", id)
    users= []
    for row in users_db:
        users.append({
            "username":row["username"],
            "email":row["email"],
            "country_code":row["country_code"],
            "phone":row["phone"]
        })
    if request.method == "GET":
            return render_template("user.html", users = users)


