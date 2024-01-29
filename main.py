from utils.actions.prompt_to_image import prompt_to_image
from utils.actions.load_workflow import load_workflow
from utils.actions.interrupt_prompt import interrupt
import time
import sys

def main():
    try:
      print("Welcome to the program!")
      workflow = load_workflow('./workflows/test_workflow.json')

      prompt_to_image(workflow, 'a tiny little green and blue monster wearing a coat and a little hat, very cute with sharp teeths', True)
    except Exception as e:
      print(f"An error occurred: {e}")
      exit_program()

def exit_program():
  print("Exiting the program...")
  interrupt()
  sys.exit(0)

main()