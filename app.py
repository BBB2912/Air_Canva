from flask import Flask, render_template, jsonify
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_paint', methods=['POST'])
def start_paint():
    # Start the Air_Canvas.py script
    subprocess.Popen(["python", "AirCanva.py"])
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(debug=True)
