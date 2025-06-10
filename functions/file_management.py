import time
import sys
import os
import logging
import uhal
sys.path.append('../../autogen/agwb/python/')
from smx_tester import *

class FileManagement:

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s,%(msecs)03d:%(module)s:%(levelname)s:%(message)s",
        datefmt="%H:%M:%S",
    )

    def set_logging_details(module_dir = "/home/cbm/lsegura/emu_ladder/python/module_files"):    
        date  = time.strftime("%y%m%d_%H%M")

        logFileName = os.path.basename(sys.argv[0]).replace('.py', '') + "_" + date + ".log"

        module_dir = os.path.abspath(module_dir)
        os.makedirs(module_dir, exist_ok=True)

        logFilePath = os.path.join(module_dir, logFileName) 

        fh = logging.FileHandler(logFilePath, 'w')
        fh.setLevel(logging.DEBUG)

        fmt = logging.Formatter('[%(levelname)s] %(message)s')
        fh.setFormatter(fmt)

        logging.getLogger().addHandler(fh)

        uhal.setLogLevelTo(uhal.LogLevel.WARNING)