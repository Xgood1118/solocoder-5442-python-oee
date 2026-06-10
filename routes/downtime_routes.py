from flask import Blueprint, request, jsonify
from modules.downtime import (
    list_downtime_records,
    get_downtime_record,
    get_downtime_by_category,
    get_downtime_summary,
    get_big_loss_root_causes,
    aggregate_downtime_by_dimension,
)
from config import Config

downtime_bp = Blueprint('downtime', __name__)


@downtime_bp.route('/records', methods=['GET'])
def list_records():
    line_id = request.args.get('line_id')
    category = request.args.get('category')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    is_big_loss = request.args.get('is_big_loss')

    big_loss_flag = None
    if is_big_loss is not None:
        big_loss_flag = is_big_loss.lower() == 'true'

    results = list_downtime_records(
        line_id=line_id, category=category, shift=shift,
        start_date=start_date, end_date=end_date, is_big_loss=big_loss_flag
    )
    return jsonify(results)


@downtime_bp.route('/records/<record_id>', methods=['GET'])
def get_record(record_id):
    result = get_downtime_record(record_id)
    if result is None:
        return jsonify({'error': 'Record not found'}), 404
    return jsonify(result)


@downtime_bp.route('/summary', methods=['GET'])
def summary():
    line_id = request.args.get('line_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = get_downtime_summary(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )
    return jsonify(result)


@downtime_bp.route('/by-category', methods=['GET'])
def by_category():
    line_id = request.args.get('line_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = get_downtime_by_category(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )
    return jsonify(results)


@downtime_bp.route('/big-losses/root-causes', methods=['GET'])
def big_loss_root_causes():
    line_id = request.args.get('line_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = get_big_loss_root_causes(
        line_id=line_id, start_date=start_date, end_date=end_date
    )
    return jsonify(results)


@downtime_bp.route('/aggregate/<dimension>', methods=['GET'])
def aggregate(dimension):
    valid_dimensions = ['line', 'category', 'shift', 'date', 'week', 'month']
    if dimension not in valid_dimensions:
        return jsonify({'error': f'Invalid dimension. Must be one of: {valid_dimensions}'}), 400

    line_id = request.args.get('line_id')
    category = request.args.get('category')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = aggregate_downtime_by_dimension(
        dimension=dimension, line_id=line_id, category=category,
        shift=shift, start_date=start_date, end_date=end_date
    )
    return jsonify(results)


@downtime_bp.route('/categories', methods=['GET'])
def categories():
    result = []
    for key, info in Config.DOWNTIME_CATEGORIES.items():
        result.append({
            'key': key,
            'name': info['name'],
            'six_big_loss': info['six_big_loss'],
        })
    return jsonify(result)
