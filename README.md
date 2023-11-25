# 449-project-2 install instructions

**1. Install dependencies**
```
sudo apt update
```
```
sudo apt install --yes ruby-foreman
```
```
python -m pip install 'fastapi[all]'
```


**2. Populate the database with sample data, from within the `api` folder run:**
```
./bin/init.sh
```

**3. Start the api**
```
foreman start --formation krakend=1,enrollment_api=3,primary=1,secondary_1=1,secondary_2=1
```

# 449-project 3
This project builds from project 2 by implementing of polyglot persistence, moving part of the data from Project 2 into Redis and the rest into DynamoDB Local.
