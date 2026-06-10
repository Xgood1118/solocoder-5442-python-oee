from flask import Blueprint, request, jsonify
from modules.production import (
    list_production_records,
    get_production_record,
    aggregate_production_by_dimension,
    validate_routing_consistency,
)
from data.mock_data import get_all_lines, get_all_products, get_routing, get_holidays

production_bp = Blueprint('production', __name__)


@production_bp.route('/records', methods=['GET'])
def list_records():
    line_id = request.args.get('line_id')
    product_id = request.args.get('product_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = list_production_records(
        line_id=line_id, product_id=product_id, shift=shift,
        start_date=start_date, end_date=end_date
    )
    return jsonify(results)


@production_bp.route('/records/<record_id>', methods=['GET'])
def get_record(record_id):
    result = get_production_record(record_id)
    if result is None:
        return jsonify({'error': 'Record not found'}), 404
    return jsonify(result)


@production_bp.route('/aggregate/<dimension>', methods=['GET'])
def aggregate(dimension):
    valid_dimensions = ['line', 'product', 'shift', 'date', 'week', 'month']
    if dimension not in valid_dimensions:
        return jsonify({'error': f'Invalid dimension. Must be one of: {valid_dimensions}'}), 400

    line_id = request.args.get('line_id')
    product_id = request.args.get('product_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = aggregate_production_by_dimension(
        dimension=dimension, line_id=line_id, product_id=product_id,
        shift=shift, start_date=start_date, end_date=end_date
    )
    return jsonify(results)


@production_bp.route('/lines', methods=['GET'])
def list_lines():
    results = get_all_lines()
    return jsonify(results)


@production_bp.route('/products', methods=['GET'])
def list_products():
    results = get_all_products()
    return jsonify(results)


@production_bp.route('/routing', methods=['GET'])
def get_routing_info():
    product_id = request.args.get('product_id')
    line_id = request.args.get('line_id')

    if not product_id or not line_id:
        return jsonify({'error': 'product_id and line_id are required'}), 400

    result = get_routing(product_id, line_id)
    if result is None:
        return jsonify({'error': 'Routing not found'}), 404
    return jsonify(result)


@production_bp.route('/validate-routing', methods=['GET'])
def validate_routing():
    product_id = request.args.get('product_id')
    line_id = request.args.get('line_id')

    if not product_id or not line_id:
        return jsonify({'error': 'product_id and line_id are required'}), 400

    result = validate_routing_consistency(product_id, line_id)
    return jsonify(result)


@production_bp.route('/holidays', methods=['GET'])
def list_holidays():
    results = get_holidays()
    return jsonify(results)
