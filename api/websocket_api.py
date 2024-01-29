#This is an example that uses the websockets api to know when a prompt execution is done
#Once the prompt execution is done it downloads the images using the /history endpoint

import uuid
import json
import urllib.request
import urllib.parse
import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
from PIL import Image
import io


server_address='127.0.0.1:8188'
client_id=str(uuid.uuid4())

ws = websocket.WebSocket()
ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))

def generate_image_by_prompt(prompt, output_path, save_previews=False):
    prompt_id = queue_prompt(prompt)['prompt_id']
    images = get_images(ws, prompt_id, save_previews)
    save_image(images, output_path, save_previews)

def save_image(images, output_path, save_previews):
    for itm in images:
        if itm['type'] == 'temp' and save_previews:
            image = Image.open(io.BytesIO(itm['image_data']))
            image.save(output_path + 'temp/' + itm['file_name'])
        else:
            image = Image.open(io.BytesIO(itm['image_data']))
            image.save(output_path + itm['file_name'])

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def interupt_prompt():
    req =  urllib.request.Request("http://{}/interrupt".format(server_address), data={})
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt_id, allow_preview = False):
    output_images = []
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            continue #previews are binary data


    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        output_data = {}
        if 'images' in node_output:
            for image in node_output['images']:
                if allow_preview and image['type'] == 'temp':
                    preview_data = get_image(image['filename'], image['subfolder'], image['type'])
                    output_data['image_data'] = preview_data
                if image['type'] == 'output':
                    image_data = get_image(image['filename'], image['subfolder'], image['type'])
                    output_data['image_data'] = image_data
        output_data['file_name'] = image['filename']
        output_data['type'] = image['type']
        output_images.append(output_data)

    return output_images



