
__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__version__    = "3"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''  '''

from loguru import logger

#==========================================================================
def get_feb_type( name ) -> tuple:
    
    try:
        sn_number = int( name )
    except:
        logger.error('FEB SN is not a number')
        return

    if not sn_number in range(999, 7000):
        logger.error('FEB SN is not in range')
        return

    # ----- G S I -----
    # GSI 8.2 A
    elif sn_number in range(1000, 2000):
        return 'A', '8-2', 'GSI'

    # GSI 8.2 B
    elif sn_number in range(2000, 3000):
        return 'B', '8-2', 'GSI'

    # GSI 8.5 A
    elif sn_number in range(5000, 5500):
        return 'A', '8-5', 'GSI'
        
    # GSI 8.5 B
    elif sn_number in range(6000, 6500):
        return 'B', '8-5', 'GSI'

    # ----- K I T -----
    # KIT 8.2 A
    elif sn_number in range(3000, 4000):
        return 'A', '8-2', 'KIT'
    
    # KIT 8.2 B
    elif sn_number in range(4000, 5000):
        return 'B', '8-2', 'KIT'

    # KIT 8.5 A
    elif sn_number in range(5500, 6000):
        return 'A', '8-5', 'KIT'

    # KIT 8.5 B
    elif sn_number in range(6500, 7000):
        return 'B', '8-5', 'KIT'

