# dynamicfilter

HMC summer research project

To get started: 
1. Run `doxygen` in the `active` directory (where the `Doxyfile` is). This generates documentation in `active/docs`. 
1. Open `active/docs/html/index.html` in a web browser.
1. Check out the installation guide.

Dependencies:
- Python 2.7
- Django 1.11
- PostGreSQL
- Python Packages (psycopg2, numpy, scipy, seaborn, matplotlib)

To Run a Simulation:
- Install dynamicfilter
- Make migrations (python manage.py makemigrations) and migrate (python manage.py migrate)
- Go to joinapp/toggles.py to check and set parameters
- Go to tests_sim.py to check which function you're running (overnight vs single simulation)
- Run test with (python manage.py test joinapp.tests.tests_sim)