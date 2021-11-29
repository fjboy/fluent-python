from fp_lib.common import exceptions as base_exc


class InterfaceDetachTimeout(base_exc.BaseException):
    _msg = 'vm {vm} interface detach timeout with {timeout} seconds'


class VolumeAttachTimeout(base_exc.BaseException):
    _msg = 'volume {volume} attach timeout with {timeout} seconds'


class VolumeAttachtFailed(base_exc.BaseException):
    _msg = 'volume {volume} attach  failed'


class VolumeDetachTimeout(base_exc.BaseException):
    _msg = 'volume {volume} detach failed'


class VolumeCreateTimeout(base_exc.BaseException):
    _msg = 'volume {volume} create timeout({timeout}s)'


class VolumeCreateFailed(base_exc.BaseException):
    _msg = 'volume {volume} create failed'


class VmCreatedFailed(base_exc.BaseException):
    _msg = 'vm {vm} create failed'


class StopFailed(base_exc.BaseException):
    _msg = 'Stop {vm} failed, reason: {reason}'


class StartFailed(base_exc.BaseException):
    _msg = 'Start {vm} failed, reason: {reason}'


class SuspendFailed(base_exc.BaseException):
    _msg = 'suspend {vm} failed, reason: {reason}'


class ResumeFailed(base_exc.BaseException):
    _msg = 'resume {vm} failed, reason: {reason}'


class RebootFailed(base_exc.BaseException):
    _msg = 'Reboot {vm} failed, reason: {reason}'


class WaitVMStatusTimeout(base_exc.BaseException):
    _msg = 'wait {vm} status timeout, expect: {expect}, actual: {actual}'


class VMIsError(base_exc.BaseException):
    _msg = 'vm {vm} status is error'


class LoopTimeout(base_exc.BaseException):
    _msg = 'loop timeout({timeout})'


class VolumeDetachFailed(base_exc.BaseException):
    _msg = 'volume {volume} detach failed'
