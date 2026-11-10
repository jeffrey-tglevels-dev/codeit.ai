What v1 includes:
Simple GUI where users can interact.
Take user request ex "make a diet noting application"
PM agent should ask for relvant questions, like fields, would you want graph? etc.
User confirms the plan.
PM shares final plan to architect.
Architect gives design and architecture to Devs and DB Engg.
DB Engg creates DB.
Dev creates the project with frontend + backend with predefined stack.
Packaging the app in docker image and zip file.
Preview application using docker image
Output: A demo app running through image. Option to download zip of codebase and download image.

What v1 wont do:
Ability to modify already built project.
Direct deployment.
Projects currently not stored in DB.
Registration and login.


Frontend FR:
Textbox: User enters message.
Status of which agent working: 
Textbox: for user to see and respond to PM's queries.
Preview button to preview built app.
Download button to download zip and docker image.

Backend FR:
API for user query.
API for PM's query.
5 Agents- PM, ARCHITECT, DEV, DB ENG, Q&A
Q&A reviews and sends error to DEV or DB engg.
PKG of application.
Docker image runner.
API to preview image.
API to download application zip and img.