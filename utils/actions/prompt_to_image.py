from api.websocket_api import generate_image_by_prompt
from utils.helpers.find_node import find_node
from utils.helpers.randomize_seed import generate_random_15_digit_number
from utils.helpers.replace_key import replace_key
import json
def prompt_to_image(workflow, positve_prompt, negative_prompt='', save_previews=False):
  prompt = json.loads(workflow)
  replace_key(prompt, 'seed', generate_random_15_digit_number())
  postive_prompt_id = find_node(prompt, 'positive')[0]
  positive_prompt_node = find_node(prompt, postive_prompt_id)

  if negative_prompt != '':
    negative_prompt_id = find_node(prompt, 'negative')[0]
    negative_prompt_node = find_node(prompt, negative_prompt_id)
    negative_prompt_node['inputs']['text'] = negative_prompt

  positive_prompt_node['inputs']['text'] = positve_prompt

  generate_image_by_prompt(prompt, './output/', save_previews)



  