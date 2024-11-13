from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

#Route initiale
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
