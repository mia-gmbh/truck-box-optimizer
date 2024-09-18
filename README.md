# Truck Packing Optimization

Enable virtual environment
```sh
python -m venv .env
source .env/bin/activate
pipe install -r requirements
```

Start REST service:
```sh
uvicorn truck.service:app
```

Fire example data with httpie:
```sh
http :8000/truck:pack < example1.json
```
