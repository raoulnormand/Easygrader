"""
This describes a typical use case of the easygrader module.
"""

# Import Path to deal with files
from pathlib import Path

# Import classes and functions
from easygrader import Gradebook, GradingScheme, Assignment, Course, create_import

# Folder that where out files are located
folder = Path('C:\\Users\\your_name\\course_name\\')

# Gradebook files.
# These should be .csv files with headers on the first row, and
# either a full name column, or a first name + a last name column
GS_file = folder / Path(r'GS.csv')
WA_file = folder / Path(r'WA.csv')
rec_file = folder / Path(r'Recitation.csv')
part_file = folder / Path(r'Participation.csv')

# File for the summary of the grades
grade_file = folder / Path(r'Grades2.csv')

# Create the gradebooks. The file_type describe the formatting,
# that is the name used for the info columns and for the missing values.
# More info in the Gradebook class.
GS_gradebook = Gradebook(file=GS_file, file_type='GS')
WA_gradebook = Gradebook(file=WA_file, file_type='WA')
rec_gradebook = Gradebook(file=rec_file, file_type='GS')
part_gradebook = Gradebook(file=part_file, file_type='GS')

# Define the grading schemes
# Average with two lowest grades dropped
drop2 = GradingScheme('drop', 2)
# Grading scheme for the class: weights are given for eahc assignment,
# in the order that they are given in the Course class below.
# Since a list is given, this means the grade is computed as the
# max of each GradingScheme in the list.
# This Grading scheme corresponds to
# 5% WebAssign, 15% quizzes, 15% homework, 5% participation, and then
# best of # 15 % per midterm + 30 % final OR 10 % lowest midterm, 15% highest midtern, 35% final.

course_scheme = [GradingScheme('weights', [5, 15, 15, 5, 15, 15, 30]),
		GradingScheme('weights', [5, 15, 15, 5, 10, 15, 35]),
		GradingScheme('weights', [5, 15, 15, 5, 15, 10, 35])]

# Define the Assignments
 # One column called 'WebAssign', rescaled to be out of 5 in the final gradebook.
wa = Assignment(name='WebAssign', max_points=100, scaling=5)
# 11 columns called HW 1, ..., HW 11, graded out of 20.
# Average calculated by dropping the two lowest grades.
hw = Assignment(name='HW', max_points=20, nb_tests=11, grading_scheme=drop2)
# Similar, but with columns Quiz 1 - v1, Quiz 1  - v2, Quiz 2 - v1, ...
# The two versions of each are collapsed into a single grade.
quiz = Assignment(name='Quiz', max_points=20, nb_tests=10, nb_versions=2, grading_scheme=drop2)
# Participation
part = Assignment(name='Participation', max_points=5)
# Instead of definition midterm with nb_tests = 2, we define two different assignments
# in order to make the "best of" grading scheme work.
midterm1 = Assignment(name='Midterm 1', max_points=100)
midterm2 = Assignment(name='Midterm 2', max_points=100)
final = Assignment(name='Final exam', max_points=100)

# Create the course
course = Course(assignments=[wa, quiz, hw, part, midterm1, midterm2, final],
		gradebooks=[GS_gradebook, WA_gradebook, rec_gradebook, part_gradebook])

# Compute the grades, and also add the 'Comments' column
# We sort by decreasubg final grade in order to readjust thresholds if necessary.
grades = course.compute_grades(grading_scheme=course_scheme, include_others=['Comments']).sort_values('Final grade', ascending = False)

# Export the file to csv
# Remove the index or there will be two ID columns.
grades.to_csv(grade_file, index=False)

# At this point, we can modify the grade_file directly if desired, e.g. readjust letter grades
# To this end, we add a column 'Adjusted letter grade'.
# We could also do nothing and import directly. In this case, no need to
# include letter_grade_col, whcih defaults to 'Letter grade', as in the grade_file
# We also include the final exam grade.
# The file obtained can be directly uploaded to the brightspace Gradebook.

import_file = folder / Path(r'Import.csv')
create_import(grade_file, import_file, letter_grade_col='Adjusted letter grade', include_others=['Final exam'])
