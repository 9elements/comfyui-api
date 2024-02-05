from utils.actions.prompt_to_image import prompt_to_image
from utils.actions.prompt_image_to_image import prompt_image_to_image
from utils.actions.load_workflow import load_workflow
from api.api_helpers import clear
import sys

def main():
    try:
      print("Welcome to the program!")
      workflow = load_workflow('./workflows/base_workflow.json')
      for iter in range(1, 11):
        prompt_to_image(workflow, '(realistic:1.25), beautiful:1.1) mountain landscape with a deep blue lake, photolike, high detail, monoton colors', 'lowres, text, branding, watermark, humans, frames, painting', save_previews=True)
      # prompt_to_image(workflow, '(beautiful woman:1.3) sitting on a desk in a nice restaurant with a (glass of wine and plate with salat:0.9), (candlelight dinner atmosphere:1.1), (wearing a red evening dress:1.2), dimmed lighting, cinema, high detail', save_previews=True)
      # input_path = './input/ComfyUI_00241_.png'
      # prompt_image_to_image(workflow, input_path, '(white woman wearing a black evening dress:1.5), dimmed lighting, cinema, high detail', save_previews=True)
    except Exception as e:
      print(f"An error occurred: {e}")
      exit_program()

def exit_program():
  print("Exiting the program...")
  sys.exit(0)

def clear_comfy():
  clear(True, True)

main()
