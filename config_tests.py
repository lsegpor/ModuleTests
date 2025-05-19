import sys
import logging
import uhal
sys.path.append('../../autogen/agwb/python/')
# sys.path.append('../../agwb/')
import agwb
from smx_tester import *
import msts_defs as smc

class ConfigTests:

    log = logging.getLogger()

    def general_sync(emu, active_downlinks = [1,2]):
        # Function to establish connection with EMU boards, finding FEBs and synchronizing ASICs 
        manager = uhal.ConnectionManager("file://devices.xml")
        # Open xml file with list of EMU devices
    
        # Arrays to organize setup elements (FEBs)
        setup_elements = []
        emu_elements = []

        link_scan = True
        device_scan = True
        link_sync = True

        ipbus_interface = IPbusInterface(manager, emu)
        agwb_top = agwb.top(ipbus_interface, 0)
        smx_tester = SmxTester(agwb_top, CLK_160)
        setup_elements_tmp = smx_tester.scan_setup()
        log.info("setup_elements_tmp: %d", len(setup_elements_tmp))
        setup_elements.extend(setup_elements_tmp)
        emu_elements.extend( [emu for i in range(len(setup_elements_tmp))])

        #setup_elements = [setup_elements[0]]
        #active_downlinks = active_downlinks
        #active_downlinks = [0,3]
        #active_downlinks = [1,2]
        #active_downlinks = [3]

        remove_list_01 = []
        remove_list_23 = []
        
        for se in list(setup_elements):
            log.info(f"SE:\t{se.downlink}\t\t{se.uplinks}  ({len(se.uplinks)})")
            if not se.downlink in active_downlinks:
                setup_elements.remove(se)
                log.info(f"Remove setup element for downlink no. {se.downlink} with uplinks {se.uplinks}")

        for se in setup_elements:
            log.info(f"Cleaned - SE:\t{se.downlink}\t\t{se.uplinks}  ({len(se.uplinks)})")

            for uplink in se.uplinks:
                if se.downlink == 0 or se.downlink == 1:
                    if uplink > 15:
                        remove_list_01.append(uplink)
                        log.info("Uplink appended to remove list: {}".format(uplink))
                else:
                    if uplink < 16:
                        remove_list_23.append(uplink)
                        log.info("Uplink appended to remove list: {}".format(uplink))
            if se.downlink == 0 or se.downlink == 1:
                se.uplinks = [i for i in se.uplinks if i not in remove_list_01]
            else:
                se.uplinks = [i for i in se.uplinks if i not in remove_list_23]
            log.info(f"Final List UPLINKS SE:\t{se.downlink}\t\t{se.uplinks}  ({len(se.uplinks)})")
            
        # Temporary workaround becase there are no independent elink clocks.
        # setup_elements = [setup_elements[0]]
        # smx_tester.elinks.disable_downlink_clock(4)

        if link_scan:
            for se in setup_elements:
                se.characterize_clock_phase()
                log.info(f"post char clk phase\n {se}")
                se.initialize_clock_phase()
                log.info(f"post set\n {se}")

            for se in setup_elements:
                se.characterize_data_phases()
                log.info(f"post char data phase\n {se}")
                se.initialize_data_phases()
                log.info(f"post set\n {se}")

        if device_scan:        
            for se in setup_elements:
                se.scan_smx_asics_map()
                log.info(f"post scan map|n {se}")

        if link_sync:        
            for se in setup_elements:
                se.synchronize_elink()

            for se in setup_elements:
                se.write_smx_elink_masks()

        smxes = []
        for se, emu in zip(setup_elements, emu_elements):
            smxes_tmp = smxes_from_setup_element(se)
            log.info("smxes_tmp: %d", len(smxes_tmp))
            for smx in smxes_tmp:
                smx.rob = int(emu[4:])
            smxes.extend(smxes_tmp)
    
        print(emu_elements) 
        log.info("Number of setup elements: %d", len(setup_elements))
        log.info("Number of smx: %d", len(smxes))
        log.info("")
        return smxes

    def scanning_asics(smx_l):
        # Function to find the number of ASICs per dwnlink or devices    
        n_asics = 0
        p_asics = 0
        for smx in smx_l:
            log.info("Asic (emu %d   downlink %d   hw_addr %d): ", smx.rob, smx.downlink, smx.address)
            smx.func_to_reg(smc.R_ACT)
            smx.write_reg_all()
            smx.read_reg_all(compFlag = False)
            if (smx.downlink == 1 or smx.downlink == 3):
                n_asics+=1
            else:
                p_asics+=1       
        return (n_asics, p_asics)
