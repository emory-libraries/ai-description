import base64
import json
from PIL import Image
from io import BytesIO
import image_captioning_assistant.generate.prompts as p

def convert_bytes_to_base64_str(img_bytes: bytes) -> str:
    """Convert bytes to Base64 encoding.

    Args:
        img_bytes (bytes): Image bytes

    Returns:
        str: Image bytes as base64 string
    """
    return base64.b64encode(img_bytes).decode("utf-8")

def get_front_and_back_bytes_from_paths(image_path: str, image_path_back: str = None) -> tuple:
    """
    Encode the front image and optionally the back image of a ticket.

    Args:
        image_path (str): Path to the front image file.
        image_path_back (str, optional): Path to the back image file. Defaults to None.

    Returns:
        list: A list containing the base64 encoded strings of the front and back images (if provided).
    """
    image_list = []
    with open(image_path, "rb") as image_file:
        image_list.append(image_file.read())
    if image_path_back:
        with open(image_path_back, "rb") as image_file_back:
            image_list.append(image_file_back.read())
    return image_list

def encode_image_from_path(image_full_path, max_size=2048, jpeg_quality=95):
    with open(image_full_path, "rb") as image_file:
        # Open image and convert to RGB (removes alpha channel if present)
        image = Image.open(image_file).convert('RGB')
        
        # Set maximum dimensions while maintaining aspect ratio
        max_dimension = 2048  # Adjust this based on your size requirements
        image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
        
        # Optimize JPEG quality and save to buffer
        buffer = BytesIO()
        image.save(buffer, 
                  format='JPEG', 
                  quality=jpeg_quality,  # Adjust between 75-95 for quality/size balance
                  optimize=True)
        
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode("utf-8")
    
    # Verify size constraint
    if len(image_data) >= 10000000:
        raise ValueError("Resized image still exceeds size limit - try reducing max_dimension or quality")
    
    return image_data


def extract_json_and_cot_from_text(text):
    # split chain of thought
    cot, text = text.split(p.COT_TAG_END)
    try:
        return (cot.replace(p.COT_TAG,''), json.loads(text.strip()))
    except json.JSONDecodeError:
        print("Could not decode")
        print(text)
        raise json.JSONDecodeError

def format_prompt_for_claude(prompt: str, img_bytes_list: list[bytes]) -> list[dict]:
    """Format prompt for Anthropic Claude LLM.

    Args:
        prompt (str): Text prompt for model
        img_bytes_list (list[bytes]): Image(s) for model

    Returns:
        list[dict]: Prompt formatted for Anthropic's Claude models.
    """
    content = [{"type": "text", "text": prompt}]
    for img_bytes in img_bytes_list:
        img_message = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": convert_bytes_to_base64_str(img_bytes),
            },
        }
        content.append(img_message)
    return [{"role": "user", "content": content}]


def format_prompt_for_nova(prompt: str, img_bytes_list: list[bytes]) -> list[dict]:
    """Format prompt for Amazon Nova models.

    Args:
        prompt (str): Text prompt for model
        img_bytes_list (list[bytes]): Image(s) for model

    Returns:
        list[dict]: Prompt formatted for Amazon's Nova models.
    """
    content = [{"text": prompt}]
    for img_bytes in img_bytes_list:
        img_message = {
            "image": {
                "format": "jpeg",
                "source": {"bytes": convert_bytes_to_base64_str(img_bytes)},
            }
        }
        content.append(img_message)
    return [{"role": "user", "content": content}]
