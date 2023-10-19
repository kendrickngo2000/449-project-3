# 449-project-2

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