# Canvas-Learning-Mastery-Grader
 
Automatically grade learning mastery in Canvas

## Why is this important?

Canvas by Instructure has two modes for grading: Letter Based Grading (LBG), and Standards Based Grading (SBG). Standards Based Grading has many benifits such as grading students on an objective standard to completely judge the ability and performance of students on their performance indtead of anything else. However, there is one major issue; Canvas is unable to transform this grade diectly into a letter grade for students to easily view. Enter this simple GitHub repository. Canvas-Learning-Mastery-Grader is a set of python scripts to automatically handle just this. Simply follow (Setup)[#Setup] to get started and start accurately reflecting students grades in near realtime. 


## How it Works

1. It gets all courses the authenticated user has access to
2. Then it searches for an assignment equal to the `GRADING_ASSIGNMENT_NAME` environment variable
3. For each course that contains this, it iterates over every student in the course geting their outcome grades and generating percentages for each outcome
4. It averages those percentages and sets the grading assignments grade based on the scale of its maximum points

## Setup
1. Clone/Download this repo
2. Go to Canvas and generate an Oauth Api Token
   - Enter in `http://127.0.0.1:5005/oauth/callback` as a URI Redirect
   - If you choose to enforce scopes, enable the following:
     - Assignments Api
       - `url:GET|/api/v1/courses/:course_id/assignments`
     - Courses
       - `url:GET|/api/v1/courses`
       - `url:GET|/api/v1/courses/:course_id/students`
     - Grading Periods
       - `url:GET|/api/v1/courses/:course_id/grading_periods`
     - Outcome Groups Api
       - `url:GET|/api/v1/courses/:courses/outcome_groups/:id/outcomes`
       - `url:GET|/api/v1/courses/:courses/outcome_groups/:id/subgroups`
       - `url:GET|/api/v1/courses/:course_id/outcome_groups`
     - Outcome Results
       - `url:GET|/api/v1/courses/:course_id/outcome_results`
       - `url:GET|/api/v1/courses/:course_id/outcome_rollups`
     - Submissions Api
       - `url:PUT|/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id`
       - `url:GET|/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id`
4. Copy `.env.example` to `.env` and adjust it accordingly
   - `CANVAS_API_URL` is the base url of your canvas instance (ie. `https://example.instructure.com`)
   - `CLIENT_ID` is the non-hidden api number on Canvas (ie. `10000000000001`)
   - `CLIENT_SECRET` is the hidden api alphanumeric code on Canvas
   - For the default Oauth Signin, leave `REFRESH_TOKEN` and `API_TOKEN` as is. However, if you plan to run this headless, you may want to fill them in with values generated elsewhere
   - `GRADING_ASSIGNMENT_NAME` is the name of the assignment you want to give weight to for learning mastery (NOTE: This assignment must already exist)
5. That's it! You are all set to run `main.py`
