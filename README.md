# flask-rbac

## Run Steps
1. `pip install -r requirements.txt`
2. `flask run`
3. http://127.0.0.1:5000


- alice password123  #Admin
- bob password456  #User

## Running UWSGI
```bash
uwsgi --ini uwsgi.ini
```
Note the uwsgi binary must be the one inside the venv, not a system wide one

## Request Items
```bash
curl -X GET -H "Content-Type: application/json" http://127.0.0.1:9090/items
```
