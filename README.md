# newsfeed-app

## ERD Diagram

<center>
    <img src="./docs/ERD.png" alt="ERD Diagram" width="50%">
</center>

## How to run

1. Create a virtual environment

```bash
python -m venv venv
```

2. Activate the virtual environment

```bash
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create the database

```bash
python db/create_db.py
```

5. Migrate the database

```bash
python db/migrate.py
```

6. Run the app

```bash
flask run
```

7. Run the tests

```bash
pytest microservices/user_service/test_user_service.py
pytest microservices/api_gateway/test_api_gateway.py
pytest microservices/post_service/test_post_service.py
```
