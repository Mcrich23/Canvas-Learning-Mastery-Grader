# Canvas-Learning-Mastery-Grader
 
Automatically grade learning mastery in Canvas

## Setup
1. Clone/Download this repo
2. Go to Canvas and generate an Oauth Api Token
3. Copy `.env.example` to `.env` and adjust it accordingly
   - `CANVAS_API_URL` is the base url of your canvas instance (ie. `https://example.instructure.com`)
   - `CLIENT_ID` is the non-hidden api number on Canvas (ie. `10000000000001`)
   - `CLIENT_SECRET` is the hidden api alphanumeric code on Canvas
   - For the default Oauth Signin, leave `REFRESH_TOKEN` and `API_TOKEN` as is. However, if you plan to run this headless, you may want to fill them in with values generated elsewhere
   - `GRADING_ASSIGNMENT_NAME` is the name of the assignment you want to give weight to for learning mastery (NOTE: This assignment must already exist)
4. That's it! You are all set to run `main.py`
