from collections import OrderedDict

import contextlib
import logging.config
import sqlite3
import datetime

from fastapi import FastAPI, Depends, Request, HTTPException, status
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class Class(BaseModel):
    class_code: str
    section_number: str
    class_name: str
    department: str
    auto_enrollment: bool
    max_enrollment: int
    max_waitlist: int
    c_instructor_username: str

class Settings(BaseSettings, env_file=".env", extra="ignore"):
    enrollment_database: str
    enrollment_logging_config: str

def get_db():
    with contextlib.closing(sqlite3.connect(settings.enrollment_database)) as db:
        db.row_factory = sqlite3.Row
        yield db

def get_logger():
    return logging.getLogger(__name__)

settings = Settings()
app = FastAPI()

logging.config.fileConfig(settings.enrollment_logging_config, disable_existing_loggers=False)

@app.get("/enrollment_test")
def enrollment_api_test(db: sqlite3.Connection = Depends(get_db)):
    return {"Test" : "success"}


# ---------------------- Additional -----------------------------

# Example: GET http://localhost:5000/all_classes
@app.get("/all_classes")
def get_available_classes(db: sqlite3.Connection = Depends(get_db)):
    classes = db.execute("""
                SELECT *
                FROM Class
            """)    
    return {"classes": classes.fetchall()}

# Example: GET http://localhost:5000/student_details/SamDoe123
@app.get("/student_details/{student_username}")
def get_student_details(student_username: str, db: sqlite3.Connection = Depends(get_db)):

    # Get student details
    student_details = db.execute("""
        SELECT *
        FROM Student
        WHERE student_username=?
    """, (student_username,)).fetchall()[0]

    return {"student": student_details}

# Example: GET http://localhost:5000/student_enrollment/SamDoe123
@app.get("/student_enrollment/{student_username}")
def get_student_enrollment(student_username: str, db: sqlite3.Connection = Depends(get_db)):

    # Get student details
    student_enrollment = db.execute("""
        SELECT *
        FROM Enroll
        WHERE e_student_username=?
    """, (student_username,)).fetchall()

    return {"enrollment": student_enrollment}

@app.get("/waitlist")
def get_waitlist(db: sqlite3.Connection = Depends(get_db)):

    # Check to see if student on waitlist
    waitlist = db.execute("""
                SELECT *
                FROM Waitlist
            """).fetchall()
    
    return {"waitlist": waitlist}


# ---------------------- Tasks -----------------------------

# Task 1: Student can list all available classes
# Example: GET http://localhost:5000/student/available_classes
@app.get("/student/available_classes")
def student_get_available_classes(db: sqlite3.Connection = Depends(get_db)):    
    classes = db.execute("""
                SELECT class_code, section_number, class_name, i_first_name, i_last_name
                FROM Class, Instructor
                WHERE (
                    SELECT Count(*)
                    FROM Enroll
                    WHERE class_code = e_class_code
                    AND section_number = e_section_number
                ) < max_enrollment
                AND c_instructor_username = instructor_username
            """)    
    return {"classes": classes.fetchall()}

# Task 2: Student can attempt to enroll in a class
# Example: POST http://localhost:5000/student/enroll_in_class/student/SamDoe123/class/CHEM101/section/01
@app.post("/student/enroll_in_class/student/{student_username}/class/{class_code}/section/{section_number}")
def student_enroll_self_in_class(student_username: str, class_code:str, section_number:str, db: sqlite3.Connection = Depends(get_db)):
    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()
    
    if not section_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section does not exist."
        )   
        
    # Check to see if student already enrolled
    student_is_enrolled = db.execute("""
        SELECT *
        FROM Enroll
        WHERE e_student_username=? 
        AND e_class_code=? 
        AND e_section_number=?
    """, (student_username, class_code, section_number)).fetchall()

    if student_is_enrolled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Student already enrolled"
        )
    
    # Check to see if student already on waitlist
    student_on_waitlist = db.execute("""
        SELECT *
        FROM Waitlist
        Where w_student_username=?
        AND w_class_code=?
        AND w_section_number=?
    """, (student_username, class_code, section_number)).fetchall()

    if student_on_waitlist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Student already on waitlist"
        )

    # Get number of students enrolled in the class
    num_enrollments = db.execute("""
        SELECT COUNT(*) as num_enrollments
        FROM Enroll
        WHERE e_class_code=?
        AND e_section_number=?
    """, (class_code, section_number)).fetchall()[0]

    # Get class max information
    class_details = db.execute("""
        SELECT max_enrollment, max_waitlist
        FROM Class
        WHERE class_code=?
        AND section_number=?
    """, (class_code, section_number)).fetchall()[0]
    
    # If the classes is not full then enroll the student into the class
    if num_enrollments["num_enrollments"] < class_details['max_enrollment']:
        # Enroll the student into the class
        db.execute("""
            INSERT INTO Enroll (e_student_username, e_class_code, e_section_number)
            VALUES (?, ?, ?)
        """, (student_username, class_code, section_number))

        # Remove them from the drop list if they previously dropped the class
        db.execute("""
            DELETE 
            FROM Dropped
            Where d_student_username=?
            AND d_class_code=?
            AND d_section_number=?
        """, (student_username, class_code, section_number))

        # Commit the changes
        db.commit()

        return {"detail": "Student successfully enrolled in class"}

    else:

        # Get number of students on waitlist for the class
        num_waitlist = db.execute("""
            SELECT COUNT(*) as num_waitlist
            FROM Waitlist
            WHERE w_class_code=?
            AND w_section_number=?
        """, (class_code, section_number)).fetchall()[0]

        # If the waitlist is also full
        if num_waitlist["num_waitlist"] >= class_details['max_waitlist']:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Class enrollment full and waitlist full"
            )


        # Enroll the student into the class
        db.execute("""
            INSERT INTO Enroll (e_student_username, e_class_code, e_section_number)
            VALUES (?, ?, ?)
        """, (student_username, class_code, section_number))

        # Get number of classes a student is waitlisted for
        num_student_waitlists = db.execute("""
            SELECT COUNT(*) as num_waitlist
            FROM Waitlist
            WHERE w_student_username=?
        """, (student_username,)).fetchall()[0]
    
        # Student reached the max number of classes they can be waitlisted for
        if num_student_waitlists['num_waitlist'] >= 3:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Class enrollment full and student has exceeded their max number of waitlisted classes"
            )   
        
        # Add student to the waitlist
        currentDateTime = datetime.datetime.now()
        db.execute("""
            INSERT INTO Waitlist (w_student_username, w_class_code, w_section_number, timestamp)
            VALUES (?, ?, ?, ?);
        """, (student_username, class_code, section_number, currentDateTime))

        # Remove them from the drop list if they previously dropped the class
        db.execute("""
            DELETE 
            FROM Dropped
            Where d_student_username=?
            AND d_class_code=?
            AND d_section_number=?
        """, (student_username, class_code, section_number))

        # Commit the changes
        db.commit()

        return {"detail": "Class enrollment full, Student added to waitlist"}

# Task 3: Student can drop a class
# Example: DELETE http://localhost:5000/student/drop_class/student/SamDoe123/class/MATH101/section/01
@app.delete("/student/drop_class/student/{student_username}/class/{class_code}/section/{section_number}")
def student_drop_self_from_class(student_username: str, class_code:str, section_number:str, db: sqlite3.Connection = Depends(get_db)):

    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()
    
    if not section_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section does not exist."
        )   

    # Check to see if student already enrolled
    student_is_enrolled = db.execute("""
        SELECT *
        FROM Enroll
        WHERE e_student_username=? 
        AND e_class_code=? 
        AND e_section_number=?
    """, (student_username, class_code, section_number)).fetchall()

    # If they are enrolled, unroll them
    if student_is_enrolled:
        db.execute("""
        DELETE 
        FROM Enroll 
        Where e_student_username=?
        AND e_class_code=?
        AND e_section_number=?
        """, (student_username, class_code, section_number))

        # Add them to drop list
        db.execute("""
        INSERT INTO Dropped (d_student_username, d_class_code, d_section_number)
        VALUES(?, ?, ?);
        """, (student_username, class_code, section_number))

        # Commit the changes
        db.commit()

        return {"detail": "Class successfully dropped."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled."
        )   

    
# Task 4: Instructor can view current enrollment for their classes
# Example: GET http://localhost:5000/instructor/enrollment/instructor/100
@app.get("/instructor/enrollment/instructor/{instructor_username}")
def instructor_get_enrollment_for_classes(instructor_username: str, db: sqlite3.Connection = Depends(get_db)):
    enrollment = db.execute("""
        SELECT student_username, s_first_name, s_last_name, class_code, section_number, class_name
        FROM Instructor, Class, Enroll, Student
        WHERE Instructor.instructor_username=?
        AND Instructor.instructor_username=Class.c_instructor_username
        AND  Class.class_code=Enroll.e_class_code
        AND Class.section_number=Enroll.e_section_number
        AND Enroll.e_student_username=student_username
        """, (instructor_username,)).fetchall()
    
    return {"enrollment": enrollment}

# Task 5: Instructor can view students who have dropped the class
# Example: GET http://localhost:5000/instructor/dropped/instructor/100/class/CPSC449/section/01
@app.get("/instructor/dropped/instructor/{instructor_username}/class/{class_code}/section/{section_number}")
def instructor_get_students_that_dropped_class(instructor_username: str,  class_code:str, section_number:str, db: sqlite3.Connection = Depends(get_db)):
    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()
    
    if not section_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section does not exist."
        )   
    
    dropped = db.execute("""
        SELECT student_username, s_first_name, s_last_name, class_code, section_number
        FROM Instructor, Class, Dropped, Student
        WHERE Instructor.instructor_username=?
        AND Class.class_code=?
        AND Class.section_number=?
        AND Instructor.instructor_username=Class.c_instructor_username
        AND  Class.class_code=Dropped.d_class_code
        AND Class.section_number=Dropped.d_section_number
        AND Dropped.d_student_username=student_username
        """, (instructor_username, class_code, section_number)).fetchall()
    
    return {"dropped": dropped}

# Task 6: Instructor can drop students administratively (e.g. if they do not show up to class)
# Example: DELETE http://localhost:5000/instructor/drop_student/student/11111111/class/CPSC449/section/01
@app.delete("/instructor/drop_student/student/{student_username}/class/{class_code}/section/{section_number}")
def instructor_drop_student_from_class(student_username: str, class_code:str, section_number:str, db: sqlite3.Connection = Depends(get_db)):
    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()
    
    if not section_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section does not exist."
        )   

    # Check to see if student already enrolled
    student_is_enrolled = db.execute("""
        SELECT *
        FROM Enroll
        WHERE e_student_username=? 
        AND e_class_code=? 
        AND e_section_number=?
    """, (student_username, class_code, section_number)).fetchall()

    # If they are enrolled, unroll them
    if student_is_enrolled:
        db.execute("""
        DELETE 
        FROM Enroll 
        Where e_student_username=?
        AND e_class_code=?
        AND e_section_number=?
        """, (student_username, class_code, section_number))

        # Add them to drop list
        db.execute("""
        INSERT INTO Dropped (d_student_username, d_class_code, d_section_number)
        VALUES(?, ?, ?);
        """, (student_username, class_code, section_number))

        # Commit the changes
        db.commit()

        return {"detail": "Student successfully dropped."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled."
        )   
    
# Task 7: Registrar can add new classes and sections
# Example: POST http://localhost:5000/registrar/new_class
# body: {
#     "class_code": "CPSC449",
#     "section_number": "04",
#     "class_name": "Database Systems",
#     "department": "Computer Science",
#     "auto_enrollment": true,
#     "max_enrollment": 30,
#     "max_waitlist": 15,
#     "c_instructor_username": "100"
# }
@app.post("/registrar/new_class")
def registrar_create_new_class(new_class: Class, request: Request, db: sqlite3.Connection = Depends(get_db)):

    c = dict(new_class)
    
    class_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=:class_code
                AND section_number=:section_number
            """, c).fetchall()
    
    if class_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Class already exists."
        )   

    db.execute("""
        INSERT INTO Class (class_code, section_number, class_name, department, auto_enrollment, max_enrollment, max_waitlist, c_instructor_username)
        VALUES (:class_code, :section_number, :class_name, :department, :auto_enrollment, :max_enrollment, :max_waitlist, :c_instructor_username)
        """, c)
    
    # Commit the changes
    db.commit()
    
    return {"detail": "New class successfully added."}


# Task 8: Registrar can remove existing sections
# Example: DELETE http://localhost:5000/registrar/remove_class/code/CPSC449/section/04
@app.delete("/registrar/remove_class/code/{class_code}/section/{section_number}")
def registrar_remove_section(class_code: str, section_number: str, db: sqlite3.Connection = Depends(get_db)):
    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()
    
    if section_exists:
        # Delete section
        db.execute(""" 
        DELETE FROM Class 
        WHERE class_code=?
        AND section_number=?
        """, (class_code, section_number))

        # Unenroll every student who was in that section
        db.execute(""" 
        DELETE FROM Enroll 
        WHERE e_class_code=?
        AND e_section_number=?
        """, (class_code, section_number))

        # Remove every student who was in that section from the waitlist
        db.execute(""" 
        DELETE FROM Waitlist
        WHERE w_class_code=?
        AND w_section_number=?
        """, (class_code, section_number))

        # Remove every student who was in that section from the droplist
        db.execute(""" 
        DELETE FROM Dropped
        WHERE d_class_code=?
        AND d_section_number=?
        """, (class_code, section_number))

        db.commit()
        return {"detail": "Section successfully removed."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section does not exist."
        )   
    
# Task 9: Registrar can change instructor for a section
# Example: PATCH http://localhost:5000/registrar/change_instructor/class/CPSC449/section/01/new_instructor/101
@app.patch("/registrar/change_instructor/class/{class_code}/section/{section_number}/new_instructor/{instructor_username}")
def registrar_change_instructor_for_class(class_code: str, section_number: str, instructor_username: str, db: sqlite3.Connection = Depends(get_db)):

    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()
    
    if not section_exists:
        raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Section does not exist."
                )   
    
    # Check to see if instructor exists 
    instructor_exists = db.execute("""
                SELECT *
                FROM Instructor
                WHERE instructor_username=?
            """, (instructor_username,)).fetchall()
    
    if not instructor_exists:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Instructor does not exist."
                )   

    # Change instructor for section
    db.execute("""
            UPDATE Class
            SET c_instructor_username=?
            WHERE class_code=?
            AND section_number=?
        """, (instructor_username, class_code, section_number))

    db.commit()
    return {"detail": "Instructor successfully changed"}
        

# Task 10: Freeze automatic enrollment from waiting lists (e.g. during the second week of classes)
# Example: PATCH http://localhost:5000/registrar/freeze_enrollment/class/CPSC449/section/01
@app.patch("/registrar/freeze_enrollment/class/{class_code}/section/{section_number}")
def registrar_freeze_enrollment_for_class(class_code: str, section_number: str, db: sqlite3.Connection = Depends(get_db)):

    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()

    if section_exists:
        # Change class auto_enrollment to false
        db.execute("""
                UPDATE Class
                SET auto_enrollment = FALSE
                Where class_code=?
                AND section_number=?
            """, (class_code, section_number))
    
        db.commit()
        return {"detail": "auto enrollment successfully frozen."}
    
    else:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Section does not exist."
                )   
    
    
# Task 11: Student can view their current position on the waiting list
# Example: GET http://localhost:5000/student/waitlist_position/student/ScottDavis123/class/ENGL205/section/01
@app.get("/student/waitlist_position/student/{student_username}/class/{class_code}/section/{section_number}")
def student_get_waitlist_position_for_class(student_username: str, class_code: str, section_number: str, db: sqlite3.Connection = Depends(get_db)):

    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()
    
    if not section_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Section does not exist."
        )   

    # Check to see if student on waitlist
    student_on_waitlist = db.execute("""
                SELECT *
                FROM Waitlist
                WHERE w_student_username=?
                AND w_class_code=?
                AND w_section_number=?
            """, (student_username, class_code, section_number)).fetchall()
    
    
    if student_on_waitlist:
        # For all students on the wait list for the specified class, get their id and the time they joined the waitlist
        class_waitlist = db.execute("""
                SELECT w_student_username, timestamp
                FROM Waitlist
                WHERE w_class_code=?
                AND w_section_number=?
            """, (class_code, section_number)).fetchall()
        
        # Transform data so we can check the students position on the waitlist
        waitlist = {}
        for wait_list_item in class_waitlist:
            waitlist_student_username = wait_list_item["w_student_username"]
            waitlist_timestamp = wait_list_item["timestamp"]
            waitlist[waitlist_student_username] = waitlist_timestamp
        
        # Return position on waitlist
        return f'You are number {get_position_on_waitlist(waitlist, student_username)} on the waitlist'
    
    else:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Student not on waitlist."
                )   

def get_position_on_waitlist(dict, student_username):
    ordered_dict = OrderedDict({k: v for k, v in sorted(dict.items(), key=lambda item: item[1])})
    return list(ordered_dict.keys()).index(student_username) + 1

# Task 12: Student can remove themselves from a waiting list
# Example: DELETE http://localhost:5000/student/remove_from_waitlist/student/11111111/class/ENGL205/section/01
@app.delete("/student/remove_from_waitlist/student/{student_username}/class/{class_code}/section/{section_number}")
def student_remove_self_from_class_waitlist(student_username: str, class_code: str, section_number: str, db: sqlite3.Connection = Depends(get_db)):

    # Check to see if student on waitlist
    student_on_waitlist = db.execute("""
                SELECT *
                FROM Waitlist
                WHERE w_student_username=?
                AND w_class_code=?
                AND w_section_number=?
            """, (student_username, class_code, section_number)).fetchall()

    if student_on_waitlist:
        # Remove student from waitlist
        db.execute("""
                DELETE FROM Waitlist
                WHERE w_student_username=?
                AND w_class_code=?
                AND w_section_number=?
            """, (student_username, class_code, section_number))
    
        db.commit()
        return {"detail": "Successfully removed from waitlist"}
    
    else:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Student not on waitlist."
                )   
    

# Task 13: Instructor can view the current waiting list for their course
# Example: GET http://localhost:5000/instructor/waitlist_for_class/instructor/102/class/CHEM101/section/02
@app.get("/instructor/waitlist_for_class/instructor/{instructor_username}/class/{class_code}/section/{section_number}")
def instructor_get_waitlist_for_class(instructor_username: str, class_code: str, section_number: str, db: sqlite3.Connection = Depends(get_db)):

    # Check to see if section exists 
    section_exists = db.execute("""
                SELECT *
                FROM Class
                WHERE class_code=?
                AND section_number=?
            """, (class_code, section_number)).fetchall()
    
    if not section_exists:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Section does not exist."
                )   
    
    # Check to see if section exists 
    instructor_exists = db.execute("""
                SELECT *
                FROM Instructor
                WHERE instructor_username=?
            """, (instructor_username,)).fetchall()
    
    if not instructor_exists:
        raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Instructor does not exist."
                )   

    # Get all students on the waitlist
    waitlist = db.execute("""
                SELECT student_username, s_first_name, s_last_name, class_code, section_number, timestamp
                FROM Instructor, Class, Waitlist, Student
                WHERE Instructor.instructor_username=?
                AND Class.class_code=?
                AND Class.section_number=?
                AND Instructor.instructor_username=Class.c_instructor_username
                AND  Class.class_code=Waitlist.w_class_code
                AND Class.section_number=Waitlist.w_section_number
                AND Waitlist.w_student_username=student_username
            """, (instructor_username, class_code, section_number)).fetchall()
    
    return {"waitlist": waitlist}
