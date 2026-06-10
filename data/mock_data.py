from datetime import date, timedelta
from copy import deepcopy


production_lines = {
    'line_01': {'id': 'line_01', 'name': '1号产线', 'workshop': '车间A'},
    'line_02': {'id': 'line_02', 'name': '2号产线', 'workshop': '车间A'},
    'line_03': {'id': 'line_03', 'name': '3号产线', 'workshop': '车间B'},
    'line_04': {'id': 'line_04', 'name': '4号产线', 'workshop': '车间B'},
}


products = {
    'prod_a': {'id': 'prod_a', 'name': '产品A', 'type': '标准件'},
    'prod_b': {'id': 'prod_b', 'name': '产品B', 'type': '标准件'},
    'prod_c': {'id': 'prod_c', 'name': '产品C', 'type': '定制件'},
}


routing = {
    ('prod_a', 'line_01'): {'cycle_time_minutes': 2.0, 'std_output_per_hour': 30},
    ('prod_a', 'line_02'): {'cycle_time_minutes': 2.2, 'std_output_per_hour': 27},
    ('prod_b', 'line_01'): {'cycle_time_minutes': 3.0, 'std_output_per_hour': 20},
    ('prod_b', 'line_03'): {'cycle_time_minutes': 2.8, 'std_output_per_hour': 21},
    ('prod_b', 'line_04'): {'cycle_time_minutes': 3.2, 'std_output_per_hour': 18},
    ('prod_c', 'line_02'): {'cycle_time_minutes': 5.0, 'std_output_per_hour': 12},
    ('prod_c', 'line_04'): {'cycle_time_minutes': 4.5, 'std_output_per_hour': 13},
}


_holidays = set()
_base_date = date(2026, 6, 1)
for i in range(30):
    d = _base_date + timedelta(days=i)
    if d.weekday() >= 5:
        _holidays.add(d.isoformat())

holidays = list(_holidays)


def _generate_production_and_downtime_records():
    production_records = []
    downtime_records = []

    base = date(2026, 6, 1)
    shifts = ['morning', 'afternoon', 'night']

    scenarios = {
        'line_01': {
            'good_rate_base': 0.96,
            'performance_base': 0.92,
            'downtime_per_shift': {
                'equipment_failure': {'minutes': 8, 'count': 1},
                'mold_change': {'minutes': 15, 'count': 1},
                'material_wait': {'minutes': 5, 'count': 1},
                'rest': {'minutes': 10, 'count': 1},
            },
            'products': [
                {'prod': 'prod_a', 'target': 200, 'weight': 0.6},
                {'prod': 'prod_b', 'target': 120, 'weight': 0.4},
            ],
        },
        'line_02': {
            'good_rate_base': 0.94,
            'performance_base': 0.88,
            'downtime_per_shift': {
                'equipment_failure': {'minutes': 12, 'count': 1},
                'mold_change': {'minutes': 20, 'count': 1},
                'material_wait': {'minutes': 10, 'count': 1},
                'idling': {'minutes': 8, 'count': 2},
                'rest': {'minutes': 10, 'count': 1},
            },
            'products': [
                {'prod': 'prod_a', 'target': 180, 'weight': 0.5},
                {'prod': 'prod_c', 'target': 80, 'weight': 0.5},
            ],
        },
        'line_03': {
            'good_rate_base': 0.91,
            'performance_base': 0.82,
            'downtime_per_shift': {
                'equipment_failure': {'minutes': 25, 'count': 2},
                'mold_change': {'minutes': 30, 'count': 1},
                'reduced_speed': {'minutes': 20, 'count': 1},
                'rest': {'minutes': 10, 'count': 1},
                'startup_loss': {'minutes': 5, 'count': 1},
            },
            'products': [
                {'prod': 'prod_b', 'target': 150, 'weight': 1.0},
            ],
        },
        'line_04': {
            'good_rate_base': 0.85,
            'performance_base': 0.75,
            'downtime_per_shift': {
                'equipment_failure': {'minutes': 40, 'count': 3},
                'mold_change': {'minutes': 25, 'count': 1},
                'material_wait': {'minutes': 15, 'count': 1},
                'idling': {'minutes': 10, 'count': 2},
                'reduced_speed': {'minutes': 15, 'count': 1},
                'startup_loss': {'minutes': 8, 'count': 1},
                'rest': {'minutes': 10, 'count': 1},
            },
            'products': [
                {'prod': 'prod_b', 'target': 100, 'weight': 0.5},
                {'prod': 'prod_c', 'target': 70, 'weight': 0.5},
            ],
        },
    }

    root_causes = {
        'equipment_failure': ['轴承磨损', '电机故障', '传感器失灵', '液压系统泄漏', '电路故障'],
        'mold_change': ['产品切换', '模具维修', '模具更换'],
        'material_wait': ['物料缺货', '来料检验', '物料配送延迟'],
    }

    rid = 1
    did = 1

    for day_offset in range(10):
        d = base + timedelta(days=day_offset)
        day_is_holiday = d.isoformat() in holidays

        for shift in shifts:
            for line_id, scenario in scenarios.items():
                line_skipped = day_is_holiday and line_id in ['line_03', 'line_04']
                if line_skipped:
                    continue

                shift_downtime_items = []
                shift_total_downtime = 0

                for cat, cat_cfg in scenario['downtime_per_shift'].items():
                    per_event = cat_cfg['minutes']
                    count = cat_cfg['count']

                    if day_offset % 3 == 0 and cat == 'equipment_failure':
                        per_event = per_event * 2

                    for i in range(count):
                        is_big = per_event >= 15
                        rc_list = root_causes.get(cat, [])
                        root_cause = rc_list[(day_offset + i) % len(rc_list)] if rc_list else None

                        dt_record = {
                            'id': f'dt_{did:05d}',
                            'date': d.isoformat(),
                            'shift': shift,
                            'line_id': line_id,
                            'category': cat,
                            'duration_minutes': per_event,
                            'is_big_loss': is_big,
                            'root_cause': root_cause,
                            'description': f'{cat}停机事件',
                        }
                        shift_downtime_items.append(dt_record)
                        shift_total_downtime += per_event
                        did += 1

                downtime_records.extend(shift_downtime_items)

                prod_info = scenario['products'][day_offset % len(scenario['products'])]
                product_id = prod_info['prod']
                cycle = routing.get((product_id, line_id), {}).get('cycle_time_minutes', 3.0)
                planned_minutes = 480 - 60

                actual_run_minutes = max(0, planned_minutes - shift_total_downtime)

                noise = 1 + (day_offset % 5 - 2) * 0.03
                effective_performance = scenario['performance_base'] * noise
                actual_output = max(0, int((actual_run_minutes / cycle) * min(1.0, effective_performance)))
                good_output = int(actual_output * scenario['good_rate_base'] * noise)
                good_output = min(good_output, actual_output)
                defect_output = actual_output - good_output
                theoretical_output = max(0, int(actual_run_minutes / cycle))

                prod_record = {
                    'id': f'prod_{rid:05d}',
                    'date': d.isoformat(),
                    'shift': shift,
                    'line_id': line_id,
                    'product_id': product_id,
                    'planned_production_minutes': planned_minutes,
                    'actual_run_minutes': actual_run_minutes,
                    'total_downtime_minutes': shift_total_downtime,
                    'total_output': actual_output,
                    'good_output': good_output,
                    'defect_output': defect_output,
                    'theoretical_output': theoretical_output,
                    'cycle_time_minutes': cycle,
                    'is_holiday': day_is_holiday,
                    'has_production': True,
                    'line_stopped': line_skipped,
                }
                production_records.append(prod_record)
                rid += 1

    return production_records, downtime_records


production_records, downtime_records = _generate_production_and_downtime_records()


_alerts = []
_alert_id_counter = 1


def get_all_lines():
    return deepcopy(list(production_lines.values()))


def get_line(line_id):
    return deepcopy(production_lines.get(line_id))


def get_all_products():
    return deepcopy(list(products.values()))


def get_product(product_id):
    return deepcopy(products.get(product_id))


def get_routing(product_id, line_id):
    key = (product_id, line_id)
    return deepcopy(routing.get(key))


def get_holidays():
    return list(holidays)


def is_holiday(d):
    if isinstance(d, date):
        return d.isoformat() in holidays
    return d in holidays
