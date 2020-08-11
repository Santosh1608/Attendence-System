from flask import Flask, render_template, request, flash, redirect, session
from passlib.hash import sha256_crypt
from database import connection
from functools import wraps

app = Flask(__name__)


def login_required(f):
    @wraps(f)
    def wrap():
        if 'email' in session:
            return f()
        else:
            flash("login as teacher first")
            return redirect('/loginT')

    return wrap


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/dashboard')
@login_required
def dash():
    return render_template('dashboard.html')


@app.route('/loginT', methods=['GET', 'POST'])
def loginT():
    try:
        if request.method == 'POST':
            c, conn = connection()
            x = c.execute("SELECT * FROM teachers WHERE email = '{}'".
                          format(request.form["email"].upper()))
            if x == 0:
                flash("Please register first")
                return redirect('/registerT')
            else:
                data = c.fetchone()
                if sha256_crypt.verify(request.form['password'], data['password']):
                    try:
                        c, conn = connection()
                        c.execute("SELECT * FROM teachers WHERE email = '{}'".format(request.form["email"]))
                        data = c.fetchone()
                        if data['secret_key'] != "super":
                            session["logged_In"] = True
                            session["email"] = request.form["email"]
                            session["name"] = data["name"].lower()
                            flash("Succesfully logged In")
                            return redirect('/dashboard')
                        else:
                            session["logged_In"] = True
                            session["email"] = request.form["email"]
                            session["name"] = data["name"].lower()
                            session["hod"] = True
                            flash("Succesfully logged In as admin ")
                            return redirect('/dashboard')
                    except:
                        flash("Try again")
                        return redirect('/loginT')
                else:
                    flash('Incorrect credentials')
                    return redirect("/loginT")
        else:
            return render_template('LoginT.html')
    except Exception as e:
        flash("Something went wrong try again", e)
        return render_template('loginT.html')


@app.route('/registerT', methods=['GET', 'POST'])
def registerT():
    try:
        if request.method == 'POST':
            if request.form["secret_key"] == "abcd":
                try:
                    c, conn = connection()
                    flag = c.execute("SELECT * FROM teachers WHERE email = '{}'".format(request.form["email"].upper()))
                    if flag > 0:
                        flash("Sorry entered email is already existed")
                        return redirect("/registerT")
                    else:
                        password = sha256_crypt.encrypt(request.form["password"])
                        c.execute(
                            """INSERT INTO teachers (name,password,email,subject,classname,secret_key) 
                            VALUES ('{}','{}','{}','{}','{}','{}')"""
                                .format(request.form["name"].upper(), password, request.form["email"].upper(),
                                        request.form["subject"].upper(), request.form["classname"].upper(),
                                        request.form["secret_key"]))
                        conn.commit()
                        session["logged_In"] = True
                        session["email"] = request.form["email"]
                        session["name"] = request.form["name"]
                        flash("U have successfully Registered")
                        return redirect('/dashboard')

                except Exception as e:
                    flash("Something wrong with database try again later", e)
                    return redirect("/registerT")
            elif request.form["secret_key"] == "super":
                try:
                    c, conn = connection()
                    flag = c.execute(
                        "SELECT * FROM teachers WHERE secret_key = '{}' or email = '{}'"
                            .format(request.form["secret_key"], request.form["email"].upper()))
                    if flag > 0:
                        flash("Super user account is already created")
                        return redirect("/registerT")
                    else:
                        password = sha256_crypt.encrypt(request.form["password"])
                        c.execute(
                            """INSERT INTO teachers (name,password,email,subject,classname,secret_key) 
                            VALUES ('{}','{}','{}','{}','{}','{}')"""
                                .format(request.form["name"].upper(), password, request.form["email"].upper(),
                                        request.form["subject"].upper(), request.form["classname"].upper(),
                                        request.form["secret_key"]))
                        conn.commit()
                        session["logged_In"] = True
                        session["email"] = request.form["email"]
                        session["hod"] = True
                        session["name"] = request.form["name"]
                        flash("U have successfully registered as admin")
                        return redirect('/dashboard')

                except Exception as e:
                    flash("Something wrong with database try again later", e)
                    return redirect("/registerT")

            else:
                flash("U have not rights to register as teacher")
                return redirect('/')
        else:
            return render_template('RegisterT.html')
    except Exception as e:
        flash("Somthing went wrong try agian", e)
        return render_template('registerT.html')


@app.route('/registerS', methods=['GET', 'POST'])
@login_required
def registerS():
    try:
        if request.method == 'POST':
            c, conn = connection()
            x = c.execute("SELECT * FROM student_data WHERE usn = '{}'".format(request.form["usn"]))
            if x > 0:
                flash("Username already exist")
                return redirect('/registerS')
            else:
                c.execute("INSERT INTO student_data (name,usn,classname) VALUES ('{}','{}','{}')".
                          format(request.form['name'], request.form['usn'], request.form['classname']))
                conn.commit()
                flash("Succesfully {} registered".format(request.form['name']))
                return redirect('/dashboard')
        else:
            return render_template('RegisterS.html')
    except Exception as e:

        flash("Somthing went wrong", e)
        return render_template('RegisterS.html')


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("logged out succesfully")
    return redirect('/')


@app.route("/show")
def show():
    try:
        c, conn = connection()
        c.execute("SELECT MIN(uid) AS uid,DATE_FORMAT(date, '%y-%m-%d') AS date FROM students GROUP BY date")
        dates = c.fetchall()
        return render_template('show_attendence.html', dates=dates)
    except:
        flash("something went wrong")
        return redirect('/')


@app.route("/show/<string:date>", methods=['GET', 'POST'])
def gotdate(date):
    if request.method == 'GET':
        return render_template("details.html", date=date)
    else:
        try:
            c, conn = connection()
            c.execute("SELECT * FROM students WHERE date = '{}' and classname = '{}' and subject = '{}'"
                      .format(date, request.form["classname"], request.form["subject"]))
            attendence = c.fetchall()
            return render_template("attendence.html", attendence=attendence, flag="show")
        except Exception as e:
            flash("Something went wrong")
            return redirect("/")


@app.route("/give", methods=['POST', 'GET'])
@login_required
def give():
    email = session['email']
    try:
        c, conn = connection()
        c.execute("SELECT * FROM teachers where email = '{}'".format(email))
        teacher = c.fetchone()
        classname = teacher["classname"]
        subject = teacher["subject"]
        teachername = teacher["name"]
        teacheremail = teacher["email"]
        c.execute("SELECT * FROM student_data WHERE classname = '{}'"
                  .format(classname))
        students_data = c.fetchall()
        if request.method == 'POST':
            x = c.execute("SELECT * FROM students WHERE date = curdate() and subject = '{}' and classname = '{}' "
                          .format(subject, classname))
            if x > 0:
                flash("U have already given attendence today")
                return redirect('/dashboard')
            else:
                for i, student in enumerate(students_data):
                    check = request.form[f"{i + 1}"]
                    usn = student["usn"]
                    name = student["name"]
                    classname = student["classname"]
                    if "present" in check:
                        c.execute(
                            "INSERT INTO students (usn,name,classname,present,subject,date,teacheremail,teachername) VALUES ('{}','{}','{}',{},'{}',curdate(),'{}','{}')"
                                .format(usn, name, classname, 1, subject, teacheremail, teachername))
                    else:
                        c.execute(
                            "INSERT INTO students (usn,name,classname,present,subject,date,teacheremail,teachername) VALUES ('{}','{}','{}',{},'{}',curdate(),'{}','{}')"
                                .format(usn, name, classname, 0, subject, teacheremail, teachername))
                conn.commit()
                flash("attendence submitted")
                return redirect('/dashboard')


        else:
            return render_template('give_attendence.html', students=students_data)

    except Exception as e:
        try:
            c, conn = connection()
            c.execute("SELECT * FROM teachers where email = '{}'".format(email))
            teacher = c.fetchone()
            classname = teacher["classname"]
            c.execute("SELECT * FROM student_data WHERE classname = '{}'"
                      .format(classname))
            students_data = c.fetchall()
            flash("Please give the attendence for everyone")
            return render_template('give_attendence.html', students=students_data)
        except:
            flash("something went wrong")
            return redirect('/dashboard')


@app.route('/edit')
@login_required
def edit():
    try:
        c, conn = connection()
        c.execute("SELECT MIN(uid) AS uid,DATE_FORMAT(date, '%y-%m-%d') AS date FROM students GROUP BY date")
        dates = c.fetchall()
        return render_template('edit_attendence.html', dates=dates)
    except:
        flash("something went wrong")
        return redirect('/')


@app.route('/edit/<string:date>')
def edit_attendence(date):
    try:
        email = session["email"]
        c, conn = connection()
        c.execute("SELECT * FROM students WHERE date = '{}' and teacheremail = '{}'".format(date, email))
        attendence = c.fetchall()
        return render_template('attendence.html', attendence=attendence, flag="edit", date=date)
    except:
        pass


@app.route('/edit/<string:date>', methods=['POST'])
def final_edit(date):
    try:
        email = session["email"]
        c, conn = connection()
        c.execute("SELECT * FROM students WHERE teacheremail = '{}' and date = '{}'".format(email, date))
        editdata = c.fetchall()
        for i, student in enumerate(editdata):
            check = request.form[f"{i + 1}"]
            usn = student['usn']
            if "present" in check:
                c.execute("UPDATE students SET present = {} WHERE usn = '{}'".format(1, usn))
            else:
                c.execute("UPDATE students SET present = {} WHERE usn = '{}'".format(0, usn))
        conn.commit()
        flash("Attendence updated successfully")
        return redirect("/")
    except:
        flash("Something went wrong pls try again")
        return redirect("/")


@app.route('/show_students')
def show_students():
    try:
        c, conn = connection()
        c.execute("SELECT * FROM student_data")
        students_list = c.fetchall()
        return render_template('remove_students.html', students=students_list)
    except:
        flash("Something went wrong try again later")
        return redirect('/dash')


@app.route('/show_teachers')
def show_teachers():
    try:
        c, conn = connection()
        c.execute("SELECT * FROM teachers where secret_key = '{}'".format("abcd"))
        teachers_list = c.fetchall()
        return render_template('remove_teachers.html', teachers=teachers_list)
    except:
        flash("Something went wrong try again later")
        return redirect('/dash')


@app.route('/remove_student/<string:usn>')
def remove_student(usn):
    try:
        c, conn = connection()
        x = c.execute("SELECT * FROM student_data WHERE usn = '{}'".format(usn))
        if x > 0:
            c.execute("DELETE FROM student_data where usn = '{}'".format(usn))
            conn.commit()
            flash('U have succesfully unregistered student')
            return redirect('/show_students')
        else:
            flash('student is not registered to delete')
            return redirect('/show_students')
    except:
        flash("Somthing went wrong")
        return redirect('/dash')


@app.route('/remove_teacher/<string:email>')
def remove_teacher(email):
    print("teacher")
    try:
        c, conn = connection()
        x = c.execute("SELECT * FROM teachers WHERE email = '{}'".format(email))
        if x > 0:
            c.execute("DELETE FROM teachers where email = '{}'".format(email))
            conn.commit()
            flash('U have succesfully unregistered teacher')
            return redirect('/show_teachers')
        else:
            flash('teacher is not registered to delete')
            return redirect('/show_teachers')
    except:
        flash("Something went wrong")
        return redirect('/dashboard')


if __name__ == "__main__":
    app.secret_key = "asfeiuwfbiwe132298423489"
    app.run(debug=True, port=8000)
