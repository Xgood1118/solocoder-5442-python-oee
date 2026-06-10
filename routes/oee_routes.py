from flask import Blueprint, request, jsonify
from modules.oee import (
    get_oee_by_line,
    get_oee_by_dimension,
    get_oee_detail,
    get_all_lines_oee,
    validate_planned_time_boundary,
)

oee_bp = Blueprint('oee', __name__)


@oee_bp.route('/summary', methods=['GET'])
def oee_summary():
    line_id = request.args.get('line_id')
    product_id = request.args.get('product_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = get_oee_by_line(
        line_id=line_id, product_id=product_id, shift=shift,
        start_date=start_date, end_date=end_date
    )
    return jsonify(result)


@oee_bp.route('/by-dimension/<dimension>', methods=['GET'])
def oee_by_dimension(dimension):
    valid_dimensions = ['line', 'product', 'shift', 'date', 'week', 'month']
    if dimension not in valid_dimensions:
        return jsonify({'error': f'Invalid dimension. Must be one of: {valid_dimensions}'}), 400

    line_id = request.args.get('line_id')
    product_id = request.args.get('product_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = get_oee_by_dimension(
        dimension=dimension, line_id=line_id, product_id=product_id,
        shift=shift, start_date=start_date, end_date=end_date
    )
    return jsonify(results)


@oee_bp.route('/detail/<line_id>', methods=['GET'])
def oee_detail(line_id):
    product_id = request.args.get('product_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = get_oee_detail(
        line_id=line_id, product_id=product_id, shift=shift,
        start_date=start_date, end_date=end_date
    )
    return jsonify(result)


@oee_bp.route('/all-lines', methods=['GET'])
def all_lines_oee():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = get_all_lines_oee(start_date=start_date, end_date=end_date)
    return jsonify(results)


@oee_bp.route('/validate-boundary', methods=['GET'])
def validate_boundary():
    line_id = request.args.get('line_id')
    shift = request.args.get('shift')
    target_date = request.args.get('date')

    if not line_id or not shift or not target_date:
        return jsonify({'error': 'line_id, shift, and date are required'}), 400

    result = validate_planned_time_boundary(line_id, shift, target_date)
    return jsonify(result)
