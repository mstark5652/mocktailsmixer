# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common settings for assistant helpers."""

ASSISTANT_APP_NAME = 'googlesamples-assistant' # todo-change and re-run auth
ASSISTANT_OAUTH_SCOPE = (
  'https://www.googleapis.com/auth/assistant-sdk-prototype'
)
PUBSUB_OAUTH_SCOPE = 'https://www.googleapis.com/auth/pubsub'
ASSISTANT_CREDENTIALS_FILENAME = 'assistant_credentials.json'
CREDENTIALS_FILE_PATH = '/home/pi/.config/google-oauthlib-tool/credentials.json'
DEVICE_MODEL_ID = 'mixologist-7d277-mixologist-v1'
PROJECT_ID = 'mixologist-7d277'
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5
DEFAULT_AUDIO_SAMPLE_RATE = 16000
DEFAULT_AUDIO_SAMPLE_WIDTH = 2
DEFAULT_AUDIO_ITER_SIZE = 3200
DEFAULT_AUDIO_DEVICE_BLOCK_SIZE = 6400
DEFAULT_AUDIO_DEVICE_FLUSH_SIZE = 25600



# network={
# ssid="YOUR_NETWORK_NAME"
# psk="YOUR_NETWORK_PASSWORD"
# proto=RSN
# key_mgmt=WPA-PSK
# pairwise=CCMP
# auth_alg=OPEN
# priority=1
# }

# ex:
# {
#     "ssid": "<Network Name>",
#     "psk": "<Password123>",
#     "id_str": "<Network Id>",
#     "priority": "1"
# }

# must have unique id_str for lookup
wifi_config = [

    
]


