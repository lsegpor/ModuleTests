import threading
import time

# Dictionary to track locks for each EMU
_emu_locks = {}
_emu_owners = {}
_lock = threading.Lock()  # For thread-safe access to the dictionaries

def acquire_emu(emu_id, tab_id, timeout=30):
    global _emu_locks, _emu_owners
    
    # Ensure there's a lock for this EMU
    with _lock:
        if emu_id not in _emu_locks:
            _emu_locks[emu_id] = threading.Lock()
            _emu_owners[emu_id] = None
    
    # If this tab already owns the lock, return True immediately
    with _lock:
        if _emu_owners[emu_id] == tab_id:
            print(f"Tab {tab_id}: Already owns lock for {emu_id}")
            return True
    
    # Try to acquire the lock
    start_time = time.time()
    while True:
        with _lock:
            if _emu_owners[emu_id] is None:
                _emu_locks[emu_id].acquire()
                _emu_owners[emu_id] = tab_id
                print(f"Tab {tab_id}: Acquired lock for {emu_id}")
                return True
                
        # Check for timeout
        if time.time() - start_time > timeout:
            print(f"Tab {tab_id}: Failed to acquire lock for {emu_id} (timeout)")
            return False
            
        print(f"Tab {tab_id}: Waiting for {emu_id} lock, owned by Tab {_emu_owners[emu_id]}")
        time.sleep(0.5)

def release_emu(emu_id, tab_id):
    """
    Release a lock for a specific EMU
    
    Parameters:
    - emu_id: ID of the EMU board (e.g., "EMU_236")
    - tab_id: ID of the tab requesting the release
    
    Returns:
    - True if lock released, False if not owner
    """
    global _emu_locks, _emu_owners
    
    with _lock:
        if emu_id in _emu_locks and _emu_owners[emu_id] == tab_id:
            _emu_locks[emu_id].release()
            _emu_owners[emu_id] = None
            print(f"Tab {tab_id}: Released lock for {emu_id}")
            return True
        else:
            print(f"Tab {tab_id}: Cannot release lock for {emu_id} - not the owner")
            return False
