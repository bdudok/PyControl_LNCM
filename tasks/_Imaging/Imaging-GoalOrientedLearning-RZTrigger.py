#Treadmill with fixed reward zones. Zone entry comes from a position trigger on the encoder, so there is no polling.
from pyControl.utility import *
from devices import *
from pyControl.hardware import Analog_trigger
import gc
'''---------------------------------------------------- CONFIG--------------------------------------------------'''
zones = [50, 150] #list of locations of zones in cm, in increasing order. make it a list even if it's a list of 1
reward_zone_length = 15 #size of zone in cm. Avoid setting it very small so mouse doesn't miss.
reward_lockout_time = 5 #s. how long the mouse can take reward before having to find the next zone. start with 5
reward_lockout_drops = 10 #number of rewards the mouse can take before having to find the next zone. start with 50.
reward_size = 2 #ul. 2 ul is standard drop size.
hidden_reward = True
v.houselight = True
'''------------------------------------------------------END CONFIG------------------------------------------------'''
#calibration
cm = 41.5 #quad/cm
ul = 24 #ms/microliter
belt_len = 225 #cm
never = 2 ** 30 - 1 #a threshold the position can't reach, this disarms a trigger

v.reward_zone_list = [int(x * cm) for x in zones]
v.reward_zone_open = reward_lockout_time*second #reward availability after RZ entry
v.reward_zone_length = int(reward_zone_length * cm)
v.reward_duration = int(reward_size*ul)  # Time reward solenoid is open for. - calibrated to microliters
v.belt_length = int(belt_len * cm)
v.force_lap_reset = int(belt_len * cm * 1.1) #lap reset triggered if not reset tag
v.manual_valve_open = 1*second
v.max_lick_per_zone = reward_lockout_drops
v.verbose = 0
v.is_hidden = hidden_reward
v.pos = 0

#init attributes for use within states:
v.next_reward = 0 #position of the zone the trigger is set to, 0 if none
v.last_zone___ = -1 #last zone visited in this lap
v.lap_counter = 0
v.lick_count___ = 0
v.reward_zone_entry_time___ = 0
v.reward_zone_lapsed___ = False
v.last_lap_end = 0 #position at the end of last lap
v.total_licks = 0
v.sol_toggle___ = 0
v.first_lap = True

board = Breakout_1_2() # Breakout board.

# Instantiate hardware - would normally be in a seperate hardware definition file.

# Thresholds are compared to the encoder's position, which counts up over the session and is not reset in each lap.
# Don't call set_threshold in run_start or in the entry of the initial state: the framework starts them first.
zone_trigger = Analog_trigger(threshold=never, rising_event='reached_target')
lap_limit_trigger = Analog_trigger(threshold=never, rising_event='lap_limit')

# Running wheel must be plugged into port 1 of breakout board.
belt_pos = Rotary_encoder(name='pos', sampling_rate=15, output='position', triggers=[zone_trigger, lap_limit_trigger])

lick_port = Lickometer(board.port_2, debounce=50)

# lap_reset_tag_cp = Digital_input(board.port_3.DIO_A, rising_event='RFID_CP', falling_event=None, debounce=5, pull='down')
# cp has no signal, use TIR pin instead
lap_reset_tag = Digital_input(board.port_3.DIO_B, rising_event='RFID_TIR', falling_event=None, debounce=1000, pull='down')

#led control and power
led_power = Digital_output(pin=board.port_3.POW_B)

solenoid = lick_port.SOL_1 # Reward delivery solenoid.

session_output = Digital_output(pin=board.BNC_1, )
sync_output = Rsync(pin=board.BNC_2, mean_IPI=1000, event_name='rsync') #sync signnal

# States and events.

states = ['trial_start',
          'searching', 'reward_zone_entry', 'reward_zone', 'reward', #RZ behavior
          ]

events = [
    'lick_1', #lick port
    'RFID_TIR', #RFID tag in range
    'reward_timer', #internal timer
    'reached_target', 'lap_limit', #position triggers
    'sol_on', 'sol_off', #for gui controls
    'manual_reward', 'manual_open', 'manual_toggle',  # for gui controls
    'rsync', #utility
]

initial_state = 'trial_start'


#functions used by states

def lap_reset(force=False):
    '''
    Called by the lap reset tag, or by the lap_limit trigger if the belt went past the tag without detecting it.
    Should work from any state, should not change state
    '''
    get_abs_pos()
    v.lap_counter += 1
    print_variables(['pos', 'lap_counter', ])
    if force:
        v.last_lap_end += v.belt_length #where the tag should have been, so zones stay aligned
    else:
        v.last_lap_end = belt_pos.position
    v.first_lap = False
    v.last_zone___ = -1
    lap_limit_trigger.set_threshold(v.last_lap_end + v.force_lap_reset)
    set_reward()

def get_abs_pos():
    '''
    Update the position within the lap.
    assumes that the rotary position counter never overflows
    '''
    v.pos = belt_pos.position - v.last_lap_end

def close_reward_zone():
    v.reward_zone_lapsed___ = True
    set_timer('reward_timer', 10)

def set_reward():
    '''
    Set the trigger to the next zone of this lap, or disarm it if there are none left.
    There is no reward until the first lap reset, because the position on the belt is not known before that.
    '''
    v.next_reward = 0
    threshold = never
    if not v.first_lap:
        get_abs_pos()
        for rz in v.reward_zone_list:
            if rz > v.pos and rz > v.last_zone___:
                v.next_reward = rz
                threshold = v.last_lap_end + rz
                if v.verbose:
                    print_variables(['next_reward', ])
                break
    zone_trigger.set_threshold(threshold)

def leave_reward_zone():
    disarm_timer('reward_timer')
    goto_state('searching')

def run_start():
    belt_pos.record() # Start streaming wheel velocity to computer.
    session_output.pulse(10, duty_cycle=50, n_pulses=1) #start microscope
    if v.houselight:
        led_power.on()

def run_end():
    session_output.pulse(10, duty_cycle=50, n_pulses=1)  # stop microscope
    led_power.off()
    print_variables(['lap_counter', 'total_licks'])

# State behaviour functions.
def trial_start(event):
    if event == 'entry':
        timed_goto_state('searching', 1*second)

def all_states(event):
    if event == 'RFID_TIR': #called by the lap reset sensor
        lap_reset()
    elif event == 'lap_limit':
        lap_reset(force=True)
    elif event == 'sol_on':
        solenoid.on()
    elif event == 'sol_off':
        solenoid.off()
    elif event == 'manual_reward':
        set_timer('sol_off', 1 + v.reward_duration)
        publish_event('sol_on')
    elif event == 'manual_open':
        set_timer('sol_off', 1 + v.manual_valve_open)
        publish_event('sol_on')
    elif event == 'manual_toggle':
        if not v.sol_toggle___:
            publish_event('sol_on')
        else:
            publish_event('sol_off')
            v.sol_toggle___ = False

def searching(event):
    '''
    this is the default state. wait for the position trigger of the next RZ.
    '''
    if event == 'entry':
        gc.collect()  # this is a good time to garbage collect as nothing urgent can happen
        set_reward()
    elif event == 'reached_target':
        get_abs_pos()
        if v.verbose > 1:
            print_variables(['pos', 'next_reward'])
        # the check is for an event that was queued just before a lap reset moved the zone
        if (v.next_reward > 0) and (v.next_reward <= v.pos < v.next_reward + v.reward_zone_length):
            goto_state('reward_zone_entry')
        else:
            set_reward()

def reward_zone_entry(event):
    '''Reset lick count for current rz, starts timeout, and waits for licks'''
    if event == 'entry':
        v.last_zone___ = v.next_reward
        v.lick_count___ = 0
        v.reward_zone_entry_time___ = get_current_time()
        v.reward_zone_lapsed___ = False
        if not v.is_hidden:
            set_timer('lick_1', 10*ms)
        set_timer('reward_timer', v.reward_zone_open)
    elif event == 'lick_1':
        goto_state('reward')
    elif event == 'reward_timer':
        goto_state('searching')

def reward_zone(event):
    '''
    Lick returns to this state. wait for licks and terminate if RZ is over.
    '''
    if event == 'entry':
        if v.lick_count___ >= v.max_lick_per_zone:
            close_reward_zone()
        elif get_current_time() > v.reward_zone_entry_time___ + v.reward_zone_open:
            close_reward_zone()
    elif event == 'lick_1':
        get_abs_pos()
        if v.pos > (v.last_zone___ + v.reward_zone_length): #abort if zone size passed
            print('rz length reached')
            leave_reward_zone()
        elif get_current_time() > v.reward_zone_entry_time___ + v.reward_zone_open:
            leave_reward_zone()
        elif not v.reward_zone_lapsed___:
            goto_state('reward')
        else:
            leave_reward_zone()
    elif event == 'reward_timer':
        goto_state('searching')


def reward(event):
    '''
    Separate state for opening the reward (so the solenoid can't stay on).
    '''
    if event == 'entry':
        v.lick_count___ += 1
        if v.verbose:
            print_variables(['total_licks', ])
        timed_goto_state('reward_zone', v.reward_duration)
        #we hope that the reward_timer event cannot be missed if it happens during this exit or searching's entry. - it can.
        solenoid.on()
        v.total_licks += 1
    elif event == 'exit':
        solenoid.off()
    else:
        if v.lick_count___ >= v.max_lick_per_zone:
            close_reward_zone()
        elif get_current_time() > v.reward_zone_entry_time___ + v.reward_zone_open:
            close_reward_zone()
