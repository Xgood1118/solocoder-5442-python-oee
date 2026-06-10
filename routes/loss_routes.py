from flask import Blueprint, request, jsonify
from modules.loss import (
    calculate_six_big_losses,
    get_loss_pareto,
    get_loss_by_category,
    get_big_losses_detail,
)
from config import Config

loss_bp = Blueprint('loss', __name__)


@loss_bp.route('/six-big-losses', methods=['GET'])
def six_big_losses():
    line_id = request.args.get('line_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = calculate_six_big_losses(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )
    return jsonify(result)


@loss_bp.route('/pareto', methods=['GET'])
def pareto():
    line_id = request.args.get('line_id')
    shift = request.args.get('shift')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = get_loss_pareto(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )
    return jsonify(result)


@loss_bp.route('/by-category', methods=['GET'])
def by_category():
    line_id = request.args.get('line_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = get_loss_by_category(
        line_id=line_id, start_date=start_date, end_date=end_date
    )
    return jsonify(results)


@loss_bp.route('/big-losses/detail', methods=['GET'])
def big_losses_detail():
    line_id = request.args.get('line_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    results = get_big_losses_detail(
        line_id=line_id, start_date=start_date, end_date=end_date
    )
    return jsonify(results)


@loss_bp.route('/six-big-losses/types', methods=['GET'])
def six_big_losses_types():
    result = []
    for key, info in Config.SIX_BIG_LOSSES.items():
        result.append({
            'key': key,
            'name': info['name'],
            'category': info['category'],
        })
    return jsonify(result)
