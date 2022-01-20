import json
from app.data import settings as msettings
from app import flask_app

def prepare_enter():
    if msettings.get_configuration_setting('enable-enter'):
        ret = {'template': json.loads(msettings.get_configuration_setting('enter-template'))}
        return EnterResult(EnterResult.Result.E_OK, ret)
    return EnterResult(EnterResult.Result.E_COULD_NOT_ENTER, None)


class EnterResult:
    def __init__(self, result, ret={}):
        self.result = result
        self.ret = ret

    class Result:
        E_OK = 'ok'
        E_NOK = 'nok'
        E_COULD_NOT_ENTER = 'could-not-enter'
    result = Result.E_OK
    ret = {}


def end_user_wants_to_enter(code=None):
    is_opened = msettings.get_configuration_setting('enable-enter')
    if is_opened or code == flask_app.config['CODE_ENTER']:
        ret = {
            'template': json.loads(msettings.get_configuration_setting('enter-template')),
            'tabpages': json.loads(msettings.get_configuration_setting('enter-content-json'))
        }
        return EnterResult(EnterResult.Result.E_OK, ret)
    return EnterResult(EnterResult.Result.E_COULD_NOT_ENTER, None)

