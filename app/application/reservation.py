from app.application.utils import datetime_to_dutch_datetime_string, formiodate_to_datetime, datetime_to_formiodate
from app.application import guest as maguest
from app.data import utils as mutils, guest as mguest, settings as msettings, timeslot_configuration as mtc
from app import log
import datetime, json, sys


def prepare_reservation(code=None):
    try:
        if 'new' == code:
            empty_values = {
            'phone': '',
            'email': '',
            'full_name': '',
            'child_name': '',
            'reservation-code': 'new',
            }
            misc_config = json.loads(msettings.get_configuration_setting('import-misc-fields'))
            empty_values.update({c['veldnaam']: '' for c in misc_config})
            ret = {'default_values': empty_values,
                   'template': json.loads(msettings.get_configuration_setting('register-template')),
                   'available_timeslots': get_available_timeslots(),
                   'mode': 'new'
                   }
            return RegisterResult(RegisterResult.Result.E_OK, ret)
        else:
            guest = mguest.get_first_guest(code=code)
            if not guest:
                return RegisterResult(RegisterResult.Result.E_COULD_NOT_REGISTER)
            default_values = guest.flat()
            if guest.timeslot:
                default_values['update-reservation'] = 'true'
            ret = {'default_values': default_values,
                   'template': json.loads(msettings.get_configuration_setting('register-template')),
                   'available_timeslots': get_available_timeslots(guest.timeslot),
                   'mode': 'update'
                   }
            return RegisterResult(RegisterResult.Result.E_OK, ret)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return RegisterResult(RegisterResult.Result.E_NOK)


def delete_reservation(code):
    try:
        guest = mguest.get_first_guest(code=code)
        mguest.update_timeslot(guest, None)
        return RegisterResult(result=RegisterResult.Result.E_OK)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return RegisterResult(result=RegisterResult.Result.E_NOK)


def add_or_update_reservation(data, suppress_send_ack_email=False):
    try:
        code = data['reservation-code']
        timeslot = formiodate_to_datetime(data['radio-timeslot'])
        if 'new' == code:
            if data['email'] == '' or data['child_name'] == '':
                return RegisterResult(RegisterResult.Result.E_COULD_NOT_REGISTER)
            if not check_requested_timeslot(timeslot):
                ret = {'reservation-code': 'new'}
                return RegisterResult(RegisterResult.Result.E_TIMESLOT_FULL, ret)
            misc_config = json.loads(msettings.get_configuration_setting('import-misc-fields'))
            extra_fields = [c['veldnaam'] for c in misc_config]
            extra_field = {f: data[f] for f in extra_fields}
            guest = maguest.add_guest(full_name=data['full_name'].strip(), email=data['email'].strip())
            guest = mguest.update_guest(guest, child_name=data['child_name'].strip(), phone=data['phone'].strip(),
                                        timeslot=timeslot, misc_field=extra_field)
        else:
            guest = mguest.get_first_guest(code=code)
            if timeslot != guest.timeslot and not check_requested_timeslot(timeslot):
                return RegisterResult(RegisterResult.Result.E_TIMESLOT_FULL, guest.flat())
            guest = mguest.update_guest(guest, full_name=data['full_name'].strip(), phone=data['phone'].strip(),
                                        timeslot=timeslot)
        if guest and not suppress_send_ack_email:
            guest.set_email_send_retry(0)
            guest.set_ack_email_sent(False)
        register_ack_template = msettings.get_configuration_setting('register-ack-template')
        timeslot = datetime_to_dutch_datetime_string(guest.timeslot)
        register_ack_template = register_ack_template.replace('{{TAG_TIMESLOT}}', timeslot)
        return RegisterResult(RegisterResult.Result.E_OK, register_ack_template)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return RegisterResult(RegisterResult.Result.E_COULD_NOT_REGISTER)


def update_reservation(property, id, value):
    try:
        guest = mguest.get_first_guest(id=id)
        if 'note' == property:
            mguest.update_guest(guest, note=value)
        if 'invite_email_sent' == property:
            guest.set_invite_email_sent(value)
        elif 'ack_email_sent' == property:
            guest.set_ack_email_sent(value)
        elif 'enabled' == property:
            guest.set_enabled(value)
        elif 'email_send_retry' == property:
            guest.set_email_send_retry(value)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


reservation_changed_cb = []


def subscribe_reservation_changed(cb, opaque):
    try:
        reservation_changed_cb.append((cb, opaque))
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def guest_property_change_cb(value, opaque):
    for cb in reservation_changed_cb:
        cb[0](value, cb[1])


mguest.subscribe_enabled(guest_property_change_cb, None)
mguest.subscribe_ack_email_sent(guest_property_change_cb, None)
mguest.subscribe_nbr_ack_email_sent(guest_property_change_cb, None)
mguest.subscribe_invite_email_sent(guest_property_change_cb, None)
mguest.subscribe_nbr_invite_email_sent(guest_property_change_cb, None)
mguest.subscribe_email_send_retry(guest_property_change_cb, None)


def get_reservation_counters():
    reserved_guests = mguest.get_guests(enabled=True, timeslot_is_not_none=True)
    open_guests = mguest.get_guests(enabled=True, timeslot_is_none=True)
    child_names = [g.child_name for g in reserved_guests]
    filtered_open_guest = [g for g in open_guests if g.child_name not in child_names]
    nbr_open = len(filtered_open_guest)
    nbr_reserved = len(reserved_guests)
    nbr_total = nbr_open + nbr_reserved
    return nbr_total, nbr_open, nbr_reserved


def get_available_timeslots(default_date=None):
    try:
        timeslots = []
        timeslot_configs = mtc.get_timeslot_configurations()
        for timeslot_config in timeslot_configs:
            flat = timeslot_config.flat()
            date = timeslot_config.date
            for i in range(timeslot_config.nbr_of_timeslots):
                nbr_guests = mguest.get_guest_count(date)
                available = timeslot_config.items_per_timeslot - nbr_guests
                default_flag = default_date and date == default_date
                if default_flag:
                    available += 1
                label = f"{datetime_to_dutch_datetime_string(date)}"
                if flat['show_items_left']:
                    label = f"({available}) {label}"
                if flat['label'] != '':
                    label = f"{label} ({flat['label']})"
                timeslots.append({
                    'label':  label,
                    'value': datetime_to_formiodate(date),
                    'available': available,
                    'default': default_flag,
                    'maximum': timeslot_config.items_per_timeslot,
                })
                date += datetime.timedelta(minutes=timeslot_config.length)
        return timeslots
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return []


def datatable_get_timeslots():
    out = []
    timeslots = get_available_timeslots()
    for timeslot in timeslots:
        em = {
            'row_action': "0",
            'id': 0,
            'DT_RowId': 0,
            'timeslot': timeslot['label'],
            'nbr_total': timeslot['maximum'],
            'nbr_open': timeslot['available'],
            'nbr_reserved': timeslot['maximum'] - timeslot['available']
        }
        out.append(em)
    return out



def check_requested_timeslot(date):
    try:
        timeslots = []
        tcs = mtc.get_timeslot_configurations()
        for tc in tcs:
            start_date = tc.date
            end_date = tc.date + datetime.timedelta(minutes=(tc.nbr_of_timeslots * tc.length))
            if start_date <= date <= end_date:
                guest_count = mguest.get_guest_count(date)
                return guest_count < tc.items_per_timeslot
        return False
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return False


class RegisterResult:
    def __init__(self, result, ret={}):
        self.result = result
        self.ret = ret

    class Result:
        E_OK = 'ok'
        E_NOK = 'nok'
        E_REGISTER_OK = 'guest-ok'
        E_COULD_NOT_REGISTER = 'could-not-register'
        E_TIMESLOT_FULL = 'timeslot-full'

    result = Result.E_OK
    ret = {}

