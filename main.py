from utils.actions.prompt_to_image import prompt_to_image
from utils.actions.prompt_image_to_image import prompt_image_to_image
from utils.actions.load_workflow import load_workflow
from api.websocket_api import clear_comfy_cache
from api.websocket_api import get_image
import time
import sys

def main():
    try:
      print("Welcome to the program!")
      workflow = load_workflow('./workflows/image_to_image.json')

      # prompt_to_image(workflow, 'beautiful woman sitting on a desk in a nice restaurant, candlelight dinner atmosphere, wearing a red dress', save_previews=True)
      input_path = './input/ComfyUI_00103_.png'
      prompt_image_to_image(workflow, input_path, 'beautiful [white woman], (dark lighting), curly blond hair', save_previews=True)
    except Exception as e:
      print(f"An error occurred: {e}")
      exit_program()

def exit_program():
  print("Exiting the program...")
  sys.exit(0)

def clear():
  clear_comfy_cache(True, True)

def image_by_file():
  print(get_image('ComfyUI_00042_.png', '', 'output'))

main()
# clear()

# image_by_file()