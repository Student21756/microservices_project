from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import Column, Integer, Float, Date
from datetime import date

app = Flask(__name__)

# Konfiguracja bazy danych PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@db_invoice/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model Faktury
class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    date_issued = Column(Date, default=date.today)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "amount": self.amount,
            "date_issued": self.date_issued.isoformat()
        }

# Schemat walidacji i serializacji faktury
class InvoiceSchema(Schema):
    id = fields.Int(dump_only=True)
    order_id = fields.Int(required=True, validate=validate.Range(min=1))
    amount = fields.Float(required=True, validate=validate.Range(min=0))
    date_issued = fields.Date(dump_only=True)

invoice_schema = InvoiceSchema()

# Obsługa błędów walidacji
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({"error": error.messages}), 400

# Endpoint do dodania faktury
@app.route('/invoices', methods=['POST'])
def add_invoice():
    try:
        # Walidacja danych wejściowych
        data = invoice_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    new_invoice = Invoice(order_id=data['order_id'], amount=data['amount'])
    db.session.add(new_invoice)
    db.session.commit()
    return jsonify(invoice_schema.dump(new_invoice)), 201

# Endpoint do pobrania szczegółów faktury
@app.route('/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if invoice is None:
        return jsonify({"error": "Invoice not found"}), 404
    return jsonify(invoice_schema.dump(invoice))

# Komenda CLI do tworzenia tabel
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Initialized the invoice database.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
