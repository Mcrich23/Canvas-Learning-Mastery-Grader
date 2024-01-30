# Canvas-Learning-Mastery-Grader
 
Automatically grade learning mastery in Canvas

## Setup
1. Clone/Download this repo
2. Go to Canvas and generate an Oauth Api Token
   - Enter in `http://127.0.0.1:5005/oauth/callback` as a URI Redirect
   - Add the following scopes:
     - Assignments Api
       - `url:GET|/api/v1/courses/:course_id/assignments`
     - Courses
       - `url:GET|/api/v1/courses`
       - `url:GET|/api/v1/courses/:course_id/students`
     - Grading Periods
       - `url:GET|/api/v1/courses/:course_id/grading_periods`
     - Outcome Groups Api
       - `url:GET|/api/v1/accounts/:account_id/outcome_groups/:id/outcomes`
       - `url:GET|/api/v1/accounts/:account_id/outcome_groups/:id/subgroups`
       - `url:GET|/api/v1/courses/:course_id/outcome_groups`
     - Outcome Results
       - `url:GET|/api/v1/courses/:course_id/outcome_results`
     - Submissions Api
       - `url:PUT|/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id`
4. Copy `.env.example` to `.env` and adjust it accordingly
   - `CANVAS_API_URL` is the base url of your canvas instance (ie. `https://example.instructure.com`)
   - `CLIENT_ID` is the non-hidden api number on Canvas (ie. `10000000000001`)
   - `CLIENT_SECRET` is the hidden api alphanumeric code on Canvas
   - For the default Oauth Signin, leave `REFRESH_TOKEN` and `API_TOKEN` as is. However, if you plan to run this headless, you may want to fill them in with values generated elsewhere
   - `GRADING_ASSIGNMENT_NAME` is the name of the assignment you want to give weight to for learning mastery (NOTE: This assignment must already exist)
5. That's it! You are all set to run `main.py`
