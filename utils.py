from datetime import datetime
from sqlalchemy import func
from app import db
from models import CourseSession, Attendance, CourseEnrollment

def calculate_attendance(student_id, course_id):
    """
    Calculate attendance statistics for a student in a specific course.
    
    Args:
        student_id: ID of the student
        course_id: ID of the course
        
    Returns:
        Dictionary containing attendance stats
    """
    # Get all sessions for this course
    session_ids = db.session.query(CourseSession.id).filter_by(course_id=course_id).all()
    session_ids = [session[0] for session in session_ids]
    
    # If no sessions, return default stats
    if not session_ids:
        return {
            'total': 0,
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0,
            'percentage': 0
        }
    
    # Get all attendance records for this student in these sessions
    attendance_records = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.session_id.in_(session_ids)
    ).all()
    
    # Count by status
    present_count = sum(1 for record in attendance_records if record.status == 'present')
    absent_count = sum(1 for record in attendance_records if record.status == 'absent')
    late_count = sum(1 for record in attendance_records if record.status == 'late')
    excused_count = sum(1 for record in attendance_records if record.status == 'excused')
    
    # Calculate attendance percentage (present + late) / (total non-excused sessions)
    recorded_sessions = len(attendance_records)
    unattended_sessions = len(session_ids) - recorded_sessions
    
    # Add unattended sessions as 'absent'
    absent_count += unattended_sessions
    
    total_sessions = len(session_ids)
    total_required = total_sessions - excused_count
    
    if total_required > 0:
        percentage = (present_count + late_count) / total_required * 100
    else:
        percentage = 0
    
    return {
        'total': total_sessions,
        'present': present_count,
        'absent': absent_count,
        'late': late_count,
        'excused': excused_count,
        'percentage': round(percentage, 2)
    }

def get_attendance_stats(course_id):
    """
    Get overall attendance statistics for a course.
    
    Args:
        course_id: ID of the course
        
    Returns:
        Dictionary containing attendance stats
    """
    # Get all sessions for this course
    sessions = CourseSession.query.filter_by(course_id=course_id).all()
    if not sessions:
        return {
            'attendance_rate': 0,
            'sessions_count': 0,
            'student_count': 0,
            'below_threshold': 0
        }
    
    # Get all enrollments for this course
    enrollments = CourseEnrollment.query.filter_by(course_id=course_id).all()
    student_count = len(enrollments)
    
    # Calculate statistics
    total_present = 0
    total_late = 0
    total_records = 0
    below_threshold = 0
    
    for enrollment in enrollments:
        stats = calculate_attendance(enrollment.student_id, course_id)
        if stats['total'] > 0:
            below_threshold += 1 if stats['percentage'] < 75 else 0
    
    # Calculate overall attendance rate from Attendance records
    attendance_records = db.session.query(
        Attendance.status,
        func.count(Attendance.id).label('count')
    ).join(
        CourseSession, Attendance.session_id == CourseSession.id
    ).filter(
        CourseSession.course_id == course_id
    ).group_by(
        Attendance.status
    ).all()
    
    total_records = 0
    present_late_count = 0
    
    for status, count in attendance_records:
        total_records += count
        if status in ['present', 'late']:
            present_late_count += count
    
    attendance_rate = (present_late_count / total_records * 100) if total_records > 0 else 0
    
    return {
        'attendance_rate': round(attendance_rate, 2),
        'sessions_count': len(sessions),
        'student_count': student_count,
        'below_threshold': below_threshold
    }

def send_attendance_notification(student, course, attendance_percentage):
    """
    Send notification to student about low attendance.
    In a real application, this would send an email or other notification.
    For this implementation, we'll just print to the console.
    
    Args:
        student: Student object
        course: Course object
        attendance_percentage: Current attendance percentage
    """
    # This would be replaced with actual notification logic in a production system
    print(f"⚠️ NOTIFICATION: Student {student.full_name} ({student.student_id}) "
          f"has attendance of {attendance_percentage:.2f}% in {course.title}, "
          f"which is below the required minimum of {course.min_attendance_percent}%.")
    
    # In a real system, you could:
    # 1. Send an email
    # 2. Generate a notification in the UI
    # 3. Send an SMS
    # etc.
