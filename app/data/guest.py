from app.data.models import Guest
from sqlalchemy import not_
from app import log, db
import sys, json


def add_guest_bulk(full_name=None, child_name=None, phone=None, email=None, code=None):
    try:
        guest = Guest(full_name=full_name, child_name=child_name, phone=phone, email=email, code=code)
        db.session.add(guest)
        return guest
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def guest_bulk_commit():
    try:
        db.session.commit()
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def add_guest(full_name=None, child_name=None,phone=None, email=None, code=None):
    try:
        guest = add_guest_bulk(full_name=full_name, child_name=child_name, phone=phone, email=email, code=code)
        guest_bulk_commit()
        return guest
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_guests(id=None, email=None, code=None, timeslot=None, enabled=None, timeslot_is_not_none=False, timeslot_is_none=False,  first=False, count=False):
    try:
        guests = Guest.query
        if id:
            guests = guests.filter(Guest.id == id)
        if email:
            guests = guests.filter(Guest.email == email)
        if code:
            guests = guests.filter(Guest.code == code)
        if timeslot:
            guests = guests.filter(Guest.timeslot == timeslot)
        if enabled is not None:
            guests = guests.filter(Guest.enabled == enabled)
        if timeslot_is_not_none:
            guests = guests.filter(Guest.timeslot != None)
        if timeslot_is_none:
            guests = guests.filter(Guest.timeslot == None)
        if first:
            guest = guests.first()
            return guest
        if count:
            return guests.count()
        guests = guests.all()
        return guests
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_first_guest(id=None, email=None, code=None):
    try:
        guest = get_guests(id=id, email=email, code=code, first=True)
        return guest
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_guest_count(timeslot=None):
    try:
        count = get_guests(timeslot=timeslot, enabled=True, count=True)
        return count
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return -1


def update_guest(guest, full_name=None, child_name=None, phone=None, email=None, timeslot=None, note=None, misc_field=None):
    guest = update_guest_bulk(guest, full_name=full_name, child_name=child_name, phone=phone, email=email,
                              timeslot=timeslot, note=note, misc_field=misc_field)
    guest_bulk_commit()
    return guest


def update_guest_bulk(guest, full_name=None, child_name=None, phone=None, email=None, timeslot=None, note=None, misc_field=None):
    try:
        if full_name:
            guest.full_name = full_name
        if child_name:
            guest.child_name = child_name
        if phone:
            guest.phone = phone
        if email:
            guest.email = email
        if timeslot:
            guest.timeslot = timeslot
        if note is not None:
            guest.note = note
        if misc_field is not None:
            guest.misc_field = json.dumps(misc_field)
        return guest
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None

def delete_guest(id_list=None):
    try:
        for id in id_list:
            guest = get_first_guest(id)
            db.session.delete(guest)
        db.session.commit()
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def update_timeslot(guest, timeslot):
    try:
        guest.timeslot = timeslot
        db.session.commit()
        return guest
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_first_not_sent_invite():
    try:
        guest = Guest.query.filter(Guest.enabled, not_(Guest.invite_email_sent)).first()
        return guest
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_first_not_sent_ack():
    try:
        guest = Guest.query.filter(Guest.enabled, not_(Guest.ack_email_sent)).first()
        return guest
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def subscribe_ack_email_sent(cb, opaque):
    return Guest.subscribe_ack_email_sent(cb, opaque)


def subscribe_nbr_ack_email_sent(cb, opaque):
    return Guest.subscribe_nbr_ack_sent(cb, opaque)


def subscribe_invite_email_sent(cb, opaque):
    return Guest.subscribe_invite_email_sent(cb, opaque)


def subscribe_nbr_invite_email_sent(cb, opaque):
    return Guest.subscribe_nbr_invite_sent(cb, opaque)


def subscribe_email_send_retry(cb, opaque):
    return Guest.subscribe_email_send_retry(cb, opaque)


def subscribe_enabled(cb, opaque):
    return Guest.subscribe_enabled(cb, opaque)


def pre_filter():
    return db.session.query(Guest)


def filter_data(query, filter):
    if 'timeslot' in filter:
        select = filter['timeslot']
        if 'yes' == select:
            query = query.filter(Guest.timeslot != None)
        elif 'no' == select:
            query = query.filter(Guest.timeslot == None)
    return query


def search_data(search_string):
    search_constraints = []
    search_constraints.append(Guest.full_name.like(search_string))
    search_constraints.append(Guest.child_name.like(search_string))
    search_constraints.append(Guest.email.like(search_string))
    search_constraints.append(Guest.phone.like(search_string))
    search_constraints.append(Guest.misc_field.like(search_string))
    return search_constraints


def format_data(db_list):
    out = []
    for i in db_list:
        em = i.flat()
        em.update({
            'row_action': f"{i.id}",
            'id': i.id,
            'DT_RowId': i.id
        })
        out.append(em)
    return out


