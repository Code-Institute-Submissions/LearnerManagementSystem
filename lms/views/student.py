from sys import stderr
from flask import ( Blueprint, render_template, jsonify, request,  
    redirect, url_for, flash, session)

from database import mongo
from ..controllers.student_controller import (get_student_by_name,
       update_student_profile, get_student_by_id, get_subject_content)

mod = Blueprint("student", __name__)


@mod.route('/')
def student_index():
    student = get_student_by_id(session['user'])
    return render_template('student/index.html',student=student)


@mod.route('/update_profile', methods=['POST'])
def update_profile():
    student = get_student_by_id(session['user'])
    data = {'profile_about':request.form.get('profile_about'),
            'profile_img': request.files.get('profile_image')}
    message = update_student_profile(student.id,data)
    if message:
        flash(message)

    return redirect(url_for('student.student_index'))


@mod.route('/courses')
def student_courses():
    student = get_student_by_id(session['user'])
    return render_template('student/courses.html',
                           student=get_student_by_id(session['user']),
                           menu_items=student.subjects)


@mod.route('/_load_course_content', methods=['POST'])
def load_course_content():
    student = get_student_by_id(session['user'])
    subject = request.json['subject']
    course = request.json['course']
    content = student.subjects[subject][course];
    return content

@mod.route('/_load_subject_content', methods=['POST'])
def load_subject_content():
    avg = get_subject_content(session['user'],request.json['subject'])
    # avg = get_subject_content("2",'wrong')
    return avg
