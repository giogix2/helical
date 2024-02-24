import logging
from constants.enums import LoggingType, LoggingLevel
import os

class Logger(): 
    def __init__(self, log_type: LoggingType, level: LoggingLevel):
        
        self.log_filename = "debug.log"
        format = '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s'
        datetime = '%H:%M:%S'
        level = level.value
        
        if log_type == LoggingType.FILE_AND_CONSOLE:
            self._remove_log()
            logging.basicConfig(
                format=format,
                datefmt=datetime,
                level=level,
                handlers=[
                    logging.FileHandler(self.log_filename),
                    logging.StreamHandler(),
                ],
            )
            
        elif log_type == LoggingType.CONSOLE:
            logging.basicConfig(
                format=format,
                datefmt=datetime,
                level=level,
                handlers=[
                    logging.StreamHandler(),
                ],
            )            
        
        elif log_type == LoggingType.FILE:
            self._remove_log()
            logging.basicConfig(
                format=format,
                datefmt=datetime,
                level=level,
                handlers=[
                    logging.FileHandler(self.log_filename),
                ],
            )
            
        else:
            logging.disable = True
    
    def _remove_log(self):
        try:
            os.remove(self.log_filename)
        except OSError:
            pass
