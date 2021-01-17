from flask import redirect, render_template, request, url_for, jsonify, session, copy_current_request_context, request
from flask_login import login_required, current_user
from . import end_user
from app import log, socketio, admin_required
from flask_socketio import emit, join_room, leave_room, close_room, rooms, disconnect
from app.application import end_user as mend_user, info_items as minfo_items, floor as mfloor, visit as mvisit, \
    reservation as mreservation, settings as msettings, email as memail
import json, re
from app.data import reservation as dmreservation
from app.data.models import SchoolReservation
from app.presentation.view import base_multiple_items
from app.presentation.view import update_available_periods, false, true, null, prepare_registration_form

@end_user.route('/register', methods=['POST', 'GET'])
def register():
    try:
        current_url = request.url
        current_url = re.sub(f'{request.url_rule.rule}.*', '', current_url)
        memail.set_base_url(current_url)
        code = request.args['code'] if 'code' in request.args else None
        config_data = prepare_registration_form(code)
        return render_template('end_user/register.html', config_data=config_data,
                               registration_endpoint = 'end_user.register_save')
    except Exception as e:
        log.error(f'could not register {request.args}: {e}')
        return render_template('end_user/messages.html', type='unknown-error', message=e)


@end_user.route('/register_save/<string:form_data>', methods=['POST', 'GET'])
def register_save(form_data):
    try:
        data = json.loads(form_data)
        if data['cancel-reservation']:
            try:
                mreservation.delete_registration(data['reservation-code'])
                return render_template('end_user/messages.html', type='cancel-ok')
            except Exception as e:
                return render_template('end_user/messages.html', type='could-not-cancel', message=e)
        else:
            try:
                ret = mreservation.add_or_update_registration(data)
                if ret.result == ret.Result.E_NO_BOXES_SELECTED:
                    return render_template('end_user/messages.html', type='no-boxes-selected')
                if ret.result == ret.Result.E_OK:
                    info = {'school': ret.reservation['name-school'], 'period': ret.reservation['period'], 'nbr_boxes': ret.reservation['number-boxes']}
                    return render_template('end_user/messages.html', type='register-ok', info=info)
                if ret.result == ret.Result.E_NOT_ENOUGH_BOXES:
                    return render_template('end_user/messages.html', type='not-enough-boxes')
            except Exception as e:
                return render_template('end_user/messages.html', type='could-not-register', message=e)
            return render_template('end_user/messages.html', type='could-not-register')
    except Exception as e:
        return render_template('end_user/messages.html', type='unknown-error', message=e)


register_formio = \
    {
        "display": "form",
        "components": [
            {
                "html": "<p><i>Beste directie, beste meester/juf</i></p><p><i>Hieronder kan je een reservatie maken voor SUM-in-a-box.</i></p><p><i>Gelieve één tijdslot te kiezen en het aantal boxen te selecteren (1 box is geschikt voor maximum 25 leerlingen).</i></p><p><i>Vul de velden met de contactgegevens in, zodat we de box op het schooladres kunnen leveren en eventueel contact kunnen opnemen. Naar het mailadres zullen we ook een Microsoft Teams-link doorsturen.</i></p><p><i>Velden met een rood sterretje zijn verplicht.</i></p>",
                "label": "header",
                "refreshOnChange": false,
                "key": "header",
                "type": "content",
                "input": false,
                "tableView": false
            },
            {
                "title": "Contactgegevens",
                "theme": "warning",
                "collapsible": false,
                "key": "contact-info",
                "type": "panel",
                "label": "Contactgevevens",
                "input": false,
                "tableView": false,
                "components": [
                    {
                        "label": "Naam school",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "persistent": false,
                        "validate": {
                            "required": true
                        },
                        "key": "name-school",
                        "type": "textfield",
                        "input": true
                    },
                    {
                        "label": "Voornaam en familienaam van leerkracht 1",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "validate": {
                            "required": true
                        },
                        "key": "name-teacher-1",
                        "type": "textfield",
                        "labelWidth": 40,
                        "labelMargin": 3,
                        "input": true
                    },
                    {
                        "label": "Voornaam en familienaam van leerkracht 2",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "persistent": false,
                        "key": "name-teacher-2",
                        "type": "textfield",
                        "labelWidth": 40,
                        "input": true
                    },
                    {
                        "label": "Voornaam en familienaam van leerkracht 3",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "persistent": false,
                        "key": "name-teacher-3",
                        "type": "textfield",
                        "labelWidth": 40,
                        "input": true
                    },
                    {
                        "label": "Telefoonnummer",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "key": "phone",
                        "type": "textfield",
                        "input": true
                    },
                    {
                        "label": "Adres school (straat en nummer)",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "validate": {
                            "required": true
                        },
                        "key": "address",
                        "type": "textfield",
                        "input": true
                    },
                    {
                        "label": "Postcode",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "validate": {
                            "required": true
                        },
                        "key": "postal-code",
                        "type": "textfield",
                        "input": true
                    },
                    {
                        "label": "Gemeente",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "validate": {
                            "required": true
                        },
                        "key": "city",
                        "type": "textfield",
                        "input": true
                    },
                    {
                        "label": "Totaal aantal leerlingen",
                        "labelPosition": "left-left",
                        "mask": false,
                        "spellcheck": true,
                        "tableView": false,
                        "delimiter": false,
                        "requireDecimal": false,
                        "inputFormat": "plain",
                        "validate": {
                            "required": true
                        },
                        "key": "number-students",
                        "type": "number",
                        "input": true
                    }
                ]
            },
            {
                "title": "Kies één datum en selecteer het aantal boxen",
                "theme": "warning",
                "collapsible": false,
                "key": "select-period-boxes",
                "type": "panel",
                "label": "Kies één datum en het aantal boxen (rechts)",
                "input": false,
                "tableView": false,
                "components": [
                    {
                        "label": "Datum-1",
                        "labelPosition": "left-left",
                        "widget": "choicesjs",
                        "tableView": true,
                        "defaultValue": "0",
                        "data": {
                            "values": [
                                {
                                    "label": "0",
                                    "value": "0"
                                },
                                {
                                    "label": "1",
                                    "value": "1"
                                }
                            ]
                        },
                        "dataType": "string",
                        "selectThreshold": 0.3,
                        "persistent": false,
                        "validate": {
                            "onlyAvailableItems": false
                        },
                        "key": "datum1",
                        "attributes": {
                            "class": "test"
                        },
                        "type": "select",
                        "indexeddb": {
                            "filter": {}
                        },
                        "input": true
                    }
                ]
            },
            {
                "title": "Op onderstaand mailadres sturen we een Microsoft Teams-link om digitaal vragen met de klasgroep te kunnen beantwoorden. Selecteer een datum en uur wanneer dit kan plaatsvinden:",
                "theme": "warning",
                "collapsible": false,
                "key": "info-or-questions",
                "type": "panel",
                "label": "Info of vragen?  Laat een e-mailadres achter en selecteer een datum en uur wanneer wij u kunnen contacteren",
                "input": false,
                "tableView": false,
                "components": [
                    {
                        "label": "E-mailadres",
                        "labelPosition": "left-left",
                        "tableView": true,
                        "key": "meeting-email",
                        "type": "email",
                        "input": true
                    },
                    {
                        "label": "Datum en uur in die uitgeleende week",
                        "labelPosition": "left-left",
                        "useLocaleSettings": true,
                        "allowInput": false,
                        "format": "dd/MM/yyyy HH:mm",
                        "tableView": false,
                        "enableMinDateInput": false,
                        "datePicker": {
                            "disableWeekends": false,
                            "disableWeekdays": false
                        },
                        "enableMaxDateInput": false,
                        "timePicker": {
                            "showMeridian": false
                        },
                        "persistent": false,
                        "key": "meeting-date",
                        "type": "datetime",
                        "input": true,
                        "widget": {
                            "type": "calendar",
                            "displayInTimezone": "viewer",
                            "locale": "en",
                            "useLocaleSettings": true,
                            "allowInput": false,
                            "mode": "single",
                            "enableTime": true,
                            "noCalendar": false,
                            "format": "dd/MM/yyyy HH:mm",
                            "hourIncrement": 1,
                            "minuteIncrement": 1,
                            "time_24hr": true,
                            "minDate": null,
                            "disableWeekends": false,
                            "disableWeekdays": false,
                            "maxDate": null
                        },
                        "labelWidth": 40
                    }
                ]
            },
            {
                "label": "Inzenden",
                "showValidations": false,
                "theme": "success",
                "size": "lg",
                "tableView": false,
                "key": "submit",
                "type": "button",
                "input": true
            }
        ]
    }
