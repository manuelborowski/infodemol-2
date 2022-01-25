from app.data import timeslot_configuration as mtc, settings as msettings
from app import log, db
import datetime, sys, json


def add_timeslot_configuration(date, length, nbr_of_timeslots, items_per_timeslot):
    try:
        tc = mtc.get_first_timeslot_configuration(date, length, nbr_of_timeslots, items_per_timeslot)
        if tc:
            return
        mtc.add_timeslot_configuration(date, length, nbr_of_timeslots, items_per_timeslot)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

def timeslot_configuration_changed_cb(value, opaque):
    try:
        new_tcs = None
        try:
            new_tcs = json.loads(value)
        except:
            pass
        if new_tcs:
            tcs = mtc.get_timeslot_configurations()
            mtc.delete_timeslot_configuration(tc_list = tcs)
            for tc in new_tcs:
                misc_fields = {
                    'label': tc['label'],
                    'show_items_left': tc['toon_aantal'] != 0
                }
                mtc.add_timeslot_configuration(datetime.datetime(tc['jaar'], tc['maand'], tc['dag'], tc['uur'], tc['minuut']),
                                               tc['lengte'], tc['aantal'], tc['plaatsen'], misc_fields)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


msettings.subscribe_setting_changed('timeslot-config-template', timeslot_configuration_changed_cb, None)



# add_timeslot_configuration(datetime.datetime(2021, 5, 1, 9, 0), 15, 12, 8)
# add_timeslot_configuration(datetime.datetime(2021, 5, 1, 12, 0), 15, 4, 5)
# add_timeslot_configuration(datetime.datetime(2021, 5, 1, 13, 0), 15, 16, 8)
# add_timeslot_configuration(datetime.datetime(2021, 5, 5, 13, 0), 15, 16, 5)
