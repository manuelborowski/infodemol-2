from . import reservation
from app import admin_required, log, supervisor_required
from flask import redirect, url_for, request, render_template
from flask_login import login_required
from app.presentation.view import base_multiple_items
from app.presentation.layout.utils import flash_plus, button_pressed
from app.data import guest as mguest
from app.application import socketio as msocketio, reservation as mreservation, guest as maguest, settings as msettings
from app.data.models import Guest
from app.application import tables

import json


@reservation.route('/reservation', methods=['POST', 'GET'])
@login_required
@supervisor_required
def show():
    misc_config = json.loads(msettings.get_configuration_setting('import-misc-fields'))
    base_multiple_items.update(table_configuration, misc_config)
    return base_multiple_items.show(table_configuration)


@reservation.route('/reservation/table_ajax', methods=['GET', 'POST'])
@login_required
@supervisor_required
def table_ajax():
    misc_config = json.loads(msettings.get_configuration_setting('import-misc-fields'))
    base_multiple_items.update(table_configuration, misc_config)
    return base_multiple_items.ajax(table_configuration)


@reservation.route('/reservation/table_action', methods=['GET', 'POST'])
@login_required
@supervisor_required
def table_action():
    if button_pressed('edit'):
        return item_edit()
    if button_pressed('add'):
        return item_add()
    if button_pressed('delete'):
        return item_delete()
    if button_pressed('update_reservation'):
        return update_reservation()
    return redirect(url_for('reservation.show'))


@reservation.route('/reservation/item_action/<string:action>', methods=['GET', 'POST'])
@login_required
@supervisor_required
def item_action(action=None):
    try:
        id = int(request.values['item-id'])
    except:
        id = -1
    if button_pressed('save'):
        if action == 'add':
            return item_add(done=True)
        if action == 'edit':
            return item_edit(done=True, id=id)
    if button_pressed('edit'):
        if action == 'view':
            return item_edit(False, id)
    return redirect(url_for('reservation.show'))


def item_delete(done=False, id=-1):
    try:
        chbx_id_list = request.form.getlist('chbx')
        ids = [int(i) for i in chbx_id_list]
        mguest.delete_guest(ids)
    except Exception as e:
        log.error(f'could not delete guest {request.args}: {e}')
    return redirect(url_for('reservation.show'))


def update_reservation(done=False, id=-1):
    try:
        chbx_id_list = request.form.getlist('chbx')
        if chbx_id_list:
            id = int(chbx_id_list[0])  # only the first one can be edited
        guest = mguest.get_first_guest(id=id)
        return redirect(url_for('guest.register', code=guest.code))
    except Exception as e:
        log.error(f'could not edit reservation {request.args}: {e}')
    return redirect(url_for('reservation.show'))


def get_form(extra_fields, default_values={}):
    form = {
        'fields': ['full_name', 'child_name', 'email', 'phone'],
        'config': {
            'full_name': {'label': 'Naam ouder', 'default': ''},
            'child_name': {'label': 'Naam kind', 'default': ''},
            'email': {'label': 'E-mail', 'default': ''},
            'phone': {'label': 'Telefoon', 'default': ''},
        }
    }
    for field in extra_fields:
        form['fields'].append(field['veldnaam'])
        form['config'][field['veldnaam']] = {'label': field['overzicht']['naam'], 'default': ''}
    if default_values:
        for field in form['fields']:
            form['config'][field]['default'] = default_values[field]
    return form


def get_misc_fields(extra_fields, form):
    misc_field = {}
    for field in extra_fields:
        if field['veldnaam'] in form:
            misc_field[field['veldnaam']] = form[field['veldnaam']]
    return misc_field


def item_edit(done=False, id=-1):
    try:
        misc_config = json.loads(msettings.get_configuration_setting('import-misc-fields'))
        common_details = tables.prepare_item_config_for_view(table_configuration, 'edit')
        if done:
            misc_field = get_misc_fields(misc_config, request.form)
            guest = mguest.get_first_guest(id=id)
            guest = mguest.update_guest(guest, full_name=request.form['full_name'], email=request.form['email'],
                                        child_name=request.form['child_name'], phone=request.form['phone'],
                                        misc_field=misc_field)
            return redirect(url_for('reservation.show'))
        else:
            chbx_id_list = request.form.getlist('chbx')
            if chbx_id_list:
                id = int(chbx_id_list[0])  # only the first one can be edited
            if id > -1:
                guest = mguest.get_first_guest(id=id)
                form = get_form(misc_config, guest.flat())
                common_details['item_id'] = id
            else:
                return redirect(url_for('reservation.show'))
            return render_template('reservation/reservation.html', form_details=form, common_details=common_details)
    except Exception as e:
        log.error(f'Could not edit guest {e}')
        flash_plus('Kan gebruiker niet aanpassen', e)
    return redirect(url_for('reservation.show'))


def item_add(done=False):
    try:
        misc_config = json.loads(msettings.get_configuration_setting('import-misc-fields'))
        if done:
            misc_field = get_misc_fields(misc_config, request.form)
            guest = maguest.add_guest(full_name=request.form['full_name'], email=request.form['email'])
            guest = mguest.update_guest(guest, child_name=request.form['child_name'], phone=request.form['phone'],
                                        misc_field=misc_field)
            log.info(f'add: {guest.email}')
            return redirect(url_for('reservation.show'))
        else:
            common_details = tables.prepare_item_config_for_view(table_configuration, 'add')
            form = get_form(misc_config)
            return render_template('reservation/reservation.html', form_details=form,
                                   common_details=common_details)
    except Exception as e:
        log.error(f'Could not add guest {e}')
        flash_plus(f'Kan gebruiker niet toevoegen: {e}')
    return redirect(url_for('reservation.show'))


@reservation.route('/reservation_save/<string:form_data>', methods=['POST', 'GET'])
@login_required
@supervisor_required
def reservation_save(form_data):
    try:
        data = json.loads(form_data)
        if 'cancel-reservation' in data and data['cancel-reservation']:
            try:
                mreservation.delete_reservation(data['reservation-code'])
                flash_plus('Reservatie is verwijderd')
            except Exception as e:
                flash_plus('Kon de reservatie niet verwijderen', e)
        else:
            try:
                ret = mreservation.add_or_update_reservation(data)
                if ret.result == ret.Result.E_OK:
                    flash_plus('Reservatie is aangepast')
                if ret.result == ret.Result.E_TIMESLOT_FULL:
                    flash_plus('Op dit tijdslot zijn er geen plaatsen meer beschikbaar')
            except Exception as e:
                flash_plus('Onbekende fout opgetreden', e)
    except Exception as e:
        flash_plus('Onbekende fout opgetreden', e)
    return redirect(url_for('reservation.show'))


def reservation_update_cb(value, opaque):
    msocketio.broadcast_message({'type': 'celledit-reservation', 'data': {'reload-table': True}})


mreservation.subscribe_reservation_changed(reservation_update_cb, None)


def celledit_event_cb(msg, client_sid=None):
    if msg['data']['column'] == 6:
        mreservation.update_reservation('note', msg['data']['id'], msg['data']['value'])
    if msg['data']['column'] == 7:
        mreservation.update_reservation('invite_email_sent', msg['data']['id'], msg['data']['value'])
    if msg['data']['column'] == 9:
        mreservation.update_reservation('ack_email_sent', msg['data']['id'], msg['data']['value'])
    if msg['data']['column'] == 11:
        mreservation.update_reservation('enabled', msg['data']['id'], msg['data']['value'])
    if msg['data']['column'] == 12:
        mreservation.update_reservation('email_send_retry', msg['data']['id'], msg['data']['value'])
    msocketio.send_to_room({'type': 'celledit-reservation', 'data': {'status': True}}, client_sid)


msocketio.subscribe_on_type('celledit-reservation', celledit_event_cb)


def get_filters():
    return [
        {
            'type': 'select',
            'name': 'timeslot',
            'label': 'Reservatie',
            'choices': [
                ['default', 'Alles'],
                ['yes', 'Gemaakt'],
                ['no', 'Open'],
            ],
            'default': 'default',
        },
    ]


def get_show_info():
    nbr_total, nbr_open, nbr_reserved = mreservation.get_reservation_counters()
    return [
        f'Totaal: {nbr_total}',
        f'Open: {nbr_open}',
        f'Gereserveerd: {nbr_reserved}',
    ]


table_configuration = {
    'view': 'reservation',
    'title': 'Gasten',
    'buttons': ['edit', 'add', 'delete', 'update_reservation'],
    'delete_message': 'Opgelet!!<br>'
                      'Bent u zeker om deze gast(en) verwijderen?<br>'
                      'Eens verwijderd kunnen ze niet meer worden terug gehaald.<br>'
                      'Indien u de reservatie wilt verwijderen, kies dan <b>Wijzig</'
                      'b> en annuleer dan de reservatie.',
    'template': [
        {'name': 'row_action', 'data': 'row_action', 'width': '1%'},
        {'name': 'Tijdslot', 'data': 'timeslot', 'order_by': Guest.timeslot, 'orderable': True, 'width': '10%'},
        {'name': 'Email', 'data': 'email', 'order_by': Guest.email, 'orderable': True, 'width': '12%'},
        {'name': 'Naam', 'data': 'full_name', 'order_by': Guest.full_name, 'orderable': True, 'width': '6%'},
        {'name': 'Kind', 'data': 'child_name', 'order_by': Guest.child_name, 'orderable': True, 'width': '6%'},
        {'name': 'Telefoon', 'data': 'phone', 'order_by': Guest.phone, 'orderable': True, 'width': '6%'},
        {'name': 'Notitie', 'data': 'note', 'order_by': Guest.note, 'orderable': True, 'width': '20%',
         'celledit': 'text'},
        {'name': 'U', 'data': 'invite_email_sent', 'order_by': Guest.invite_email_sent, 'width': '1%',
         'celltoggle': 'standard'},
        {'name': 'U', 'data': 'nbr_invite_sent', 'order_by': Guest.nbr_invite_sent, 'width': '1%'},
        {'name': 'B', 'data': 'ack_email_sent', 'order_by': Guest.ack_email_sent, 'width': '1%',
         'celltoggle': 'standard'},
        {'name': 'B', 'data': 'nbr_ack_sent', 'order_by': Guest.nbr_ack_sent, 'width': '1%'},
        {'name': 'A', 'data': 'enabled', 'order_by': Guest.enabled, 'width': '1%', 'celltoggle': 'standard'},
        {'name': 'R', 'data': 'email_send_retry', 'order_by': Guest.email_send_retry, 'orderable': True,
         'celledit': 'text', 'width': '1%'},
    ],
    'get_filters': get_filters,
    'get_show_info': get_show_info,
    'item': {
        'edit': {'title': 'Wijzig een gast', 'buttons': ['save', 'cancel']},
        # 'view': {'title': 'Bekijk een reservatie', 'buttons': ['edit', 'cancel']},
        'add': {'title': 'Voeg een gast toe', 'buttons': ['save', 'cancel']},
    },
    'href': [],
    'pre_filter': mguest.pre_filter,
    'format_data': mguest.format_data,
    'filter_data': mguest.filter_data,
    'search_data': mguest.search_data,
    'default_order': (1, 'asc'),
    'socketio_endpoint': 'celledit-reservation',
    # 'cell_color': {'supress_cell_content': True, 'color_keys': {'X': 'red', 'O': 'green'}}, #TEST
    # 'suppress_dom': True,

}
