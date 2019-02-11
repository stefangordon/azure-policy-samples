import logging


class PolicyLogger(object):
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(__name__)

    def exception_handler(self, exception):
        self.logger.warning(exception)
