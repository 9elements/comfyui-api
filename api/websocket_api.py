#This is an example that uses the websockets api to know when a prompt execution is done
#Once the prompt execution is done it downloads the images using the /history endpoint

import uuid
import json
import urllib.request
import urllib.parse
import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
from PIL import Image
import io
from utils.helpers.find_node import find_node
from requests_toolbelt import MultipartEncoder

server_address='127.0.0.1:8188'
client_id=str(uuid.uuid4())

ws = websocket.WebSocket()
ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))

def setup_image(input_path, name, type="input", overwrite=False):
    with open(input_path, 'rb') as file:
        multipart_data = MultipartEncoder(
            fields={
                'image': (name, file, 'image/jpeg'),  # Adjust the content-type accordingly
                'type': type,
                'overwrite': str(overwrite).lower()
            }
        )

        data = multipart_data
        headers = {'Content-Type': multipart_data.content_type}
        request = urllib.request.Request("http://{}/upload/image".format(server_address), data=data, headers=headers)
        with urllib.request.urlopen(request) as response:
            return response.read()

def generate_image_by_prompt(prompt, output_path, save_previews=False):
    prompt_id = queue_prompt(prompt)['prompt_id']
    track_progress(prompt, ws, prompt_id)
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


def track_progress(prompt, ws, prompt_id):
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
            continue #previews are binary data
    return

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

def get_node_info_by_class(node_class):
    with urllib.request.urlopen("http://{}/object_info/{}".format(server_address, node_class)) as response:
        return json.loads(response.read())

def clear_comfy_cache(unload_models=False, free_memory=False):
    clear_data = {
        "unload_models": unload_models,
        "free_memory": free_memory
    }
    data = json.dumps(clear_data).encode('utf-8')

    with urllib.request.urlopen("http://{}/free".format(server_address), data=data) as response:
        return response.read()

