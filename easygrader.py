#pylint: disable=no-member
"""
Definition of classes and import function.
"""

from heapq import nlargest
import pandas as pd
import numpy as np
from utils import format_file, test_score, letter_conversion, inverse_conversion


class GradingScheme:
    """
    Class describing a grading scheme. Can be applied to an assignment, or to a class.
    The scheme is applied row by row:
        _for an Assignment, it is applied to all Test
        _for a Course, it is applied to the average of each assignment
            (where the average is calculated with a GradingScheme)

    scheme can:
    _None (default) or 'mean': the average
    _'drop', with arg provided: drop the arg lowest
    _'weights', with arg a list: returns the weighted average
    _'weights', with arg a dictionary: returns the weighted average,
        with weight of column key being the value arg[key]
    _otherwise, scheme is returned. This can be used to defined a handmade function.
    """
    def __init__(self, scheme=None, arg=None):
        if scheme is None or scheme == 'mean':
            self.scheme = lambda x: x.mean()
        elif scheme == 'drop':
            def func(grades):
                nb_grades = len(grades) - arg
                return sum(nlargest(nb_grades, grades)) / nb_grades
            self.scheme = func
        elif scheme == 'weights':
            if isinstance(arg, dict):
                self.scheme = lambda x: sum([x[key]*value for
                        (key, value) in arg.items()])/sum(arg.values())
            else:
                self.scheme = lambda x: (x*arg).sum()/sum(arg)
        else:
            self.scheme = scheme

class Test:
    """
    Class describing a specific test, such as 'Quiz 1' or 'HW 2'.
    Attributes:
    _ name, e.g. 'HW 1'
    _ max_points, e.g. 20
    _ nb_versions: number of versions for this test.
    The version names are separated by version_separator.
    _ versions: the name of the different versions, given by name only when nb_versions is None,
    and name + version_separator + i, for i = 1, 2, ..., nb_versions.
    E.g.: 'Quiz 3 - v1', 'Quiz 3 - v2'.
    Note: if name = 'Quiz 5' and nb_versions = None, versions = ['Quiz 5'];
    if name = 'Quiz 5' and nb_versions = 1, versions = ['Quiz 5 - v1']
    """

    def __init__(self, name, max_points, nb_versions=None, version_separator=' - v'):
        self.name = name
        self.max_points = max_points

        if nb_versions is None:
            self.versions = [name]
            self.nb_versions = 1
        else:
            self.versions = [name + version_separator + str(i) for i in range(1, nb_versions + 1)]


class Assignment:
    """
    Class describing a specific (type of) assignment, such as 'Quiz' or 'HW'.
    Attributes:
    _ name, e.g. 'HW 1'
    _ max_points. If all tests of this type have the same maximum number of points,
    enter a int (or float).
    Otherwise, enter a list containing the maximum number of points of each assignment.
    This list should have length nb_tests.
    _ nb_versions: number of versions for each test.
    The version names are separated by version_separator.
    Same comment as for max_points.
    _ tests: the name of the different tests, separated by test_separator.
    If nb_tests = None, there is only one test with test.name = name.
    Otherwise, the name of the tests are
    name + test_separator + i, for i = 1, 2, ..., nb_tests. E.g.: 'Quiz 1', 'Quiz 2', 'Quiz 3'.
    _ scaling: the maximum number of points when displayed in the gradebook.
    Defaults to max_points if max_points is an int, otherwise to 100.
    _ grading_scheme: a GradingScheme used to compute the average of this assignment.
    Defaults to the mean.
    Can also enter a list of GradingScheme, then the max is returned.
    """

    def __init__(self, name, max_points, grading_scheme=None, scaling=None, nb_tests=None,
                 test_separator=' ', nb_versions=None, version_separator=' - v'):
        self.name = name

        # self.nb_tests is the actual number of tests
        if nb_tests is None:
            self.nb_tests = 1
        else:
            self.nb_tests = nb_tests

        # self.max_points is a list of the max points of each test
        if not isinstance(max_points, list):
            self.max_points = [max_points] * self.nb_tests
        else:
            self.max_points = max_points

        # Set the default grading scheme to be the mean
        if grading_scheme is None:
            self.grading_scheme = [GradingScheme()]
        elif isinstance(grading_scheme, GradingScheme):
            self.grading_scheme = [grading_scheme]
        else:
            self.grading_scheme = grading_scheme

        # Set the default scaling
        if scaling is None:
            if isinstance(max_points, (int, float)):
                self.scaling = max_points
            else:
                self.scaling = 100
        else:
            self.scaling = scaling

        # self.nb_versions is a list of the nb of versions of each test
        if not isinstance(nb_versions, list):
            self.nb_versions = [nb_versions] * self.nb_tests
        else:
            self.nb_versions = nb_versions

        # check that the lengths match
        if len(self.max_points) != self.nb_tests or len(self.nb_versions) != self.nb_tests:
            raise Exception('max_points and nb_versions should be a \
                                int / float or a list of nb_tests size')

        if nb_tests is None:
            # name is just the name
            self.tests = [Test(name, max_points=self.max_points[0],
                                nb_versions=nb_versions, version_separator=version_separator)]
        else:
            # name is name + the nb of tests (which could be 1)
            self.tests = [Test(name + test_separator + str(i + 1), max_points=self.max_points[i],
                               nb_versions=self.nb_versions[i], version_separator=version_separator)
                          for i in range(nb_tests)]


class Gradebook:
    """
    Class for gradebooks.
    A gradebook is merely a .csv file with a standard formatting.

    Attributes:
    _ df: a pandas dataframe created from file, formatted in a standard format
    with first columns representing the first name, last, ID, and email.
    The index of the df is given by the ID of the student, assumed to be a unique identifier.
    Missing values are replaced by np.nan.
    """

    def __init__(self, file, file_type=None, input_col=None, info_col=None,
                last_name_first=None, name_separator=None, missing_values=None):
        """
        _file: a .csv file formatted with:
            _ headers on the first row
            _ either a full name column, or a first name + a last name column
            _ an ID column or an email column. If no ID is given, it is inferred
            to be the username of the email. If both are missing, an exception is raised.
        _file_type: standard formatting for Gradescope ('GS') or WebAssign ('WA')
        _input_col: a dictionary with keys 'first' and 'last' (two columns for first and last name)
            or 'full' (one column for the full name),
            'id', and 'email'.
            The values are the name of the corresponding columns in the file.
        _info_col: same format as input_col. The values are the name of the
            columns in the DataFrame that is created. Defaults are 'Last Name',
            'First Name', 'ID', 'Email'
        _last_name_first: True if the file has a full name column and the first name
            appears first.
        _name_separator: if the file has a full name column, the character(s)
            used to separate the names (e.g. space ' ' or comma ', ')
        _missing_values: a list of the aliases for missing_values in the csv file
        """
        self.df = format_file(file, file_type, input_col, info_col,
                last_name_first, name_separator, missing_values)


class Course:
    """
    Sets up a course containing all grades.
    It is important to note that the first gradebook is used as a reference
    containing all the students. It could be a Gradebook pulled from
    Gradescope or Brightspace. WebAssign, on the other hand, does not
    remove students after they withdraw.
    The other gradebooks will be appended to the first Gradebook. If there are students in other
    gradebooks, they will not be added.

    Parameters:
    _assignments: a list of assignments in the class
    _assignments: a list of the assignments in the class
    _gradebooks: single Gradebook file, or list of Gradebook files

    Attributes:
    _assignments
    _roster: the class roster, containing last name, first name, ID, email.
    _gradebook: all gradebooks combined as described aboce
    _grades: all test grades for the tests of all the assignments given.
        This is a cleaned-up version of the gradebook, with different test versions combined,
        and extraneaous info like lateness removed.
    _info_col: a dictionary giving the name of the student info columns

    Methods:
    _grades: returns a Dataframe that includes a summary of the grades
    and more information such as number of assignment missed, averages,
    letter grades
    """

    def __init__(self, assignments, gradebooks, info_col=None):

        # Set up assignments as a list of Assignments
        if isinstance(assignments, Assignment):
            assignments = [assignments]
        self.assignments = assignments

        # Set up gradebook as a list of Gradebooks
        if isinstance(gradebooks, Gradebook):
            gradebooks = [gradebooks]

        # Set up standard info columns
        if info_col is None:
            info_col = {}
            info_col['last'] = 'Last Name'
            info_col['first'] = 'First Name'
            info_col['id'] = 'ID'
            info_col['email'] = 'Email'
        self.info_col = info_col

        # Create roster from the first gradebook
        self.roster = gradebooks[0].df[info_col.values()]

        # Create gradebook by concatenating the different gradebooks
        # First test for missing grades
        for i, gradebook in enumerate(gradebooks[1:]):
            difference = set(self.roster.index).difference(set(gradebook.df.index))
            if difference:
                print(f'The following students are missing grades in gradebook {i+1}:', difference)
        # Remove info columns from other gradebooks
        trimmed_gradebooks = [gradebook.df.loc[:, ~gradebook.df.columns.isin(self.roster.columns)] for gradebook in gradebooks]
        # Concatenate
        self.gradebook = pd.concat([self.roster] + trimmed_gradebooks, axis = 1).reindex(self.roster.index)

        # Create the grades DataFrame, containing only the grades of the
        # assignments given, and with the different versions combined

        self.grades = self.roster.copy()

        self.tests = [test for assignment in assignments for test in assignment.tests]

        for test in self.tests:
            self.grades[test.name] = self.gradebook.apply(lambda x, test=test: test_score(test.name, x[test.versions], x[info_col['id']]), axis=1)

    def compute_grades(self, grading_scheme=None, thresholds=None, letters=None,
        include=None, include_others=None):
        """
        Compute a DataFrame containing, optionally each of the following grades:
        _the individual grades of each test 'tests'
        _the average of each assignment type (e.g. Quiz, Homework) 'averages'
        _the final grade 'final', out of 100
        _the final letter grade 'letter'
        _the number of each assignment missed 'missed'
        _other columns: 'column_name', e.g. 'Comments'

        Parameters:
        _grading_scheme: a GradingScheme or list of GradingSchemes,
        to compute the grade form the average of each assignment.
        If a list is given, returns the max of the result obtained
        by each GradingScheme.
        _thresholds: a list in decreeasing order. These are the thresholds between
            each letter grade. A grade at the threshold is given the higher lettr grade.
            Defaults to [93, 90, 87, 83, 80, 75, 65, 50]
        _letters: the letters grades in decreasing opder. Defaults to
            ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'F']
        _include: the columns to include. If None, includes the average
        of each Assignmne,t the number of assignment missed, the
        final grade, and the letter grade.
        Otherwise, can be any sublist of ['tests', 'averages', 'final', 'letter', 'missed'],
        where 'tests' would include the result of each individual test.
        _include_others: name of other columns to include, e.g. 'Comments'.
        """

        # Standard grading_scheme
        if grading_scheme is None:
            grading_scheme = [GradingScheme()]
        elif isinstance(grading_scheme, GradingScheme):
            grading_scheme = [grading_scheme]

        # Standard thresholds
        if thresholds is None:
            thresholds = [93, 90, 87, 83, 80, 75, 65, 50]

        # Standard letter grades
        if letters is None:
            letters = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'F']

        #  Warn if thresholds not sorted in the decreasing order
        if any(thresholds[i] < thresholds[i + 1] for i in range(len(thresholds) - 1)):
            print('Thresholds not sorted')

        # Thresholds should separate letter grades, warn if lengths do not match
        if len(thresholds) != len(letters) - 1:
            print('Incorrect sizes of threshold and letters.\
                    There should be n letter grades and n-1 thresholds.')            

        # Default inclusion: averages, missed assignments, final grade, letter grade
        if include is None:
            include = ['averages', 'missed', 'final', 'letter']

        # Create the additional df

        include_options = ['tests', 'averages', 'final', 'letter', 'missed']
        dfs = {key: pd.DataFrame(index=self.roster.index) for key in include_options + ['others']}

        # Create a df containg the number of missed assignments.

        if 'missed' in include:
            for assignment in self.assignments:
                test_names = [test.name for test in assignment.tests]
                dfs['missed'][assignment.name + ' missed'] = self.grades[test_names].isna().sum(axis=1)

        # Then replace missing assignments by 0.

        grades = self.grades.copy()
        grades.replace(np.nan, 0, inplace=True)

        # Create a df containing the tests results

        if 'tests' in include:
            test_col = [test.name for test in self.tests]
            dfs['tests'] = self.grades[test_col]

        # Create a df containg the averages

        if 'averages' in include or 'final' in include or 'letter' in include:
            unscaled_averages = pd.DataFrame(index=self.roster.index)
            for assignment in self.assignments:
                test_names = [test.name for test in assignment.tests]
                dfs['averages'][assignment.name] = grades.apply(lambda x, test_names=test_names, assignment=assignment:
                                    max(gs.scheme(x[test_names]/assignment.max_points) for gs in assignment.grading_scheme)\
                                    *assignment.scaling, axis=1)
                unscaled_averages[assignment.name] = dfs['averages'][assignment.name]/assignment.scaling

        # Create a df containg the final grade

        if 'final' in include or 'letter' in include:
            dfs['final']['Final grade'] = unscaled_averages.apply(lambda x: max(gs.scheme(x) for gs in grading_scheme)*100, axis=1)

        # Create a df containg the letter grades

        if 'letter' in include:
            dfs['letter']['Letter grade'] = dfs['final'].apply(lambda x: letter_conversion(x['Final grade'], thresholds, letters), axis=1)

        # Create a df containing the rest of the columns
        if include_others is not None:
            other_col_to_include = [x for x in include_others if x not in include_options]
            dfs['others'] = self.gradebook[other_col_to_include]

        # Crete the df to return

        df = pd.concat([self.roster] + [df for df in dfs.values()], axis = 1).reindex(self.roster.index)

        return df


def create_import(input_path, output_path, info_col=None, letter_grade_col='Letter grade', standardize=True,
                     thresholds=None, letters=None, include_others=None):
    """
    Creates a .csv file to import directly to Brightspace.
    """

    # Standard info columns
    if info_col is None:
        info_col = {}
        info_col['last'] = 'Last Name'
        info_col['first'] = 'First Name'
        info_col['email'] = 'Email'
        info_col['id'] = 'ID'

    # Standard thresholds
        if thresholds is None:
            thresholds = [93, 90, 87, 83, 80, 75, 65, 50]

    # Standard letter grades
    if letters is None:
        letters = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'F']

    df = pd.read_csv(input_path)
    username = 'Username'
    final_grade_num = 'Adjusted Final Grade Numerator'
    final_grade_denom = 'Adjusted Final Grade Denominator'
    eol = 'End-Of-Line Indicator'
    pg_col = ' Points Grade'

    if include_others is None:
        include_others = []

    info_col_names = [info_col['last'], info_col['first'], info_col['email']]
    columns = [username] + info_col_names + [col + pg_col for col in include_others] + [final_grade_num, final_grade_denom, eol]

    output = pd.DataFrame(index=df.index, columns=columns)

    output[username] = df.apply(lambda x: '#' + x[info_col['id']], axis=1)
    output[info_col_names] = df.info_col_names
    for col in include_others:
        output[col + pg_col] = df.col
    if standardize:
        output[final_grade_num] = df.apply(lambda x: inverse_conversion(x[letter_grade_col], thresholds=thresholds, letters=letters), axis=1)
    else:
        output[final_grade_num] = df.letter_grade_col
    output[final_grade_denom] = 100
    output[eol] = '#'
    output.to_csv(output_path, index=False)
