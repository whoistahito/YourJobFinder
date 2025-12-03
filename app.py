from flask import Flask, request, jsonify, redirect
from flask_cors import CORS

from db.database_service import UserManager
from extension import db, migrate
from credential import Credential

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Credential().get_db_uri()
db.init_app(app)
migrate.init_app(app, db)
user_manager = UserManager()
# TODO: Add www to list
cors = CORS(app)

@app.route('/user', methods=['POST'])
def add_user():
    data = request.json
    email = data.get('email')
    position = data.get('position')
    location = data.get('location')
    job_type = data.get('jobType')
    skills = data.get('skills')
    experience = data.get('experience')
    education = data.get('education')
    try:
        if email is None or position is None or location is None or job_type is None:
            return jsonify({"message": "Invalid request"}), 400
        user_manager.add_user(email, position, location, job_type, skills, experience, education)
        return jsonify({"message": "User added successfully!"}), 201
    except Exception as e:
        print(e)
        return jsonify({"message": str(e)}), 500



@app.route('/user', methods=['DELETE'])
def delete_user():
    data = request.json
    email = data.get('email')
    position = data.get('position')
    location = data.get('location')
    try:
        if email is None or position is None or location is None:
            raise Exception
        user_manager.delete_user(email, position, location)
        return jsonify({"message": "User added successfully!"}), 201
    except Exception as e:
        print(e)
        return jsonify({"message": e}), 500

@app.route('/confirm/<token>', methods=['GET'])
def confirm_email(token):
    user = user_manager.confirm_user(token)
    if user:
        return redirect("https://yourjobfinder.website/confirm-email")
    else:
        return redirect("https://yourjobfinder.website/confirm-email/error")

@app.route('/', methods=['GET'])
def index():
    return redirect("https://yourjobfinder.website")




if __name__ == '__main__':
    app.run(threaded=True, port=5000)