
STOP = 'stop'
START = 'start'
REBOOT = 'reboot'
ATTACH_INTERFACE = 'attach-interface'
ATTACH_VOLUME = 'attach-volume'
SUSPEND = 'suspend'
RESUME = 'resume'
PAUSE = 'pause'
UNPAUSE = 'unpause'
RESIZE = 'resize'
MIGRATE = 'migrate'
LIVE_MIGRATE = 'live-migrate'


ACTIONS_ALL = [
    STOP, START, REBOOT, RESIZE, SUSPEND, RESUME, PAUSE, UNPAUSE,
    MIGRATE, LIVE_MIGRATE,
    ATTACH_INTERFACE, ATTACH_VOLUME
]
