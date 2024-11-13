from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import Column, Integer, String, Float

app = Flask(__name__)

# Konfiguracja bazy danych PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@db_product/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model Produktu
class Product(db.Model):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description, "price": self.price}

# Schemat walidacji i serializacji produktu
class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=3))
    description = fields.Str()
    price = fields.Float(required=True, validate=validate.Range(min=0))

product_schema = ProductSchema()

# Obsługa błędów walidacji
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({"error": error.messages}), 400

# Endpoint do dodania produktu
@app.route('/products', methods=['POST'])
def add_product():
    try:
        # Walidacja danych wejściowych
        data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    new_product = Product(name=data['name'], description=data.get('description', ''), price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify(product_schema.dump(new_product)), 201

# Endpoint do pobrania szczegółów produktu
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product_schema.dump(product))

# Komenda CLI do tworzenia tabel
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Initialized the product database.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
