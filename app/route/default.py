from flask import Blueprint, jsonify, current_app

bp_default = Blueprint('default', __name__)

@bp_default.route('/', defaults={'path': ''})
@bp_default.route('/<path:path>')
def catch_all(path):
    # return jsonify({'msg': 'Por favor moço, sou pobre, tenho dinheiro pra comprar carro não... ajuda aê!!'})
    response = {
        "recommendation": str(),
        "entities": list()
    }
    return jsonify(response), 200
