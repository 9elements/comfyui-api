from api.websocket_api import generate_image_by_prompt
from api.websocket_api import setup_image
from utils.helpers.find_node import find_node
from utils.helpers.randomize_seed import generate_random_15_digit_number
from utils.helpers.replace_key import replace_key
from utils.helpers.find_parent import find_parent_of_key
import json
def prompt_image_to_image(workflow, input_path, positve_prompt, negative_prompt='', save_previews=False):
  prompt = json.loads(workflow)
  replace_key(prompt, 'seed', generate_random_15_digit_number())
  id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
  k_sampler = [key for key, value in id_to_class_type.items() if value == 'KSampler'][0]

  postive_input_id = prompt.get(k_sampler)['inputs']['positive'][0]
  prompt.get(postive_input_id)['inputs']['text_g'] = positve_prompt
  prompt.get(postive_input_id)['inputs']['text_l'] = positve_prompt

  if negative_prompt != '':
    negative_input_id = prompt.get(k_sampler)['inputs']['negative'][0]
    id_to_class_type.get(negative_input_id)['inputs']['text_g'] = negative_prompt
    id_to_class_type.get(negative_input_id)['inputs']['text_l'] = negative_prompt


  image_loader = [key for key, value in id_to_class_type.items() if value == 'LoadImage'][0]
  filename = input_path.split('/')[-1]
  prompt.get(image_loader)['inputs']['image'] = filename

  setup_image(input_path, filename)
  generate_image_by_prompt(prompt, './output/', save_previews)



  