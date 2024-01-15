import re

def pull_details_out(text):
    dc = {}
    member_no_pattern = re.compile(r'Member no: (\d+)')
    member_grade_pattern = re.compile(r'Member grade: (\w+)')
    email_pattern = re.compile(r'Email: (\S+)')

    # Extracting information
    member_no_match = member_no_pattern.search(text)
    member_grade_match = member_grade_pattern.search(text)
    email_match = email_pattern.search(text)

    # Checking if matches were found
    if member_no_match:
        member_no = member_no_match.group(1)
    else:
        member_no = None

    if member_grade_match:
        member_grade = member_grade_match.group(1)
    else:
        member_grade = None

    if email_match:
        email = email_match.group(1)
    else:
        email = None

    # Printing results
    dc['member_no'] = member_no
    dc['member_grade'] = member_grade
    dc['email'] = email
    
    return dc
