# Easygrader, a library for easy grade computation

This library is meant to help compute grades obtained from different platforms, such as Gradescope, WebAssign, Brightspace, etc. In essence, it takes different gradebooks, merges them as a pandas DataFrame, computes the final grade according to a given grading scheme, and computes a letter grade.

## Technologies

Project created with:
- Python 3.10.4
- numpy 1.21.5
- pandas 1.4.2

## Requirements

To install the requirements for the project, run
```
pip install -r requirements.txt
```

## Example

See a detailed example in the example.py file. Details are below.

## Documentation

### Standard columns

The easygrader module gives access to several classes. More options than the ones discussed below are availale: please see the code for details.

Several classes can take an argument info_col. This is a dictionary that describes the headers used for the columns containing the first name, last name, ID, and email of the students. Default to
```
info_col = {'last': 'Last Name',
            'first' = 'First Name',
            'id', = 'ID',
            'email' = 'Email'}
```
If a gradebook only has one column for the full name, then the name is split (see Gradebook class).

For all gradeboks and for merging them, the ID column is used as a unique identifier for students. If no ID is given, it is inferred  to be the username of the email. If both are missing, an exception is raised.

### Gradebook class

A Gradebok is a DataFrame obtained from a .csv file, with a standard formatting. The file should have
- headers on the first row;
- either a full name column, or a first name + a last name column;
- an ID column and / or an email column.

For instance, a .csv file obtained from Gradescope is already formatted correctly, but a WebAssign file needs a bit of clean up.

The headers used in the files should be provided. n alternative if to provide a file_type 'GS' (for Gradescope headers) or 'WA' (WebAssign).

### Test class

A Test is describes a specific test, such as 'Quiz 1' or 'HW 2', with its max number of points. It can have several versions. For instance, if
```
- name = 'Quiz 5'
- nb_versions = 2
- max_points = 10
```
then the grades for this test should appear in the columns 'Quiz 5 - v1' and 'Quiz 5 - v2' of one of the Gradebooks, and each is graded out of 10. When creating a Course (see below), the grades of each version are then merged together into a single 'Quiz 5' column.

A Test should never be used by itself, and is "hidden" inside an Assignment.

### Assignment class

An Assignment describes a specific type of assignment, such as 'Quiz' or 'HW'. In essence, it consists of a sequence of tests. For instance, if
```
- name = 'Quiz'
- nb_versions = 3
- nb_tests = 6
```
then the corresponding Assignment will have an attibute `tests` that is a list of 6 Tests with name 'Quiz 1', ..., 'Quiz 6', and 3 versions each. 

Additionally, an Assignment should contain a GradingScheme that describes how the average of the Tests it contains is calculated.

### GradingScheme class

A GradingScheme is essentially a function applied to some rows of the DataFrame in order to compute an average. It can be applied to an assignment or to a Course.
- for an Assignment, it is applied to the Tests it contains;
- for a Course, it is applied to the average of each Assignment (where the average is calculated using the Assignment's GradingScheme).
An instance of a GradingScheme returns the unweighted average by default, but it can be used to drop the $k$ lowest grades, weighted averages, or use any user-defined function.

### Course class

A Course contains Gradebooks and Assignments. It has a `gradebook` attribute which contains a concatenation of all the Gradebooks.  It is important to note that the first Gradebook is used as a reference containing all the students. The other gradebooks will be appended to the first Gradebook, using their ID as index. If there are students in other Gradebooks that do not appear in the first Gradebook they will not be added. This is meant to avoid adding extra students who dropped out. Typically, the first Gradebook would be synchronized from the class list.

It also has a `grades` attribute that contains a summary of the grades of all the tests, with different versions of each test merged.

The roster can be recovered with the `roster` attribute.

The most useful feature of a Course is the `compute_grades` method, which can be called with

```
grades = course.compute_grades(grading_scheme, thresholds, letters, include, include_others)
```

This returns a DataFrame whose index is the ID of the students, and with their names and grades.
- `grading_scheme` is a GradingScheme that is applied to the average of each Assignment.
- `thresholds` are the thresholds for the letter grades, in decreasing order.
- `letters` are the letter grades, in decreaing order.
- `include` are the columns to include, out of 'tests' (grades of each test), 'averages' (averages of each assignment), 'final' (final grade calculated with the Course GradinScheme), 'letter' (letter grades), 'missed' (number of each assigmnet missed). Does not include 'tests' by default,
- `include_others` are the name of other columns to include, e.g. 'Comments'.

You can then import this file as a csv with
```
grades.to_csv(path_to_grades_file, index=False)
```

### create_import function

This function take a .csv file and creates a .csv file to import directly to the Brightspace gradebook. For instance, to obtain an import file that contains the letter grades directly, do
```
create_import(path_to_grades_file, path_to_import_file)
```