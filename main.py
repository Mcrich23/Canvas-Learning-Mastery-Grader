import requests
import os
from dotenv import load_dotenv, set_key

load_dotenv()

# Replace these placeholders with your Canvas API details
CANVAS_API_URL = os.getenv("CANVAS_API_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")

def refresh_access_token():
    global API_TOKEN  # Declare that you want to modify the global variable

    auth_url = f"{CANVAS_API_URL}/login/oauth2/auth"
    token_url = f"{CANVAS_API_URL}/login/oauth2/token"

    # Make a request to refresh the access token
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
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    courses = response.json()
    # print(courses)
    return courses

# Function to get all students in a course
def get_students(course_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/students"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    students = response.json()
    return students

# Function to get learning mastery scores for an assignment
def get_learning_mastery(course_id, assignment_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/learning_mastery"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    learning_mastery = response.json()
    return learning_mastery

# Function to set grades for an assignment
def set_grades(course_id, assignment_id, grades):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/update_grades"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    payload = {"grade_data": grades}
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code

# Function to get assignment ID by name
def get_assignment_id_by_name(course_id, assignment_name):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    assignments = response.json()

    for assignment in assignments:
        if assignment["name"] == assignment_name:
            return assignment["id"]

    return None

# Main script
def main():
    # Get all courses in the account
    courses = get_all_courses()
    if 'errors' in courses and courses['errors'] is not None:
        new_token = refresh_access_token()
        if new_token is not None:
            main()
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

        # You can customize the assignment ID based on your needs
        ASSIGNMENT_ID = get_assignment_id_by_name(course_id, "Test")
        if ASSIGNMENT_ID is not None:
            print(ASSIGNMENT_ID)

            # # Get learning mastery scores for the assignment
            # learning_mastery = get_learning_mastery(course_id, ASSIGNMENT_ID)

            # # Calculate and set grades for the assignment
            # grades = {}
            # for student in students:
            #     user_id = student["id"]
            #     user_name = student["name"]
            #     user_scores = learning_mastery.get(str(user_id), {}).get("scores", [])

            #     # Calculate average (you may customize this calculation based on your needs)
            #     average_score = sum(user_scores) / len(user_scores) if user_scores else 0

            #     # Scale the average score to the 0-4 range
            #     scaled_grade = min(max(average_score * 4, 0), 4)

            #     # Add the scaled grade to the grades dictionary
            #     grades[user_id] = {"posted_grade": scaled_grade, "text_comment": f"Graded by script for {user_name}"}

            # # Set the calculated grades for the assignment
            # status_code = set_grades(course_id, ASSIGNMENT_ID, grades)

            # if status_code == 200:
            #     print("Grades updated successfully.")
            # else:
            #     print(f"Failed to update grades for course {course_name}. Status code: {status_code}")
        else:
            print(f"Assignment not found in course {course_name}")

if __name__ == "__main__":
    main()
