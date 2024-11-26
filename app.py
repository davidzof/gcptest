# app.py
from flask import Flask
import datetime

app = Flask(__name__)

@app.route("/")
def hello_world():
    today = datetime.date.now()
    return "Hello, World! " + today

if __name__ == '__main__':
    app.run(debug=True, port=8080)
