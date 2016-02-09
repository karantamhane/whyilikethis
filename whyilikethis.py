from flask import Flask

app = Flask(__name__)


@app.route('/')
def home_page():
    return "This is the response from your home page!"

if __name__ == '__main__':
    app.run()
