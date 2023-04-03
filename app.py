from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, RadioField, FileField
from wtforms.validators import DataRequired
import operator
from werkzeug.utils import secure_filename




app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'MySecretKey'
app.config['UPLOAD_FOLDER'] = 'static'
db = SQLAlchemy(app)


class Employees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    month_voted = db.Column(db.String(7), nullable=False)
    employee_pic = db.Column(db.String(), nullable=True)

class Nominees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year_month = db.Column(db.String(7))
    voted_by = db.Column(db.String)
    candidate_id = db.Column(db.String)


class AddForm(FlaskForm):
    name = StringField('New employee name: ', validators=[DataRequired()])
    image = FileField('Upload Image:')
    submit = SubmitField('Submit')


class DeleteForm(FlaskForm):

    name = SelectField("Remove employee", validators=[DataRequired()])
    submit = SubmitField('Delete')



class VotingForm(FlaskForm):
    name = SelectField("Select your name: ", validators=[DataRequired()])
    candidate = SelectField("Nominate: ", validators=[DataRequired()])
    submit = SubmitField('Submit')


years = [('',''), ('2023', '2023'), ('2024', '2024'), ('2025', '2025'),]
months = [('',''), ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')]
class Year_Month(FlaskForm):
    year = SelectField("Year: ")
    month = SelectField("Month: ")
    report_type = RadioField(choices=[('full', 'Full Report'), ('summary', 'Summary')], validators=[DataRequired()])
    submit = SubmitField('Results')

@app.route('/admin')
def admin_page():
    return redirect(url_for('add_employee'))

@app.route('/', methods=['GET','POST'])
def home():
    title = 'Home'
    lastmont_list = {}
    current_month = datetime.now().strftime('%m')
    current_year = datetime.now().strftime('%Y')
    if int(current_month) == 1:
        current_year = str(int(current_year) - 1)
        current_month = '12'
    else:
        current_month = str(int(current_month) - 1)
        if int(current_month) <= 9:
            current_month = '0' + current_month

    print(current_year)
    print(current_month)
    my_date = f'{current_year}-{current_month}'
    print(my_date)
    query = Nominees.query.filter_by(year_month=str(my_date))
    print(query)
    for q in query:
        lastmont_list[q.candidate_id] = 0
    for each in query:
        lastmont_list[each.candidate_id] = lastmont_list[each.candidate_id] + 1

    sorted_d = dict(sorted(lastmont_list.items(), key=operator.itemgetter(1), reverse=True))

    winner_name = list(sorted_d.keys())[0]

    employee_of_the_month = Employees.query.filter_by(name=winner_name).first()
    current_month = int(current_month)
    current_year = int(current_year)
    print(employee_of_the_month.employee_pic)
    return render_template('home.html', title=title, employee_of_the_month=employee_of_the_month, current_month=current_month, current_year=current_year, years=years, months=months)

@app.route('/nominate', methods=['GET','POST'])
def index():
    form = VotingForm()
    employee_list = [('', '')]
    all_employee = Employees.query.all()
    for emp_name in all_employee:
        name_tuple = (emp_name.name, emp_name.name)
        employee_list.append(name_tuple)
    form.candidate.choices = employee_list

    no_vote_list = [('', '')]
    all_employee = Employees.query.all()
    for emp_name in all_employee:
        if int(emp_name.month_voted[0:4]) == int(datetime.now().strftime('%Y')):
            if int(emp_name.month_voted[5:8]) < int(datetime.now().strftime('%m')):
                name_tuple = (emp_name.name, emp_name.name)
                no_vote_list.append(name_tuple)
        elif int(emp_name.month_voted[0:4]) < int(datetime.now().strftime('%Y')):
            name_tuple = (emp_name.name, emp_name.name)
            no_vote_list.append(name_tuple)
    form.name.choices = no_vote_list

    title = 'Employee of the Month Form'
    if form.validate_on_submit():
        voter = Employees.query.filter_by(name=form.name.data).first()
        nominated = Employees.query.filter_by(name=form.candidate.data).first()
        new_candidate = Nominees(year_month=str(datetime.now().strftime('%Y-%m')), voted_by=voter.name, candidate_id=nominated.name)
        voter.month_voted = str(datetime.now().strftime('%Y-%m'))
        db.session.add_all([new_candidate, voter])
        db.session.commit()
        return redirect(url_for('thankyou'))
    return render_template('index.html', title=title, form=form)
    # return "Tang Ina"

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

@app.route('/admin/add', methods=['GET','POST'])
def add_employee():
    title = 'Add Employee'
    form = AddForm()
    status = ''
    if form.validate_on_submit():
        existing_employee = Employees.query.filter_by(name=form.name.data).first()
        if existing_employee:
            status = 'Error: Employee name already exist'
        else:
            try:
                image_filename = form.image.data.filename
                file = form.image.data
                file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
            except:
                image_filename = 'default.jpg'
            new_employee = Employees(name=form.name.data, month_voted='2023-02', employee_pic=image_filename)
            db.session.add(new_employee)
            db.session.commit()
            status = form.name.data + ' is added to the database'
            form.name.data = ''
        return render_template('add_emp.html', title=title, form=form, status=status)

    return render_template('add_emp.html', title=title, form=form, status=status)

@app.route('/admin/delete', methods=['GET','POST'])
def delete_employee():
    title = 'Delete Employee'
    form = DeleteForm()
    employee_list = [(' ', ' ')]
    all_employee = Employees.query.all()
    for emp_name in all_employee:
        name_tuple = (emp_name.name, emp_name.name)
        employee_list.append(name_tuple)
    form.name.choices = employee_list
    if form.validate_on_submit():
        delete_employee = Employees.query.filter_by(name=form.name.data).first()
        db.session.delete(delete_employee)
        db.session.commit()
        return redirect(url_for('delete_employee'))

    return render_template('delete_emp.html', title=title, form=form)

@app.route('/admin/list')
def list_employee():
    title = 'List Employee'
    everyone = Employees.query.all()
    return render_template('list_emp.html', title=title, everyone=everyone)

@app.route('/admin/list_candidates', methods=['GET','POST'])
def list_candidates():
    title = 'List Candidates'
    form = Year_Month()
    form.year.choices = years
    form.month.choices = months
    sorted_d = {}
    if form.validate_on_submit():
        year = form.year.data
        month = form.month.data
        report = form.report_type.data
        my_list = {}
        query = Nominees.query.filter_by(year_month=year+'-'+month)
        for q in query:
            my_list[q.candidate_id] = 0
        for each in query:
            my_list[each.candidate_id] = my_list[each.candidate_id]+1
        sorted_d = dict( sorted(my_list.items(), key=operator.itemgetter(1), reverse=True))
        return render_template('list_candidates.html', title=title, everyone=sorted_d, form=form, query=query, report=report)

    return render_template('list_candidates.html', title=title, everyone=sorted_d, form=form)

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
