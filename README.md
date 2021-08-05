# ImpelSurvey
A simple survey application where Admin can set up a survey, its questions, offered answer choices, and a timer (for example 5 mins or 30 mins).

# Technology used
Python. Django, PostgreSQL, Docker

# Start the project with Docker (Recomended)
To launch the project you have to install [Docker](https://docs.docker.com/engine/install/) and [Make](https://www.gnu.org/software/make/) in your PC. Then :

1. Clone the project by `git clone https://github.com/localboy/impel-survey.git`
2. Go to project directory `cd impel-survey`.
3. create a file `.env` from `sample.env` and add database and other information mentioned in the file
4. Run `make build`. It will install required packages.
5. Run `make start`. It will start the container in background.
6. Run `make superuser` to create super user.
7. Please read [Makefile](https://github.com/localboy/impel-survey/blob/master/Makefile) for more commands.
8. Go to browser [http://localhost:8000/](http://localhost:8000/)

# Start project without Docker:
1. Follow previous first three step. 
2. Create a virtual envireonment in your PC and activate it. 
3. Install required packages by `pip install -r requirements.txt`
4. Run `python manage.py migrate`
5. Run `python manage.py createsuperuser` to create admin user.
6. Run `python manage.py runserver` and got to [http://localhost:8000/](http://localhost:8000/)

# Features / Functionality
1. User must be staff user to login (since it uses admin login form for now)
2. All data of user input is stored in session during the survey time.
3. User able to navigate back and forth between questions and changes answer during the survey time.
4. There is a timer that shows the remaining time of the survey. After the timer ends, the survey will end immediately and show a timeout page. The session data will save in the backend database with the response type `Time Up`. Otherwise, the response type is always `Submitted`.
5. Users are able to participate in a survey only once. Once the survey time end, he will not able to participate again in the survey.