from flask import render_template, request
from . import guest
from app import log, socketio
from app.application import email as memail, reservation as mreservation, enter as menter
import json, re, urllib
from app.presentation.view import prepare_registration_form, prepare_enter_form


@guest.route('/register', methods=['POST', 'GET'])
def register():
    try:
        current_url = request.url
        current_url = re.sub(f'{request.url_rule.rule}.*', '', current_url)
        memail.set_base_url(current_url)
        code = request.args['code'] if 'code' in request.args else None
        ret = prepare_registration_form(code)
        if ret.result == ret.Result.E_COULD_NOT_REGISTER:
            return render_template('guest/messages.html', type='could-not-register')
        return render_template('guest/register.html', config_data=ret.ret,
                               registration_endpoint='guest.register_save')
    except Exception as e:
        log.error(f'could not register {request.args}: {e}')
        return render_template('guest/messages.html', type='unknown-error', message=e)


@guest.route('/register_save/<string:form_data>', methods=['POST', 'GET'])
def register_save(form_data):
    try:
        data = json.loads(urllib.parse.unquote(form_data))
        if 'cancel-reservation' in data and data['cancel-reservation']:
            try:
                mreservation.delete_reservation(data['reservation-code'])
                return render_template('guest/messages.html', type='cancel-ok')
            except Exception as e:
                return render_template('guest/messages.html', type='could-not-cancel', message=e)
        else:
            try:
                ret = mreservation.add_or_update_reservation(data)
                if ret.result == ret.Result.E_OK:
                    return render_template('guest/messages.html', type='register-ok', info=ret.ret)
                if ret.result == ret.Result.E_TIMESLOT_FULL:
                    return render_template('guest/messages.html', type='timeslot-full', info=ret.ret)
            except Exception as e:
                return render_template('guest/messages.html', type='could-not-register', message=e)
            return render_template('guest/messages.html', type='could-not-register')
    except Exception as e:
        return render_template('guest/messages.html', type='unknown-error', message=e)


@guest.route('/enter', methods=['POST', 'GET'])
def enter():
    try:
        code = request.args['code'] if 'code' in request.args else None
        ret = prepare_enter_form(code)
        if ret.result == ret.Result.E_COULD_NOT_ENTER:
            return render_template('guest/messages.html', type='could-not-enter')
        return render_template('guest/enter.html', config_data=ret.ret)
    except Exception as e:
        log.error(f'could not register {request.args}: {e}')
        return render_template('guest/messages.html', type='unknown-error', message=e)


register_formio = \
    {}
