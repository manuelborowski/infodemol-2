from app.data.models import TimeslotConfiguration
from app import log, db
import sys, json


def add_timeslot_configuration_bulk(date, length, nbr_of_timeslots, items_per_timeslot, misc_field):
    try:
        timeslot_configuration = TimeslotConfiguration(date=date, length=length, nbr_of_timeslots=nbr_of_timeslots,
                                                       items_per_timeslot=items_per_timeslot,
                                                       misc_field=json.dumps(misc_field))
        db.session.add(timeslot_configuration)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def add_timeslot_configuration_commit():
    try:
        db.session.commit()
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def add_timeslot_configuration(date, length, nbr_of_timeslots, items_per_timeslot, misc_field=None):
    try:
        add_timeslot_configuration_bulk(date=date, length=length, nbr_of_timeslots=nbr_of_timeslots,
                                        items_per_timeslot=items_per_timeslot, misc_field=misc_field)
        add_timeslot_configuration_commit()
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def get_timeslot_configurations(date=None, length=None, nbr_of_timeslots=None, items_per_timeslot=None, first=False):
    try:
        tcs = TimeslotConfiguration.query
        if date:
          tcs = tcs.filter(TimeslotConfiguration.date == date)
        if length:
          tcs = tcs.filter(TimeslotConfiguration.length == length )
        if nbr_of_timeslots:
          tcs = tcs.filter(TimeslotConfiguration.nbr_of_timeslots == nbr_of_timeslots)
        if items_per_timeslot:
          tcs = tcs.filter(TimeslotConfiguration.items_per_timeslot == items_per_timeslot)
        tcs = tcs.order_by(TimeslotConfiguration.date)
        if first:
            tc = tcs.first()
            return tc
        tcs = tcs.all()
        return tcs
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_first_timeslot_configuration(date=None, length=None, nbr_of_timeslots=None, items_per_timeslot=None):
    try:
        tc = get_timeslot_configurations(date=date, length=length, nbr_of_timeslots=nbr_of_timeslots, items_per_timeslot=items_per_timeslot, first=True)
        return tc
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def delete_timeslot_configuration(tc=None, tc_list=None):
    try:
        if tc:
            tc_list = [tc]
        for tc in tc_list:
            db.session.delete(tc)
        db.session.commit()
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def pre_filter():
    return db.session.query(TimeslotConfiguration)


def search_data(search_string):
    search_constraints = []
    # search_constraints.append(SchoolReservation.name_school.like(search_string))
    # search_constraints.append(SchoolReservation.name_teacher_1.like(search_string))
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


