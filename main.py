import requests
import os
from dotenv import load_dotenv, set_key
from flask import Flask, request
from werkzeug.serving import make_server
import threading
import time

import requests

load_dotenv()

CANVAS_API_URL = os.getenv("CANVAS_API_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")

app = Flask(__name__)

# Flag to signal when the OAuth callback has happened
callback_done = False
server = None
session = requests.Session()

@app.route("/oauth/callback")
def oauth_callback():
    global callback_done, API_TOKEN, REFRESH_TOKEN
    auth_code = request.args.get("code")

    if auth_code:
        token_url = f"{CANVAS_API_URL}/login/oauth2/token"

        response = requests.post(
            token_url,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": "http://127.0.0.1:5005/oauth/callback",
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
        auth_code_url = f"{auth_url}?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://127.0.0.1:5005/oauth/callback"
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
                "grant_type": "refresh_token"
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
    # print(courses)
    return courses

# Function to get all students in a course
def get_students(course_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/students"
    response = session.get(url)
    students = response.json()
    return students

# Function to get learning mastery scores for an assignment
def get_learning_mastery(course_id, student_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/outcome_results?user_ids={student_id}"
    response = session.get(url)
    learning_mastery = response.json()
    return learning_mastery

# Function to set grades for an assignment
def set_grade(course_id, assignment_id, student_id, grade):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}?submission[posted_grade]={grade}"
    response = session.put(url)
    return response.status_code

# Function to get assignment ID by name
def get_assignment_by_name(course_id, assignment_name):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments"
    response = session.get(url)
    assignments = response.json()

    for assignment in assignments:
        if assignment["name"] == assignment_name:
            return assignment

    return None

# Function to calculate the average of 'percent' values in learning mastery results
def calculate_average_percent(learning_mastery):
    if 'outcome_results' in learning_mastery:
        results = learning_mastery['outcome_results']
        if results:
            percent_values = [result['percent'] for result in results]
            average_percent = sum(percent_values) / len(percent_values)
            return average_percent
    return None

# Main script
def main():
    session.headers = {"Authorization": f"Bearer {API_TOKEN}"}
    # Get all courses in the account
    courses = get_all_courses()
    if 'errors' in courses and courses['errors'] is not None:
        if courses['errors'][0]['message'] == 'Invalid access token.' or courses['errors'][0]['message'] == 'user authorization required':
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

        # Get students in the course
        students = get_students(course_id)

        assignment = get_assignment_by_name(course_id, "Grading Calculator")
        if assignment is not None:
            # You can customize the assignment ID based on your needs
            ASSIGNMENT_ID = assignment['id']
            # print(ASSIGNMENT_ID)

            # # Calculate and set grades for the assignment
            for student in students:
                # print(student)
                user_id = student["id"]
                user_name = student["name"]

                # # Get learning mastery scores for the assignment
                learning_mastery = get_learning_mastery(course_id, user_id)

                # print(learning_mastery)
                average_percent = calculate_average_percent(learning_mastery)
                print(f'{user_name}\'s learning mastery average percent: {average_percent}')

                if average_percent is not None:
                    final_grade = average_percent*4
                    updated_grade = set_grade(course_id, ASSIGNMENT_ID, user_id, final_grade)

                    if updated_grade == 200:
                        print(f"Grade updated for {user_name} in course {course_name}")
                    else:
                        print(f"Failed to update grade for {user_name} in course {course_name}")
        else:
            print(f"Assignment not found in course {course_name}")

if __name__ == "__main__":
    main()
