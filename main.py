import requests
import os
from dotenv import load_dotenv, set_key
from flask import Flask, request
from werkzeug.serving import make_server
import threading
from datetime import datetime
import numpy as np
import urllib
import json

load_dotenv()

CANVAS_API_URL = os.getenv("CANVAS_API_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
GRADING_ASSIGNMENT_NAME = os.getenv("GRADING_ASSIGNMENT_NAME")

app = Flask(__name__)

# Flag to signal when the OAuth callback has happened
callback_done = False
server = None
session = requests.Session()

scopes = [
    "url:GET|/api/v1/courses/:course_id/assignments",
    "url:GET|/api/v1/courses",
    "url:GET|/api/v1/courses/:course_id/students",
    "url:GET|/api/v1/courses/:course_id/grading_periods",
    "url:GET|/api/v1/courses/:course_id/outcome_groups/:id/outcomes",
    "url:GET|/api/v1/courses/:course_id/outcome_rollups",
    "url:GET|/api/v1/courses/:course_id/outcome_groups/:id/subgroups",
    "url:GET|/api/v1/courses/:course_id/outcome_groups",
    "url:GET|/api/v1/courses/:course_id/outcome_results",
    "url:GET|/api/v1/outcomes/:id",
    "url:PUT|/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id",
    "url:GET|/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id"
]

@app.route("/oauth/callback")
def oauth_callback():
    global callback_done, API_TOKEN, REFRESH_TOKEN
    auth_code = request.args.get("code")

    if auth_code:
        token_url = f"{CANVAS_API_URL}/login/oauth2/token"

        scope_string = " ".join(scopes)
        response = requests.post(
            token_url,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": "http://127.0.0.1:5005/oauth/callback",
                "scope": scope_string,
            },
        )

        if response.status_code == 200:
            new_token = response.json().get("access_token")
            refresh_token = response.json().get("refresh_token")

            # Update the access token in the environment variables or configuration
            API_TOKEN = new_token
            REFRESH_TOKEN = refresh_token

            # Update the live env
            os.environ["API_TOKEN"] = new_token
            os.environ["REFRESH_TOKEN"] = refresh_token

            # Update the .env file
            set_key('.env', 'API_TOKEN', new_token)
            set_key('.env', 'REFRESH_TOKEN', refresh_token)

            print("Access token refreshed successfully.")
            callback_done = True  # Set the flag to True when callback is done
            return "Access token refreshed successfully. You can close this window now."

    return "Failed to refresh access token. Check your logs for details."

def run_flask_server():
    global server
    server = make_server('localhost', 5005, app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # Handle the keyboard interrupt (Ctrl+C)
        server.shutdown()

def stop_flask_server():
    global server
    if server:
        server.shutdown()

def refresh_access_token():
    global API_TOKEN, callback_done

    auth_url = f"{CANVAS_API_URL}/login/oauth2/auth"
    token_url = f"{CANVAS_API_URL}/login/oauth2/token"
    
    # If refresh token is not available, perform the full OAuth2 flow
    if REFRESH_TOKEN is None or REFRESH_TOKEN == "" or REFRESH_TOKEN == "<REFRESH_TOKEN>":
        scope_string = " ".join(scopes)
        scope_encoded = urllib.parse.quote(scope_string)
        auth_code_url = f"{auth_url}?client_id={CLIENT_ID}&scope={scope_encoded}&response_type=code&redirect_uri=http://127.0.0.1:5005/oauth/callback"
        print(f"Open the following URL in your browser to continue authorization:\n{auth_code_url}")

        # Start the Flask server in a separate thread
        threading.Thread(target=run_flask_server).start()

        # Wait until the callback is done
        while not callback_done:
            pass

        stop_flask_server()
        return API_TOKEN
        # return None
    else:
        # Use the refresh token to obtain a new access token
        response = requests.post(
            token_url,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": REFRESH_TOKEN,
                "grant_type": "refresh_token",
                "scope": " ".join(scopes),
            }
        )

    if response.status_code == 200:
        # Update the access token in the environment variables or configuration
        new_token = response.json().get("access_token")
        API_TOKEN = new_token

        # Update the live env
        os.environ["API_TOKEN"] = new_token

        # Update the .env file
        set_key('.env', 'API_TOKEN', new_token)

        print("Access token refreshed successfully.")
        return new_token
    else:
        print(f"Failed to refresh access token. Status code: {response.status_code}")
        return None

# Function to get all courses in the account
def get_all_courses():
    url = f"{CANVAS_API_URL}/api/v1/courses"
    response = session.get(url)
    courses = response.json()
    return courses

# Function to get all students in a course
def get_students(course_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/students"
    response = session.get(url)
    students = response.json()
    return students

def get_learning_mastery_outcome(course_id, outcome_group_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/outcome_groups/{outcome_group_id}/outcomes"
    response = session.get(url)
    learning_mastery = response.json()
    # print(f'Learning Mastery for group {outcome_group_id}: {learning_mastery}')
    outcome_ids = [outcome['outcome']['id'] for outcome in learning_mastery]
    return outcome_ids

# Function to get learning mastery scores for an assignment
def get_learning_mastery_id_list(course_id, group_id):
    root_url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/outcome_groups/{group_id}/subgroups"
    root_response = session.get(root_url)
    root_learning_mastery = root_response.json()
    outcomes = get_learning_mastery_outcome(course_id, group_id) # start with non subgrouped outcomes
    if root_learning_mastery is not None:
        for group in root_learning_mastery:
            new_outcomes = get_learning_mastery_outcome(course_id, group['id'])
            outcomes.append(new_outcomes)
    if outcomes is not None:
        return np.array(outcomes).flatten().tolist()
    else:
        return None
    
def get_learning_mastery(course_id, student_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/outcome_rollups?user_ids={student_id}"
    response = session.get(url)
    learning_mastery = response.json()
    return learning_mastery

# Function to set grades for an assignment
def set_grade(course_id, assignment_id, student_id, grade):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}?submission[posted_grade]={grade}"
    response = session.put(url)
    return response.status_code

# Function to set grades for an assignment
def get_grade(course_id, assignment_id, student_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}"
    response = session.get(url)
    return response.json()['entered_grade']

def get_mastery_group_id(course_id, group_name):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/outcome_groups"
    response = session.get(url)
    mastery_groups = response.json()

    for group in mastery_groups:
        if group["title"] == group_name:
            return group["id"]

    return None

# Function to get assignment ID by name
def get_assignment_by_name(course_id, assignment_name):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments"
    response = session.get(url)
    assignments = response.json()

    for assignment in assignments:
        if assignment["name"] == assignment_name:
            return assignment

    return None

def get_current_grading_period(course_id):
    # Canvas API URL for grading periods
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/grading_periods"

    # Make a GET request to the Canvas API
    response = session.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        grading_periods_data = response.json()

        # Get the current date and time
        current_datetime = datetime.utcnow()

        # Find the grading period that is currently active
        for period in grading_periods_data.get('grading_periods', []):
            start_date = datetime.strptime(period['start_date'], '%Y-%m-%dT%H:%M:%SZ')
            end_date = datetime.strptime(period['end_date'], '%Y-%m-%dT%H:%M:%SZ')

            if start_date <= current_datetime <= end_date:
                return period['title']

        # If no active grading period is found, return None
        return None

    else:
        # Print an error message if the request was not successful
        print(f"Failed to fetch grading periods. Status code: {response.status_code}")
        return None

def get_outcome_details(outcome_id):
    # Get outcome details for id
    url = f"{CANVAS_API_URL}/api/v1/outcomes/{outcome_id}"
    response = session.get(url)
    outcome = response.json()
    return outcome

def get_outcome_percentage(raw_score, outcome_id):
    # Get outcome details
    outcome_details = get_outcome_details(outcome_id)

    # Get the maximum score for the outcome
    max_score = outcome_details['points_possible']

    # Return the fraction of the raw score to the maximum score
    return raw_score/max_score

# Main script
def main():
    session.headers = {"Authorization": f"Bearer {API_TOKEN}"}
    # Get all courses in the account
    courses = get_all_courses()
    if 'errors' in courses and courses['errors'] is not None:
        if courses['errors'][0]['message'] == 'Invalid access token.' or courses['errors'][0]['message'] == 'user authorization required' or courses['errors'][0]['message'] == 'Insufficient scopes on access token.':
            new_token = refresh_access_token()
            if new_token is not None:
                print('Running fetch again...\n')
                main()
                return
            else:
                print(f'courses returned with errors:\n\n{courses["errors"]}\n')
                return
        else:
            print(f'courses returned with errors:\n\n{courses["errors"]}\n')
            return

    for course in courses:
        course_id = course["id"]
        course_name = course["name"]
        print(f"Processing course: {course_name}")

        current_period = get_current_grading_period(course_id)
        print(f"Current grading period: {current_period}")

        print('')

        # Get the mastery group ID
        mastery_group = get_mastery_group_id(course_id, current_period)
        # Get students in the course
        students = get_students(course_id)

        # Get the grading calculator assignment
        assignment = get_assignment_by_name(course_id, GRADING_ASSIGNMENT_NAME)
        # Get the maximum points for the grading calculator assignment
        max_assignment_points = assignment['points_possible']

        # get allowed list of outcomes
        learning_mastery_id_list = get_learning_mastery_id_list(course_id, mastery_group)
        learning_mastery_id_list = [str(outcome_id) for outcome_id in learning_mastery_id_list]

        if assignment is not None:
            # You can customize the assignment ID based on your needs
            ASSIGNMENT_ID = assignment['id']

            # # Calculate and set grades for the assignment
            for student in students:
                user_id = student["id"]
                user_name = student["name"]

                # # Get learning mastery scores for the assignment
                learning_mastery_rollups = get_learning_mastery(course_id, user_id)["rollups"]
                learning_mastery = [score for rollup in learning_mastery_rollups for score in rollup['scores']]

                if len(learning_mastery) == 0:
                    # Do nothing if there are no learning mastery scores
                    print(f'No learning mastery for {user_name} in course {course_name}')
                else:

                    # Get score percentages for each outcome
                    all_score_percentages = [get_outcome_percentage(score['score'], score["links"]["outcome"]) for score in learning_mastery if 'score' in score]
                    
                    # Calculate the average score percentage
                    average_score_percentage = sum(all_score_percentages) / len(all_score_percentages) if all_score_percentages else 0
                    
                    # Convert the average score percentage to the actual score
                    average_score = average_score_percentage * max_assignment_points

                    if average_score is not None:
                        # Check if the current grade is the same as the calculated grade
                        current_grade = get_grade(course_id, ASSIGNMENT_ID, user_id)
                        if current_grade is not None and f'{current_grade}' == f'{average_score}':
                            # Do nothing if the grade is already up to date
                            print(f"Grade already up to date for {user_name} in course {course_name}")
                        else:
                            # Set the grade for the assignment if it is different
                            updated_grade = set_grade(course_id, ASSIGNMENT_ID, user_id, average_score)

                            if updated_grade == 200:
                                print(f"Grade updated for {user_name} in course {course_name} with {average_score}")
                            else:
                                print(f"Failed to update grade for {user_name} in course {course_name}")
                    print('')
        else:
            print(f"Assignment not found in course {course_name}")

if __name__ == "__main__":
    main()
