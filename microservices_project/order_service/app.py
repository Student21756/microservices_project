from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import Column, Integer, Float

app = Flask(__name__)

# Konfiguracja bazy danych PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@db_order/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model Zamówienia
class Order(db.Model):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_price": self.total_price
        }

# Schemat walidacji i serializacji zamówienia
class OrderSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True, validate=validate.Range(min=1))
    product_id = fields.Int(required=True, validate=validate.Range(min=1))
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    total_price = fields.Float(required=True, validate=validate.Range(min=0))

order_schema = OrderSchema()

# Obsługa błędów walidacji
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({"error": error.messages}), 400

# Endpoint do dodania zamówienia
@app.route('/orders', methods=['POST'])
def add_order():
    try:
        # Walidacja danych wejściowych
        data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    new_order = Order(
        user_id=data['user_id'],
        product_id=data['product_id'],
        quantity=data['quantity'],
        total_price=data['total_price']
    )
    db.session.add(new_order)
    db.session.commit()
    return jsonify(order_schema.dump(new_order)), 201

# Endpoint do pobrania szczegółów zamówienia
@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order_schema.dump(order))

# Komenda CLI do tworzenia tabel
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Initialized the order database.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
