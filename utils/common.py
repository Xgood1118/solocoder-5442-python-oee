from config import Config


def get_color_level(value):
    if value >= Config.OEE_GREEN_THRESHOLD:
        return 'green'
    elif value >= Config.OEE_YELLOW_THRESHOLD:
        return 'yellow'
    else:
        return 'red'


def get_oee_grade(oee):
    if oee >= Config.OEE_WORLD_CLASS:
        return {'grade': 'world_class', 'name': '世界级', 'description': 'OEE >= 85%，达到世界级水平'}
    elif oee >= Config.OEE_EXCELLENT:
        return {'grade': 'excellent', 'name': '优秀', 'description': '70% <= OEE < 85%，表现优秀'}
    elif oee >= Config.OEE_AVERAGE:
        return {'grade': 'average', 'name': '一般', 'description': '60% <= OEE < 70%，行业平均水平'}
    else:
        return {'grade': 'poor', 'name': '差', 'description': 'OEE < 60%，需要重点改善'}


def format_percent(value):
    return round(value * 100, 2)
