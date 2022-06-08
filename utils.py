"""
Utility files for the easygrader module.
"""

import pandas as pd
import numpy as np

def format_file(file, file_type=None, input_col=None, info_col=None,
                last_name_first=None, name_separator=None, missing_values=None):
    """
    Utility function to format a csv file as described in the Gradebook class.
    """

    if info_col is None:
        info_col = {}
        info_col['last'] = 'Last Name'
        info_col['first'] = 'First Name'
        info_col['id'] = 'ID'
        info_col['email'] = 'Email'

    if file_type == 'GS':
        input_col = {}
        input_col['full'] = 'Name'
        input_col['id'] = 'SID'
        input_col['email'] = 'Email'
        last_name_first = False
        name_separator = ' '
    elif file_type == 'WA':
        input_col = {}
        input_col['full'] = 'Fullname'
        input_col['email'] = 'Email'
        last_name_first = True
        name_separator = ', '
        missing_values = ['ND', 'NS']

    # Read the csv file as DataFrame
    file_as_df = pd.read_csv(file)

    # Create the new DataFrame and replace all the missing values by np.nan
    df = pd.DataFrame(index=file_as_df.index)
    df.fillna(np.nan, inplace=True)
    if missing_values is not None:
        df.replace(missing_values, np.nan, inplace=True)

    # Deal with names
    if 'first' in input_col.keys() and 'last' in input_col.keys():
        for key in ['last', 'first']:
            df[info_col[key]] = file_as_df[input_col[key]]
    elif 'full' in input_col.keys():
        names = file_as_df[input_col['full']].str.split(name_separator, expand=True)
        df[info_col['first']] = names[int(last_name_first)]
        df[info_col['last']] = names[1 - int(last_name_first)]
        if 2 in names.columns:
            print('The following students have more than 2 names, the name split may be incorrect:',
                  file_as_df[input_col['full']][names[2].notna()].values)
    else:
        raise Exception('First and last name column or a full name column must be specified.')

    # Deal with ID
    id_col = info_col['id']
    if 'id' in input_col.keys():
        df[id_col] = file_as_df[input_col['id']]

    if 'email' in input_col.keys():
        email_col = info_col['email']
        df[email_col] = file_as_df[input_col['email']]
        if 'id' in input_col.keys() and any(df[id_col].isna()):
            df.loc[df[id_col].isna(), id_col] = df.loc[df[id_col].isna(), email_col].str.split('@', expand=True)[0]
        else:
            df[id_col] = df[email_col].str.split('@', expand=True)[0]
    elif 'id' not in input_col.keys() and 'email' not in input_col.keys():
        raise Exception('An ID column or an email column must be provided.')

    if any(df[id_col].isna()):
        raise Exception('Some students do not have an ID nor an email:',
                        df[[info_col['first'], info_col['last']]][df[id_col].isna()].values)

    # Check for duplicate ID
    duplicates = df[id_col][df[id_col].duplicated()]
    if duplicates.shape[0] > 0:
        raise Exception('Some IDs are duplicated:', duplicates)

    # Add other columns
    other_cols = [col for col in file_as_df.columns if col not in input_col.values()]
    df = pd.concat((df, file_as_df[other_cols]), axis=1)

    # Set index to be the IDs
    df.set_index(df[id_col], drop=False, inplace=True)

    return df


def test_score(test_name, results, student_id):
    """
    Return the score of the test, given the scores all tests versions.
    """
    not_na = [result for result in results if not np.isnan(result)]
    if not not_na:
        return np.nan
    if len(not_na) > 1:
        print(f'A student has grades in multiple versions of {test_name}: {student_id}')
    return not_na[0]


def letter_conversion(x, thresholds, letters):
    """
    Converts a score in letter grade, given the thresholds and the letters.
    """
    for (i, threshold) in enumerate(thresholds):
        if x >= threshold:
            return letters[i]
    return letters[-1]


def inverse_conversion(x, thresholds, letters):
    """
    Converts a letter grade to a normalized score, given the thresholds and the letters.
    Normalized score = middle of threshold before and after
    """
    thresholds.extend([0, 100])
    index = letters.index(x)
    return (thresholds[index] + thresholds[index-1])//2
