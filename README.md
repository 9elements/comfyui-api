# comfyui-api

Install missing packages via `requirements.txt`

`pip install -r requirements.txt`

## Using the API

You need to a comfyUI server running and be able to access the "/ws" path for this server. If you have the server running localy it usually runs under "127.0.0.1:8188".
If this is not the case for you, change the `server_address` in the `basic_api.py`.

In the workflow folder are two basic Workflows:
- base_workflow.json
- baisc_image_to_image

For simple prompt to image generation load the `base_workflow.json` and call `prompt_to_image` method with your desired parameters.
For image to image generation load the `basic_image_to_image.json` and put your input image in the input folder. Call `prompt_image_to_image` with your desired parameters.