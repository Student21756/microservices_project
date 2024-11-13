# user_service/app.py

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import Column, Integer, String

app = Flask(__name__)

# Konfiguracja bazy danych PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@db_user/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model użytkownika
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email}

# Schemat walidacji i serializacji użytkownika
class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3))
    email = fields.Email(required=True)

user_schema = UserSchema()

# Obsługa błędów walidacji
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({"error": error.messages}), 400

# Endpoint do dodania użytkownika z walidacją danych
@app.route('/users', methods=['POST'])
def add_user():
    try:
        # Walidacja danych wejściowych
        data = user_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    # Sprawdzanie czy email jest unikalny
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already in use"}), 409

    new_user = User(username=data['username'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(user_schema.dump(new_user)), 201

# Endpoint do pobrania szczegółów użytkownika
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_schema.dump(user))

# Dodajemy komendę CLI do tworzenia tabel
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Initialized the database.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
