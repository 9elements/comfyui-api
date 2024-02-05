from api.api_helpers import generate_image_by_prompt_and_image
from utils.helpers.randomize_seed import generate_random_15_digit_number
import json
def prompt_image_to_image(workflow, input_path, positve_prompt, negative_prompt='', save_previews=False):
  prompt = json.loads(workflow)
  id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
  k_sampler = [key for key, value in id_to_class_type.items() if value == 'KSampler'][0]
  prompt.get(k_sampler)['inputs']['seed'] = generate_random_15_digit_number()
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

  generate_image_by_prompt_and_image(prompt, './output/', input_path, filename, save_previews)
  