import unittest

from image_captioning_assistant.generate.utils import (
    convert_bytes_to_base64_str,
    format_prompt_for_claude,
    format_prompt_for_nova,
)


class TestUtils(unittest.TestCase):

    def test_convert_bytes_to_base64_str(self):
        test_bytes = b"Hello, World!"
        expected_base64 = "SGVsbG8sIFdvcmxkIQ=="
        self.assertEqual(convert_bytes_to_base64_str(test_bytes), expected_base64)

    def test_format_prompt_for_claude(self):
        prompt = "Test prompt"
        img_bytes_list = [b"image1", b"image2"]
        result = format_prompt_for_claude(prompt, img_bytes_list)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(len(result[0]["content"]), 3)
        self.assertEqual(result[0]["content"][0]["type"], "text")
        self.assertEqual(result[0]["content"][0]["text"], prompt)
        self.assertEqual(result[0]["content"][1]["type"], "image")
        self.assertEqual(result[0]["content"][2]["type"], "image")

    def test_format_prompt_for_nova(self):
        prompt = "Test prompt"
        img_bytes_list = [b"image1", b"image2"]
        result = format_prompt_for_nova(prompt, img_bytes_list)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(len(result[0]["content"]), 3)
        self.assertEqual(result[0]["content"][0]["text"], prompt)
        self.assertIn("image", result[0]["content"][1])
        self.assertIn("image", result[0]["content"][2])


if __name__ == "__main__":
    unittest.main()
