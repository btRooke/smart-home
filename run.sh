(cd Website;
python3 -m http.server 8000) &

(cd Controller;
export FLASK_APP=controller_api.py;
python3 -m flask run -h 0.0.0.0;)
