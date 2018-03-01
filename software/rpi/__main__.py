#!/usr/bin/python

import argparse
import logging
import time
import signal
import sys
import json
import serial
import math, random
import click
import os.path
import RPi.GPIO as GPIO
from six.moves import input
from threading import Thread, Event
import threading
from queue import Queue
from . import (audio_helpers, common_settings)
# from google.assistant.embedded.v1alpha1 import embedded_assistant_pb2
# from google.rpc import code_pb2
from google.cloud import pubsub
 
import google.auth.transport.requests
import google.oauth2.credentials
 
from google.assistant.library import Assistant
from google.assistant.library.event import EventType

DEVICE_API_URL = 'https://embeddedassistant.googleapis.com/v1alpha2'

# ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
# END_OF_UTTERANCE = embedded_assistant_pb2.ConverseResponse.END_OF_UTTERANCE
# DIALOG_FOLLOW_ON = embedded_assistant_pb2.ConverseResult.DIALOG_FOLLOW_ON
# CLOSE_MICROPHONE = embedded_assistant_pb2.ConverseResult.CLOSE_MICROPHONE


# customizations
DRINK_SIZE = 12 # size of the cup to fill in ounces
# recipes below assume:
#   bottle 0 = vodka
#   bottle 1 = malibu
#   bottle 2 = tequila
#   bottle 3 = gin
#   bottle 4 = orange
#   bottle 5 = cranberry
#   bottle 6 = pineapple
#   bottle 7 = glass
MENU = {
  'dancing bear': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 1 },
    { 'bottle' : 2, 'proportion': 1 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 1 }
  ],
  'cranberry gin': [
    { 'bottle' : 3, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 3 }
  ],
  'cape cod': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 3 }
  ],
  'screwdriver': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 4, 'proportion': 3 }
  ],
  'paradise': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 3 },
    { 'bottle' : 6, 'proportion': 3 }
  ],
  'virgin in paradise': [
    { 'bottle' : 4, 'proportion': 4 },
    { 'bottle' : 5, 'proportion': 2 },
    { 'bottle' : 6, 'proportion': 4 }
  ],
  'margarita': [
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 2 }
  ]
}


# contstants
PUBSUB_PROJECT_ID = common_settings.PROJECT_ID
SER_DEVICE = '/dev/ttyACM0' # ensure correct file descriptor for connected arduino
PUSH_TO_TALK = False
PUSH_TO_TALK_PIN = 26
PUMP_SPEED = 0.056356667 # 100 ml / min = 0.056356667 oz / sec
NUM_BOTTLES = 8
PRIME_WHICH = None


def get_pour_time(pour_prop, total_prop):
  return (DRINK_SIZE * (pour_prop / total_prop)) / PUMP_SPEED


def make_drink(drink_name, msg_q):

  print('make_drink()')

  # check that drink exists in menu
  if not drink_name in MENU:
    print('drink "' + drink_name + '" not in menu')
    return

  # get drink recipe
  recipe = MENU[drink_name]
  print(drink_name + ' = ' + str(recipe))

  # sort drink ingredients by proportion
  sorted_recipe = sorted(recipe, key=lambda p: p['proportion'], reverse=True)
  # print(sorted_recipe)

  # calculate time to pour most used ingredient
  total_proportion = 0
  for p in sorted_recipe:
    total_proportion += p['proportion']
  drink_time = get_pour_time(sorted_recipe[0]['proportion'], total_proportion)
  print('Drink will take ' + str(math.floor(drink_time)) + 's')

  # for each pour
  for i, pour in enumerate(sorted_recipe):

    # for first ingredient
    if i == 0:

      # start pouring with no delay
      pour_thread = Thread(target=trigger_pour, args=([msg_q, pour['bottle'], math.floor(drink_time)]))
      pour_thread.start()

    # for other ingredients
    else:

      # calculate the latest time they could start
      pour_time = get_pour_time(pour['proportion'], total_proportion)
      latest_time = drink_time - pour_time

      # start each other ingredient at a random time between now and latest time
      delay = random.randint(0, math.floor(latest_time))
      pour_thread = Thread(target=trigger_pour, args=([msg_q, pour['bottle'], math.floor(pour_time), delay]))
      pour_thread.start()


def trigger_pour(msg_q, bottle_num, pour_time, start_delay=0):

  if bottle_num > NUM_BOTTLES:
    print('Bad bottle number')
    return

  print('Pouring bottle ' + str(bottle_num) + ' for ' + str(pour_time) + 's after a ' + str(start_delay) + 's delay')

  time.sleep(start_delay) # start delay
  msg_q.put('b' + str(bottle_num) + 'r!') # start bottle pour
  time.sleep(pour_time) # wait
  msg_q.put('b' + str(bottle_num) + 'l!') # end bottle pour


def signal_handler(signal, frame):
    """ Ctrl+C handler to cleanup """

    if PUSH_TO_TALK:
      GPIO.cleanup()

    for t in threading.enumerate():
      # print(t.name)
      if t.name != 'MainThread':
        t.shutdown_flag.set()

    print('Goodbye!')
    sys.exit(1)


def poll(assistant_thread):
  """ Polling function for push-to-talk button """

  is_active = False
  # vals = [1, 1, 1]
  vals = [0, 0, 0]

  while True:

    # get input value
    val = GPIO.input(PUSH_TO_TALK_PIN)
    # print("input = ", in_val)

    # shift values
    vals[2] = vals[1]
    vals[1] = vals[0]
    vals[0] = val

    # check for button press and hold
    # if (is_active == False) and (vals[2] == 1) and (vals[1] == 0) and (vals[0] == 0):
    if (is_active == False) and (vals[2] == 0) and (vals[1] == 1) and (vals[0] == 1):
      is_active = True
      assistant_thread.button_flag.set()
      print('Start talking')

    # check for button release
    # if (is_active == True) and (vals[2] == 0) and (vals[1] == 1) and (vals[0] == 1):
    if (is_active == True) and (vals[2] == 1) and (vals[1] == 0) and (vals[0] == 0):
      is_active = False

    # sleep
    time.sleep(0.1)


def setup_creds():
  # Load credentials.
  try:
    credentials = common_settings.CREDENTIALS_FILE_PATH
    # credentials = os.path.join(
    #     click.get_app_dir(common_settings.ASSISTANT_APP_NAME),
    #     common_settings.ASSISTANT_CREDENTIALS_FILENAME
    # )
    with open(credentials, 'r') as f:
      global creds
      creds = google.oauth2.credentials.Credentials(token=None, **json.load(f))
    
  except Exception as e:
    logging.error('Error loading credentials: %s', e)
    return -1
  return 0


class AssistantThread(object):
  """ New Assistant Thread """

  def __init__(self, msg_queue):
    self.shutdown_flag = Event()
    self.button_flag = Event()
    self.msg_queue = msg_queue

  def run(self):


    # Create gRPC channel
    # grpc_channel = auth_helpers.create_grpc_channel(ASSISTANT_API_ENDPOINT, creds)
    # logging.info('Connecting to %s', ASSISTANT_API_ENDPOINT)

    # Create Google Assistant API client.
    with Assistant(creds, common_settings.DEVICE_MODEL_ID) as assist:
      self.assistant = assist
      print('device_model_id:', common_settings.DEVICE_MODEL_ID + '\n' + 'device_id:', self.assistant.device_id + '\n')
      
      self.register_device(common_settings.PROJECT_ID, creds, common_settings.DEVICE_MODEL_ID, self.assistant.device_id)

      self.msg_queue.put('xr!')
      events = self.assistant.start()

      for event in events:
        self.process_event(event, self.assistant.device_id)

  def register_device(self, project_id, credentials, device_model_id, device_id):
    """Register the device if needed.
 
    Registers a new assistant device if an instance with the given id
    does not already exists for this model.
 
    Args:
       project_id(str): The project ID used to register device instance.
       credentials(google.oauth2.credentials.Credentials): The Google
                OAuth2 credentials of the user to associate the device
                instance with.
       device_model_id: The registered device model ID.
       device_id: The device ID of the new instance.
    """
    base_url = '/'.join([DEVICE_API_URL, 'projects', project_id, 'devices'])
    device_url = '/'.join([base_url, device_id])
    session = google.auth.transport.requests.AuthorizedSession(credentials)
    r = session.get(device_url)
    print(device_url, r.status_code)
    if r.status_code == 404:
      print('Registering....', end='', flush=True)
      r = session.post(base_url, data=json.dumps({
        'id': device_id,
        'model_id': device_model_id,
        'client_type': 'SDK_LIBRARY'
      }))
    if r.status_code != 200:
      raise Exception('failed to register device: ' + r.text)
    print('\rDevice registered.')

      

  def process_device_actions(self, event, device_id):
    if 'inputs' in event.args:
      for i in event.args['inputs']:
        if i['intent'] == 'action.devices.EXECUTE':
          for c in i['payload']['commands']:
            for device in c['devices']:
              if device['id'] == device_id:
                if 'execution' in c:
                  for e in c['execution']:
                    if e['params']:
                      yield e['command'], e['params']
                    else:
                      yield e['command'], None
 
  def process_event_lights(self, event):

    lights_on_actions = [EventType.ON_CONVERSATION_TURN_STARTED]
    lights_off_actions = [EventType.ON_CONVERSATION_TURN_FINISHED, EventType.ON_NO_RESPONSE, EventType.ON_CONVERSATION_TURN_TIMEOUT, EventType.ON_ALERT_FINISHED, EventType.ON_END_OF_UTTERANCE, EventType.ON_RECOGNIZING_SPEECH_FINISHED, EventType.ON_RESPONDING_FINISHED, EventType.ON_START_FINISHED]
    lights_pulse_slow_actions = [EventType.ON_RESPONDING_STARTED]
    lights_pulse_fast_actions = [EventType.ON_ALERT_STARTED, EventType.ON_ASSISTANT_ERROR]
    lights_spinning_actions = [EventType.ON_DEVICE_ACTION]

    if event.type in lights_on_actions:
      self.msg_queue.put('xh!')
      print("Turning lights on")
  
    if event.type in lights_off_actions:
      self.msg_queue.put('xo!')
      print("Turning lights off")
    
    if event.type in lights_pulse_fast_actions:
      self.msg_queue.put('xr!')
      print("Pulsing Lights Fast")
    
    if event.type in lights_pulse_slow_actions:
      self.msg_queue.put('xl!')
      print("Pulsing Lights Slow")

    if event.type in lights_spinning_actions:
      self.msg_queue.put('xt!')
      print("Lights Spinning")


 
  def process_event(self, event, device_id):
      """Pretty prints events.
   
      Prints all events that occur with two spaces between each new
      conversation and a single space between turns of a conversation.
   
      Args:
          event(event.Event): The current event to process.
      """

      print(event)

      self.process_event_lights(event)

   
      if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and event.args and not event.args['with_follow_on_turn']):
        print('')
      if event.type == EventType.ON_DEVICE_ACTION:
        for command, params in self.process_device_actions(event, device_id):
          print('Do command', command, 'with params', str(params))



class SubscriptionThread(Thread):

  def __init__(self, msg_queue):

    Thread.__init__(self)

    self.shutdown_flag = Event()
    self.msg_queue = msg_queue;

    # Create a new pull subscription on the given topic
#     subscriber = pubsub.SubscriberClient()
# >>> topic = 'projects/{project_id}/topics/{topic}'.format(
# ...     project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
# ...     topic='MY_TOPIC_NAME',  # Set this to something appropriate.
# ... )
# >>> subscription_name = 'projects/{project_id}/subscriptions/{sub}'.format(
# ...     project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
# ...     sub='MY_SUBSCRIPTION_NAME',  # Set this to something appropriate.
# ... )
# >>> subscription = subscriber.create_subscription(subscription_name, topic)
    pubsub_client = pubsub.SubscriberClient(credentials=creds)
    topic_name = 'MocktailsMixerMessages'
    subscription_name = 'PythonMocktailsMixerSub'

    topic = 'projects/{project_id}/topics/{topic}'.format(
      project_id=common_settings.PROJECT_ID,
      topic=topic_name
    )
    subscription_name = 'projects/{project_id}/subscriptions/{sub}'.format(
      project_id=common_settings.PROJECT_ID,
      sub=subscription_name
    )

    try:
      self.subscription = pubsub_client.create_subscription(subscription_name, topic)
    except:
      self.subscription = pubsub_client.subscribe(subscription_name)
    
    # pubsub_client = pubsub.Client(project=PUBSUB_PROJECT_ID, credentials=creds)
    # topic_name = 'MocktailsMixerMessages'
    # topic = pubsub_client.topic(topic_name)

    # self.subscription = topic.subscription(subscription_name)

  
  def run(self):
    """ Poll for new messages from the pull subscription """

    def callback(message):
      if not message is None:
        # convert bytes to string and slice string
        # http://stackoverflow.com/questions/663171/is-there-a-way-to-substring-a-string-in-python
        json_string = str(message.data)[3:-2]
        json_string = json_string.replace('\\\\', '')
        logging.info(json_string)

        # create dict from json string
        try:
          json_obj = json.loads(json_string)
        except Exception as e:
          logging.error('JSON Error: %s', e)

        # get intent from json
        intent = json_obj['intent']
        print('pub/sub: ' + intent)

        # perform action based on intent
        if intent == 'prime_pump_start':
          PRIME_WHICH = json_obj['which_pump']
          print('Start priming pump ' + PRIME_WHICH)
          self.msg_queue.put('b' + PRIME_WHICH + 'r!') # turn on relay

        elif intent == 'prime_pump_end':
          if PRIME_WHICH != None:
            print('Stop priming pump ' + PRIME_WHICH)
            self.msg_queue.put('b' + PRIME_WHICH + 'l!') # turn off relay
            PRIME_WHICH = None

        elif intent == 'make_drink':
          make_drink(json_obj['drink'], self.msg_queue)

        message.ack()
      
      else:
        pass

      time.sleep(0.25)

    try:
      self.subscription.open(callback)
      logging.info('Subscription created')
    except Exception as e:
      print(e)
      logging.info('Subscription already exists')




class SerialThread(Thread):

  def __init__(self, msg_queue):
    Thread.__init__(self)
    self.shutdown_flag = Event()
    self.msg_queue = msg_queue;
    self.serial = serial.Serial(SER_DEVICE, 9600)

  def run(self):

    while not self.shutdown_flag.is_set():

      if not self.msg_queue.empty():
        cmd = self.msg_queue.get()
        self.serial.write(str.encode(cmd))
        print('Serial sending ' + cmd)


if __name__ == '__main__':

  # set log level (DEBUG, INFO, ERROR)
  logging.basicConfig(level=logging.INFO)

  # handle SIGINT gracefully
  signal.signal(signal.SIGINT, signal_handler)

  # setup creds
  ret_val = setup_creds()
  if ret_val == 0:

    # create message queue for communicating between threads
    msg_q = Queue()

    # start serial thread
    serial_thread = SerialThread(msg_q)
    serial_thread.start()

    # create pub/sub subscription and start thread
    sub_thread = SubscriptionThread(msg_q)
    sub_thread.start()

    # start assistant thread
    assistant_thread = AssistantThread(msg_q)

    assistant_thread.run()

    """
    # # wait for main to finish until assistant thread is done
    # assistant_thread.join()

    if PUSH_TO_TALK:

      # setup push to talk and start thread
      GPIO.setmode(GPIO.BOARD)
      GPIO.setup(PUSH_TO_TALK_PIN, GPIO.IN)
      poll_thread = Thread(target=poll, args=([assistant_thread]))
      poll_thread.start()
    """
