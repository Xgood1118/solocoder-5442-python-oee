from flask import Blueprint, request, jsonify
from modules.alert import (
    generate_alerts,
    list_alerts,
    get_alert,
    acknowledge_alert,
    resolve_alert,
    get_alert_summary,
    check_continuous_low_oee,
)

alert_bp = Blueprint('alert', __name__)


@alert_bp.route('/generate', methods=['POST'])
def generate():
    end_date = request.json.get('end_date') if request.is_json else request.args.get('end_date')

    new_alerts = generate_alerts(end_date=end_date)
    return jsonify({
        'new_alerts_count': len(new_alerts),
        'alerts': new_alerts,
    })


@alert_bp.route('/check-continuous-low-oee', methods=['GET'])
def check_low_oee():
    line_id = request.args.get('line_id')
    end_date = request.args.get('end_date')
    consecutive_days = request.args.get('consecutive_days', type=int)
    threshold = request.args.get('threshold', type=float)

    results = check_continuous_low_oee(
        line_id=line_id, end_date=end_date,
        consecutive_days=consecutive_days, threshold=threshold
    )
    return jsonify(results)


@alert_bp.route('/list', methods=['GET'])
def list_all():
    status = request.args.get('status')
    line_id = request.args.get('line_id')
    alert_type = request.args.get('alert_type')

    results = list_alerts(
        status=status, line_id=line_id, alert_type=alert_type
    )
    return jsonify(results)


@alert_bp.route('/summary', methods=['GET'])
def summary():
    result = get_alert_summary()
    return jsonify(result)


@alert_bp.route('/<alert_id>', methods=['GET'])
def get_alert_detail(alert_id):
    result = get_alert(alert_id)
    if result is None:
        return jsonify({'error': 'Alert not found'}), 404
    return jsonify(result)


@alert_bp.route('/<alert_id>/acknowledge', methods=['POST'])
def acknowledge(alert_id):
    data = request.get_json(silent=True) or {}
    handler = data.get('handler')

    result = acknowledge_alert(alert_id, handler=handler)
    if result is None:
        return jsonify({'error': 'Alert not found or already acknowledged'}), 400
    return jsonify(result)


@alert_bp.route('/<alert_id>/resolve', methods=['POST'])
def resolve(alert_id):
    data = request.get_json(silent=True) or {}
    resolution = data.get('resolution')
    handler = data.get('handler')

    result = resolve_alert(alert_id, resolution=resolution, handler=handler)
    if result is None:
        return jsonify({'error': 'Alert not found'}), 404
    return jsonify(result)
