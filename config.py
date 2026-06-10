import os
from datetime import time

class Config:
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    OEE_GREEN_THRESHOLD = 0.85
    OEE_YELLOW_THRESHOLD = 0.60

    OEE_WORLD_CLASS = 0.85
    OEE_EXCELLENT = 0.70
    OEE_AVERAGE = 0.60

    BIG_LOSS_THRESHOLD_MINUTES = 15

    ALERT_CONSECUTIVE_DAYS = 3
    ALERT_OEE_THRESHOLD = 0.60

    SHIFTS = {
        'morning': {
            'name': '早班',
            'start': time(8, 0),
            'end': time(16, 0),
            'planned_minutes': 480,
            'break_minutes': 60,
        },
        'afternoon': {
            'name': '中班',
            'start': time(16, 0),
            'end': time(0, 0),
            'planned_minutes': 480,
            'break_minutes': 60,
        },
        'night': {
            'name': '夜班',
            'start': time(0, 0),
            'end': time(8, 0),
            'planned_minutes': 480,
            'break_minutes': 60,
        },
    }

    DOWNTIME_CATEGORIES = {
        'equipment_failure': {'name': '设备故障', 'six_big_loss': 'breakdown'},
        'mold_change': {'name': '模具更换', 'six_big_loss': 'setup'},
        'material_wait': {'name': '物料等待', 'six_big_loss': 'setup'},
        'shift_change': {'name': '换班', 'six_big_loss': 'setup'},
        'rest': {'name': '休息', 'six_big_loss': 'breakdown'},
        'planned_maintenance': {'name': '计划内维护', 'six_big_loss': 'breakdown'},
        'idling': {'name': '空转短暂停机', 'six_big_loss': 'idling'},
        'reduced_speed': {'name': '减速运行', 'six_big_loss': 'reduced_speed'},
        'startup_loss': {'name': '启动不良', 'six_big_loss': 'startup_loss'},
    }

    SIX_BIG_LOSSES = {
        'breakdown': {'name': '故障停机', 'category': 'availability'},
        'setup': {'name': '换模换线', 'category': 'availability'},
        'idling': {'name': '空转短暂停机', 'category': 'performance'},
        'reduced_speed': {'name': '减速运行', 'category': 'performance'},
        'startup_loss': {'name': '启动不良', 'category': 'quality'},
        'quality_defect': {'name': '良品率损失', 'category': 'quality'},
    }
