import base64


def convert_bytes_to_base64_str(img_bytes: bytes) -> str:
    """Convert bytes to Base64 encoding.

    Args:
        img_bytes (bytes): Image bytes

    Returns:
        str: Image bytes as base64 string
    """
    return base64.b64encode(img_bytes).decode("utf-8")


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
