from modules.downtime import list_downtime_records
from modules.production import list_production_records
from config import Config
from data.mock_data import get_all_lines
from copy import deepcopy


def calculate_six_big_losses(line_id=None, shift=None, start_date=None, end_date=None):
    downtime_recs = list_downtime_records(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )
    production_recs = list_production_records(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )

    losses = {}
    for loss_key, loss_info in Config.SIX_BIG_LOSSES.items():
        losses[loss_key] = {
            'key': loss_key,
            'name': loss_info['name'],
            'category': loss_info['category'],
            'total_minutes': 0,
            'count': 0,
            'big_loss_minutes': 0,
            'big_loss_count': 0,
        }

    for dt in downtime_recs:
        cat = dt['category']
        dt_config = Config.DOWNTIME_CATEGORIES.get(cat, {})
        six_big_key = dt_config.get('six_big_loss')

        if six_big_key and six_big_key in losses:
            losses[six_big_key]['total_minutes'] += dt['duration_minutes']
            losses[six_big_key]['count'] += 1
            if dt['is_big_loss']:
                losses[six_big_key]['big_loss_minutes'] += dt['duration_minutes']
                losses[six_big_key]['big_loss_count'] += 1

    total_planned = sum(r['planned_production_minutes'] for r in production_recs)
    total_output = sum(r['total_output'] for r in production_recs)
    total_good = sum(r['good_output'] for r in production_recs)
    total_theoretical = sum(r['theoretical_output'] for r in production_recs)

    if total_planned > 0:
        total_actual_run = sum(r['actual_run_minutes'] for r in production_recs)
        performance_loss_minutes = 0
        if total_theoretical > 0 and total_actual_run > 0:
            actual_perf = total_output / total_theoretical
            perf_loss_ratio = 1 - actual_perf
            performance_loss_minutes = total_actual_run * perf_loss_ratio

        reduced_speed_minutes = performance_loss_minutes * 0.6
        idling_minutes = performance_loss_minutes * 0.4

        if 'reduced_speed' in losses:
            losses['reduced_speed']['total_minutes'] += reduced_speed_minutes
            losses['reduced_speed']['count'] += 1

        if 'idling' in losses:
            losses['idling']['total_minutes'] += idling_minutes

    if total_output > 0:
        defect_count = total_output - total_good
        if defect_count > 0:
            avg_cycle = 0
            if total_output > 0:
                total_run = sum(r['actual_run_minutes'] for r in production_recs)
                avg_cycle = total_run / total_output if total_output > 0 else 0

            quality_loss_minutes = defect_count * avg_cycle
            startup_loss_minutes = quality_loss_minutes * 0.3
            defect_loss_minutes = quality_loss_minutes * 0.7

            if 'startup_loss' in losses:
                losses['startup_loss']['total_minutes'] += startup_loss_minutes
                losses['startup_loss']['count'] += 1

            if 'quality_defect' in losses:
                losses['quality_defect']['total_minutes'] += defect_loss_minutes
                losses['quality_defect']['count'] += 1

    total_loss_minutes = sum(l['total_minutes'] for l in losses.values())

    for key in losses:
        if total_loss_minutes > 0:
            losses[key]['percentage'] = losses[key]['total_minutes'] / total_loss_minutes
        else:
            losses[key]['percentage'] = 0

    result = list(losses.values())
    result.sort(key=lambda x: x['total_minutes'], reverse=True)

    cumulative = 0
    for item in result:
        cumulative += item['percentage']
        item['cumulative_percentage'] = cumulative

    return {
        'total_loss_minutes': total_loss_minutes,
        'total_planned_minutes': total_planned,
        'losses': result,
    }


def get_loss_pareto(line_id=None, shift=None, start_date=None, end_date=None):
    result = calculate_six_big_losses(
        line_id=line_id, shift=shift, start_date=start_date, end_date=end_date
    )

    pareto_items = []
    for loss in result['losses']:
        pareto_items.append({
            'name': loss['name'],
            'key': loss['key'],
            'category': loss['category'],
            'minutes': round(loss['total_minutes'], 2),
            'percentage': round(loss['percentage'] * 100, 2),
            'cumulative_percentage': round(loss['cumulative_percentage'] * 100, 2),
        })

    return {
        'total_loss_minutes': round(result['total_loss_minutes'], 2),
        'total_planned_minutes': result['total_planned_minutes'],
        'pareto_items': pareto_items,
    }


def get_loss_by_category(line_id=None, start_date=None, end_date=None):
    downtime_recs = list_downtime_records(
        line_id=line_id, start_date=start_date, end_date=end_date
    )

    categories = {}
    for dt in downtime_recs:
        cat = dt['category']
        cat_config = Config.DOWNTIME_CATEGORIES.get(cat, {})
        if cat not in categories:
            categories[cat] = {
                'category': cat,
                'name': cat_config.get('name', cat),
                'six_big_loss': cat_config.get('six_big_loss'),
                'total_minutes': 0,
                'count': 0,
                'big_loss_count': 0,
                'big_loss_minutes': 0,
            }
        categories[cat]['total_minutes'] += dt['duration_minutes']
        categories[cat]['count'] += 1
        if dt['is_big_loss']:
            categories[cat]['big_loss_count'] += 1
            categories[cat]['big_loss_minutes'] += dt['duration_minutes']

    total_minutes = sum(c['total_minutes'] for c in categories.values())
    for cat in categories.values():
        cat['percentage'] = cat['total_minutes'] / total_minutes if total_minutes > 0 else 0

    result = list(categories.values())
    result.sort(key=lambda x: x['total_minutes'], reverse=True)
    return result


def get_big_losses_detail(line_id=None, start_date=None, end_date=None):
    big_losses = list_downtime_records(
        line_id=line_id, start_date=start_date, end_date=end_date, is_big_loss=True
    )

    grouped = {}
    for loss in big_losses:
        key = loss['category']
        if key not in grouped:
            grouped[key] = {
                'category': key,
                'name': Config.DOWNTIME_CATEGORIES.get(key, {}).get('name', key),
                'total_minutes': 0,
                'count': 0,
                'root_causes': {},
            }
        grouped[key]['total_minutes'] += loss['duration_minutes']
        grouped[key]['count'] += 1

        rc = loss.get('root_cause') or '未记录'
        if rc not in grouped[key]['root_causes']:
            grouped[key]['root_causes'][rc] = {'root_cause': rc, 'minutes': 0, 'count': 0}
        grouped[key]['root_causes'][rc]['minutes'] += loss['duration_minutes']
        grouped[key]['root_causes'][rc]['count'] += 1

    for key in grouped:
        rc_list = list(grouped[key]['root_causes'].values())
        rc_list.sort(key=lambda x: x['minutes'], reverse=True)
        grouped[key]['root_causes'] = rc_list

    result = list(grouped.values())
    result.sort(key=lambda x: x['total_minutes'], reverse=True)
    return result
