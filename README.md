# dynamicfilter

HMC summer research project

To get started: 
1. Run `doxygen` in the base directory (where the `Doxyfile` is). This generates documentation in `docs`. 
1. Open `docs/html/index.html` in a web browser.
1. Check out the installation guide.

Dependencies:
- Python 2.7
- Django 1.11
- PostGreSQL
- Python Packages (psycopg2, numpy, scipy, seaborn, matplotlib)

To run a simulation:
- Install dynamicfilter (complete the installation guide)
- Start postgres `pg_ctl -D /usr/local/var/postgres start`
- Make migrations `python manage.py makemigrations` and migrate `python manage.py migrate`
- Go to `joinapp/toggles.py` to check and set parameters
  - Set the settings to control values (you can find in `controls.py`), but you can try different `JOIN_TYPE` settings. This will run 10 simulations before it finishes.
- Go to `joinapp/tests/tests_sim.py` to check which function you're running
  - There should be a function called test_overnight_sim() and one called test_multi_sim(). Comment out overnight and make sure multi is not commented out.
- Run test with `python manage.py test joinapp.tests.tests_sim`
