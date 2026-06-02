This application is for my resume to show-case my skills      
                 
                 
                 
                 
                 
                 AI Student Helper—Project Documentation:



What This App Does
It is a web-based application, which assists students to have immediate AI-based assistance on whatever they are studying. The student logs into Google, writes his/her name only once and thereafter can pose any question and Claude AI will respond with a direct and clear simple answer. It is rather similar to a personal tutor who is available on demand, regardless of the device.

Pages
Landing Page - It is the front door of the app and the first thing that a person sees before he or she log in. It displays the name of the application, a brief explanation of what it does and a Sign in with Google button is at the center. When the student is already being logged in the page automatically skips and redirects the student to the dashboard.
Setup Page - Only shown once in a lifetime of the student at any rate, once they log in using Google, the first time. It requests the student to enter their first and last name as the app will welcome him or her on the dashboard. After submitting their name they do not come to see this page again.


Dashboard - It is the most crucial page and the core of the app. Once a student has logged in, this is where he/she will find themselves after each time. It displays a welcome message with their name on top, a big text box where they write their question, a dropdown where they can choose the subject of their question, be it Math, Science, Computer Science, History, English, or Other, and a Get Help button. On clicking the button a loading spinner will be displayed as Claude AI begins to think and the answer will be presented in a neat answer-box below the form.



History — Collaborative writing provides information on all the questions and answers asked by the student since he or she began using the app. Every post displays the topic they chose, their typed question, and the answer provided by the AI. Every student can only view his/her history which makes it personal to them.


Profile - This page provides personal details of the student that includes his or her name, Google email address and the overall number of questions he or she has already asked. It also includes an Edit Name button to enable them correct their name in case of a mistake or to change it, and a Sign Out button to leave the app.


Settings — Here the student is able to modify how the app functions to suit them. It has a dropdown to choose a default subject to avoid them having to choose it each and every time that they pose a question. It features a switch to enable light or dark theme in the entire application. It also has a Clear History button which re-writes all their past questions and answers should they wish to have a new start.
About - It is a simple informational page with details of what the app is, why it was developed, and who developed it. It contains a github link and an email address of the builder. The page is primarily helpful when a recruiter and a visitor need to know more regarding the project.

Tech Stack
The entire backend is written in Python. All the pages and routes are handled by Flask. Google Sign In can be added using Flask-Dance without having to construct it manually. The name of the student, the state of their login and the history, and settings are stored in Flask-Session between visits of the page. The AI brain that will read the question provided by the student and produce the answer is called the Claude API by Anthropic. The visual design and layout of each page are dealt with by HTML and CSS. JavaScript processes the spinner on loading, the theme of light and dark and the form submit action.

Build Order
Since just HTML and no logic are used, create the skeleton of all 7 pages first. Next add Google Sign In. Then attach the setup page to store the name of a student. Then secure the pages in such a way that they are only accessed by logged in students. Then attach the Claude API to the dashboard. Save and view history of questions. Construct the profile page then. Finally create the settings page.




Tech Stack:

The exact tech stack you are using:
Frontend — what the student sees:
HTML, CSS, and JavaScript. These 3 files build every page the student looks at and clicks on.
Backend — the brain behind the app:
Python with Flask. This handles everything that happens behind the scenes like saving the student's name, checking if they are logged in, and sending questions to the AI.
Authentication — how students log in:
Google Sign In using Flask-Dance. Students click one button and sign in with their Google account. No passwords needed.
AI — what answers the questions:
Groq API (Llama 3) as the first choice and Gemini API as the backup. Both are completely free.
Storage — where data is saved:
Flask-Session. Saves the student's name, login state, question history, and settings while they are using the app.
