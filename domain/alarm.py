# """Cột và trạng thái dùng chung cho Alarm LI (không phụ thuộc Qt)."""
# STATUSES = ('Chưa tiến hành', 'Đang thực hiện', 'Đã hoàn thành')
# TRACKING_FIELDS = ('status', 'quick_check_result', 'cal_check_result',
#                    'engineer_action', 'monitor_day1', 'monitor_day2',
#                    'monitor_day3', 'comment')
# COLUMNS = (
#     ('No', None), ('Alarm Date', 'alarm_date'), ('EQP', 'eqp'), ('Slot', 'slot'),
#     ('Fail comment', 'fail_comment'), ('Start time', 'start_datetime'),
#     ('End time', 'end_datetime'), ('Yield 15', 'yield_15'), ('Target 15', 'target_15'),
#     ('Yield 30', 'yield_30'), ('Target 30', 'target_30'), ('Scrap code', 'scrap_codes'),
#     ('LOTID', 'lotids'), ('Model', 'models'), ('Status', 'status'),
#     ('Date complete', 'date_complete'), ('Quick check result', 'quick_check_result'),
#     ('Cal check result', 'cal_check_result'), ('Engineer action', 'engineer_action'),
#     ('Monitor day 1', 'monitor_day1'), ('Monitor day 2', 'monitor_day2'),
#     ('Monitor day 3', 'monitor_day3'), ('Comment', 'comment'),
# )
"""Cột và trạng thái dùng chung cho Alarm LI (không phụ thuộc Qt)."""
STATUSES = ('Chưa tiến hành', 'Đang thực hiện', 'Đã hoàn thành')
CHECK_RESULTS = ('PASS', 'FAIL')
TRACKING_FIELDS = ('status', 'quick_check_result', 'cal_check_result',
                   'engineer_action', 'comment')
COLUMNS = (
    ('No', None), ('Alarm Date', 'alarm_date'), ('EQP', 'eqp'), ('Slot', 'slot'),
    ('Fail comment', 'fail_comment'), ('Start time', 'start_datetime'),
    ('End time', 'end_datetime'), ('Yield 15', 'yield_15'), ('Target 15', 'target_15'),
    ('Yield 30', 'yield_30'), ('Target 30', 'target_30'), ('Scrap code', 'scrap_codes'),
    ('LOTID', 'lotids'), ('Model', 'models'), ('Status', 'status'),
    ('Date complete', 'date_complete'), ('Quick check result', 'quick_check_result'),
    ('Cal check result', 'cal_check_result'), ('Engineer action', 'engineer_action'),
    ('Monitor day 1', 'monitor_day1'), ('Monitor day 2', 'monitor_day2'),
    ('Monitor day 3', 'monitor_day3'), ('Comment', 'comment'),
)
