import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
import os
import random
from requests_toolbelt import MultipartEncoder
from PIL import Image
import io

# ---------------------------------------------------------------------------------------------------------------------
# Establish Connection

def open_websocket_connection():
  """
  Establishes a websocket connection to ComfyUI running under the given address and returns the connection object, server address, and a unique client ID.

  This function generates a unique client ID using UUID4, connects to a websocket server at a predefined address, and
  returns the websocket connection object, server address, and the generated client ID. The server address is hardcoded
  to '127.0.0.1:8188'. The connection is made to a specific endpoint on the server that accepts a clientId query parameter.

  Returns:
    tuple: A tuple containing the websocket connection object, server address (str), and client ID (str).
  """
  server_address='127.0.0.1:8188'
  client_id=str(uuid.uuid4())

  ws = websocket.WebSocket()
  ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
  return ws, server_address, client_id

# ---------------------------------------------------------------------------------------------------------------------
# Basic API calls

def queue_prompt(prompt, client_id, server_address):
  """
  Sends a prompt to a ComfyUI to place it into the workflow queue

  This function takes a text prompt along with a client identifier and the server's address, then queues the prompt
  for processing on running ComfyUI. The server is expected to accept JSON data containing the prompt and client ID, and
  it returns a JSON response. The communication is done over HTTP.

  Args:
    prompt (str): The text prompt to be sent to running ComfyUI for processing.
    client_id (str): The identifier for the client sending the request, used by the server to track or manage the request.
    server_address (str): The address of running ComfyUI where the prompt is to be sent, excluding the protocol prefix.

  Returns:
    dict: A dictionary parsed from the JSON response from running ComfyUI, containing the result of processing the prompt.
  """
  p = {"prompt": prompt, "client_id": client_id}
  headers = {'Content-Type': 'application/json'}
  data = json.dumps(p).encode('utf-8')
  req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data, headers=headers)
  return json.loads(urllib.request.urlopen(req).read())



def get_history(prompt_id, server_address):
  """
  Fetches the history to a given prompt ID from ComfyUI

  This function makes an HTTP GET request to a specified server address, requesting the history associated with
  a given prompt ID. The server is expected to return a JSON response that contains the history data, that
  include e.g the paths to the generated Images

  Args:
    prompt_id (str): The unique identifier for the prompt whose history is being requested.
    server_address (str): The address of ComfyUI from which to retrieve the history, excluding the protocol prefix.

  Returns:
    A dictionary parsed from the JSON response containing the history associated with the specified prompt ID.
  """
  with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
      return json.loads(response.read())

def get_image(filename, subfolder, folder_type, server_address):
  """
  Retrieves an image from ComfyUI based on specified parameters and returns the image data.

  This function constructs a query string with the filename, subfolder, and folder type to request an image from
  ComfyUI. It communicates over HTTP to access the specified resource. The server is expected to return the
  image data in response to the constructed URL, which includes the server address and the query parameters.

  Args:
    filename (str): The name of the image file to retrieve.
    subfolder (str): The subfolder within the server's storage where the image is located.
    folder_type (str): The type of folder options are "output", "temp", "input" where the image is stored.
    server_address (str): The address of running ComfyUI from which to retrieve the image, excluding the protocol prefix.

  Returns:
    The raw image data as returned by ComfyUI in response to the query.
  """
  data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
  url_values = urllib.parse.urlencode(data)
  with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
      return response.read()

def upload_image(input_path, name, server_address, image_type="input", overwrite=False):
  """
  Uploads an image to ComfyUI using multipart/form-data encoding.

  This function opens an image file from the specified path and uploads it to running ComfyUI. The server's address,
  the name to save the image as, and optional parameters for image type and overwrite behavior are provided as arguments.
  The image is uploaded as 'image/png'.

  Args:
    input_path (str): The file system path to the image file to be uploaded.
    name (str): The name under which the image will be saved on ComfyUI.
    server_address (str): The address of running ComfyUI where the image will be uploaded, excluding the protocol prefix.
    image_type (str, optional): The type/category of the image being uploaded. Defaults to "input". Other options are "output" and "temp".
    overwrite (bool, optional): Flag indicating whether an existing file with the same name should be overwritten.
                                  Defaults to False.

  Returns:
    The ComfyUI response to the upload request.
  """
  with open(input_path, 'rb') as file:
    multipart_data = MultipartEncoder(
      fields= {
        'image': (name, file, 'image/png'),
        'type': image_type,
        'overwrite': str(overwrite).lower()
      }
    )

    data = multipart_data
    headers = { 'Content-Type': multipart_data.content_type }
    request = urllib.request.Request("http://{}/upload/image".format(server_address), data=data, headers=headers)
    with urllib.request.urlopen(request) as response:
      return response.read()

# -------------------------------------------------------------------------------------------------------
# API helper

def generate_image_by_prompt(prompt, output_path, save_previews=False):
  """
  Generates an image based on a given text prompt and saves it to a specified path, optionally saving preview images.

  This function establishes a websocket connection to initiate a request for image generation based on a text prompt.
  It sends the prompt to ComfyUI via the connection, tracks the progress of the request, retrieves the generated
  images once the process is complete, and saves the resulting image(s) to the specified output path. If enabled,
  it also saves preview images alongside the final image. The function ensures the websocket connection is closed
  properly after the operation completes or if an error occurs.

  Args:
    prompt (str): The text prompt based on which the image is to be generated.
    output_path (str): The file system path where the generated image(s) should be saved.
    save_previews (bool, optional): A flag indicating whether to save preview images alongside the final image.
                                      Defaults to False.

  Raises:
    Exception: Any exception that occurs during the operation, ensuring the websocket is closed before re-raising.
  """
  try:
    ws, server_address, client_id = open_websocket_connection()
    prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
    track_progress(prompt, ws, prompt_id)
    images = get_images(prompt_id, server_address, save_previews)
    save_image(images, output_path, save_previews)
  finally:
    ws.close()

def generate_image_by_prompt_and_image(prompt, output_path, input_path, filename, save_previews=False):
  """
  Generates an image based on a given text prompt and an input image, saving the output to a specified path,
  and optionally saving preview images.

  This function establishes a websocket connection for communication with ComfyUI, uploads an input image to be used
  in the image generation process, and sends a text prompt related to the image. It then tracks the progress of the
  request, retrieves the generated images upon completion, and saves the resulting image(s) to the specified output
  path. If enabled, preview images are also saved. The websocket connection is properly closed after the operation
  completes or in the event of an error.

  Args:
    prompt (str): The text prompt based on which the image is to be generated.
    output_path (str): The file system path where the generated image(s) should be saved.
    input_path (str): The file system path of the input image to be uploaded for the generation process.
    filename (str): The name under which the input image will be saved on CiomfyUI.
    save_previews (bool, optional): Indicates whether to save preview images alongside the final generated image.
                                      Defaults to False.

  Raises:
    Exception: Any exception that occurs during the operation, ensuring the websocket is closed before re-raising.
  """
  try:
    ws, server_address, client_id = open_websocket_connection()
    upload_image(input_path, filename, server_address)
    prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
    track_progress(prompt, ws, prompt_id)
    images = get_images(prompt_id, server_address, save_previews)
    save_image(images, output_path, save_previews)
  finally:
    ws.close()

def save_image(images, output_path, save_previews):
  """
  Saves images to a specified directory, with optional support for saving preview images in a separate subdirectory.

  This function iterates through a list of image data dictionaries, each containing image data and metadata such as
  file name and type. Depending on the type of the image ('temp' for temporary/preview images and another value for
  final images) and whether saving previews is enabled, images are saved to either the main output directory or a
  'temp' subdirectory within it. The function handles the creation of these directories if they do not already exist.
  Images are saved in the format they are received (as indicated by their file names).

  Args:
    images (list of dict): A list of dictionaries, each containing 'image_data' (binary image data),
                            'file_name' (name under which the image should be saved), and 'type' ('temp' for previews).
    output_path (str): The base directory path where the images should be saved.
    save_previews (bool): Indicates whether preview images (of type 'temp') should be saved in a separate subdirectory.

  Raises:
    Exception: Prints an error message if an image fails to be saved due to an exception.
  """
  for itm in images:
      directory = os.path.join(output_path, 'temp/') if itm['type'] == 'temp' and save_previews else output_path
      os.makedirs(directory, exist_ok=True)
      try:
          image = Image.open(io.BytesIO(itm['image_data']))
          image.save(os.path.join(directory, itm['file_name']))
      except Exception as e:
          print(f"Failed to save image {itm['file_name']}: {e}")

def track_progress(prompt, ws, prompt_id):
  """
  Tracks the progress of image generation by listening to websocket messages for a specific prompt ID.

  This function listens to messages from a websocket connection associated with a particular image generation
  request. It decodes the messages to monitor progress updates, including steps completed in the K-Sampler,
  cached execution steps, and current executing nodes. Progress information is printed to the console. The
  function completes when all nodes associated with the prompt have finished executing or when a message
  indicates that the entire execution related to the prompt ID is complete.

  Args:
    prompt (dict): The workflow or prompt configuration, used to determine the total number of nodes.
    ws (websocket.WebSocket): The websocket connection through which progress messages are received.
    prompt_id (str): The unique identifier for the prompt whose progress is being tracked.

  Note:
    This function assumes that messages received through the websocket are JSON strings with specific
    types indicating the nature of the progress update. Binary messages are ignored.
  """
  node_ids = list(prompt.keys())
  finished_nodes = []

  while True:
      out = ws.recv()
      if isinstance(out, str):
          message = json.loads(out)
          if message['type'] == 'progress':
              data = message['data']
              current_step = data['value']
              print('In K-Sampler -> Step: ', current_step, ' of: ', data['max'])
          if message['type'] == 'execution_cached':
              data = message['data']
              for itm in data['nodes']:
                  if itm not in finished_nodes:
                      finished_nodes.append(itm)
                      print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
          if message['type'] == 'executing':
              data = message['data']
              if data['node'] not in finished_nodes:
                  finished_nodes.append(data['node'])
                  print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')


              if data['node'] is None and data['prompt_id'] == prompt_id:
                  break #Execution is done
      else:
          continue
  return

def get_images(prompt_id, server_address, allow_preview = False):
  """
  Retrieves images generated from a prompt, including optional preview images, from the server.

  This function fetches the history of a prompt using its ID to get details of the outputs, specifically images
  generated in response to the prompt. It allows for the retrieval of both final output images and, if specified,
  preview images. The images are fetched from the server using their filename, subfolder location, and type, and
  are returned as a list of dictionaries, each containing the image's binary data, filename, and type.

  Args:
    prompt_id (str): The unique identifier for the prompt whose images are to be retrieved.
    server_address (str): The address of the server from which to retrieve the images.
    allow_preview (bool, optional): Indicates whether preview images should also be retrieved along with final images.

  Returns:
    list of dict: A list of dictionaries, each containing 'image_data' (the binary data of an image), 'file_name'
                  (the name of the file), and 'type' ('temp' for preview images, 'output' for final images).
  """
  output_images = []

  history = get_history(prompt_id, server_address)[prompt_id]
  for node_id in history['outputs']:
      node_output = history['outputs'][node_id]
      output_data = {}
      if 'images' in node_output:
          for image in node_output['images']:
              if allow_preview and image['type'] == 'temp':
                  preview_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                  output_data['image_data'] = preview_data
              if image['type'] == 'output':
                  image_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                  output_data['image_data'] = image_data
      output_data['file_name'] = image['filename']
      output_data['type'] = image['type']
      output_images.append(output_data)

  return output_images

def load_workflow(workflow_path):
  """
  Loads a ComfyUI workflow configuration from a JSON file and returns its content as a JSON-formatted string.

  This function attempts to open and read a workflow configuration file specified by the given path. If successful,
  it parses the file as JSON and returns a string representation of the JSON object. If the file is not found or
  contains invalid JSON, it prints an error message and returns None.

  Args:
    workflow_path (str): The file system path to the workflow configuration file to be loaded.

  Returns:
    str or None: A JSON-formatted string representing the workflow configuration if the file is successfully
                  loaded and parsed; otherwise, None.

  Raises:
    FileNotFoundError: If the specified file does not exist.
    json.JSONDecodeError: If the file contains invalid JSON.
  """
  try:
      with open(workflow_path, 'r') as file:
          workflow = json.load(file)
          return json.dumps(workflow)
  except FileNotFoundError:
      print(f"The file {workflow_path} was not found.")
      return None
  except json.JSONDecodeError:
      print(f"The file {workflow_path} contains invalid JSON.")
      return None

# ---------------------------------------------------------------------------------------------------------------
# Call API

def prompt_to_image(workflow, positve_prompt, negative_prompt='', save_previews=False):
  """
  Converts a text prompt into an image based on a predefined ComfyUI workflow configuration, with optional support
  for a negative prompt and saving preview images.

  This function takes a workflow configuration as a JSON string, along with positive and optional negative text prompts.
  It processes the workflow to update the seed for randomness and to set the positive (and optionally negative) prompts.
  The updated workflow is then used to generate an image, which is saved to a specified output directory. The function
  supports saving intermediate preview images if specified.

  Args:
    workflow (str): A JSON-formatted string representing the ComfyUI workflow configuration for image generation.
    positive_prompt (str): The main text prompt to guide the image generation.
    negative_prompt (str, optional): An optional text prompt meant to guide the image generation in what to avoid.
                                      Defaults to an empty string.
    save_previews (bool, optional): A flag indicating whether to save preview images alongside the final image.
                                    Defaults to False.

  Note:
    The workflow configuration should include at least one 'KSampler' class type for randomness and input nodes
    for positive and negative prompts. This function dynamically updates these nodes based on the provided prompts.
  """
  prompt = json.loads(workflow)
  id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
  k_sampler = [key for key, value in id_to_class_type.items() if value == 'KSampler'][0]
  prompt.get(k_sampler)['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
  postive_input_id = prompt.get(k_sampler)['inputs']['positive'][0]
  prompt.get(postive_input_id)['inputs']['text'] = positve_prompt

  if negative_prompt != '':
    negative_input_id = prompt.get(k_sampler)['inputs']['negative'][0]
    prompt.get(negative_input_id)['inputs']['text'] = negative_prompt

  generate_image_by_prompt(prompt, './output/blog/cyborg', save_previews)

def prompt_image_to_image(workflow, input_path, positve_prompt, negative_prompt='', save_previews=False):
  """
  Transforms an input image according to a positive prompt, with an optional negative prompt, based on a ComfyUI workflow
  configuration, and saves the output image(s), potentially including previews.

  This function updates a given workflow configuration with a positive prompt, an optional negative prompt, and
  an input image path. It dynamically adjusts the workflow for image-to-image transformation, setting a random
  seed for the process, updating text prompts for the transformation, and specifying the input image. The modified
  workflow is used to generate an output image that is saved to a predefined output directory.

  Args:
    workflow (str): The workflow configuration as a JSON-formatted string.
    input_path (str): The file system path of the input image to be transformed.
    positive_prompt (str): The text prompt describing the desired transformation.
    negative_prompt (str, optional): An optional text prompt describing undesired aspects of the transformation.
                                      Defaults to an empty string.
    save_previews (bool, optional): Indicates whether to save preview images alongside the final image.
                                    Defaults to False.

  Note:
    The workflow should include a 'KSampler' for randomness, input nodes for positive and negative prompts,
    and a 'LoadImage' node for the input image. This function updates these nodes based on provided arguments.
  """
  prompt = json.loads(workflow)
  id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
  k_sampler = [key for key, value in id_to_class_type.items() if value == 'KSampler'][0]
  prompt.get(k_sampler)['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
  postive_input_id = prompt.get(k_sampler)['inputs']['positive'][0]
  prompt.get(postive_input_id)['inputs']['text'] = positve_prompt

  if negative_prompt != '':
    negative_input_id = prompt.get(k_sampler)['inputs']['negative'][0]
    prompt.get(negative_input_id)['inputs']['text'] = negative_prompt

  image_loader = [key for key, value in id_to_class_type.items() if value == 'LoadImage'][0]
  filename = input_path.split('/')[-1]
  prompt.get(image_loader)['inputs']['image'] = filename

  generate_image_by_prompt_and_image(prompt, './output/blog/img2img', input_path, filename, save_previews)


# workflow = load_workflow('./workflows/basic_image_to_image.json')
# prompt_to_image(workflow, 'Cyborg in the cyberspace connection to different interfaces and screens with wires, cinematic, colorful, black and neon turquioise', 'ugly, lowres, text, branding', save_previews=True)
# input_path = ''
# prompt_image_to_image(workflow, input_path, 'Woman in a white dress standing in middle of a crowded place, skyscrapers in the background, cinematic, monotone colors, dark, dystopian', save_previews=True)
