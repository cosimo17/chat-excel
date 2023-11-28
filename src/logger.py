import logging


class Logger(object):
    def __init__(self, log_filename=None):
        if log_filename is not None:
            logging.basicConfig(filename=log_filename,
                                filemode='a',
                                format='%(asctime)s: %(levelname)s %(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.DEBUG)
        self.logger = logging.getLogger('chat-excel')

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)


logger = Logger("DEBUG.log")
