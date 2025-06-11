from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from app.interface.auth import login_required
from app.infrastructure.models import Submission, Assignment, Student, Teacher, db

submission_bp = Blueprint('submission', __name__)

# Entregar tarea (solo student inscrito)
@submission_bp.route('/', methods=['POST'])
@login_required('student')
def submit_assignment():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    data = request.get_json()
    submission = Submission(
        assignment_id=data['assignment_id'],
        student_id=student.id,
        file_url=data['file_url']
    )
    db.session.add(submission)
    db.session.commit()
    return jsonify(msg='Entrega registrada', id=submission.id), 201

# Listar entregas de una tarea (teacher dueño o student propio)
@submission_bp.route('/assignment/<int:assignment_id>', methods=['GET'])
@login_required('student')
def list_submissions(assignment_id):
    identity = session['user_id']
    assignment = Assignment.query.get_or_404(assignment_id)
    if identity['role'] == 'teacher':
        teacher = Teacher.query.filter_by(user_id=identity['id']).first()
        if not teacher or assignment.course.teacher_id != teacher.id:
            return jsonify(msg='No autorizado'), 403
        submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
    elif identity['role'] == 'student':
        student = Student.query.filter_by(user_id=identity['id']).first()
        submissions = Submission.query.filter_by(assignment_id=assignment_id, student_id=student.id).all()
    else:
        return jsonify(msg='No autorizado'), 403
    return jsonify([
        {'id': s.id, 'file_url': s.file_url, 'score': float(s.score) if s.score else None, 'feedback': s.feedback} for s in submissions
    ])

# Calificar entrega (solo teacher dueño)
@submission_bp.route('/<int:submission_id>/grade', methods=['PUT'])
@login_required('student')
def grade_submission(submission_id):
    identity = session['user_id']
    if identity['role'] != 'teacher':
        return jsonify(msg='Solo profesores pueden calificar'), 403
    submission = Submission.query.get_or_404(submission_id)
    assignment = Assignment.query.get(submission.assignment_id)
    teacher = Teacher.query.filter_by(user_id=identity['id']).first()
    if not teacher or assignment.course.teacher_id != teacher.id:
        return jsonify(msg='No autorizado'), 403
    data = request.get_json()
    submission.score = data['score']
    submission.feedback = data.get('feedback')
    db.session.commit()
    return jsonify(msg='Entrega calificada')
