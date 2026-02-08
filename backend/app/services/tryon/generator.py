import os
import uuid
import logging
import base64
from typing import List, Optional, Dict, Any
from PIL import Image
import io
import requests

from dotenv import load_dotenv
load_dotenv()
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class TryOnGenerator:
    def __init__(self):
        self.upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        self.openai_client = None
        self._init_azure_openai()

    def _init_azure_openai(self):
        try:
            # import the Azure OpenAI wrapper if available
            from openai import AzureOpenAI  # type: ignore
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            key = os.environ.get("AZURE_OPENAI_API_KEY")
            if endpoint and key:
                try:
                    self.openai_client = AzureOpenAI(
                        azure_endpoint=endpoint,
                        api_key=key,
                        api_version="2024-12-01-preview",
                    )
                    logger.info("Azure OpenAI client initialized for try-on")
                except Exception:
                    self.openai_client = None
        except ImportError:
            logger.warning("openai package not installed; AI try-on will be disabled")

    async def generate_tryon_image(self, body_image_url: str, clothing_items: List[dict]) -> Optional[Dict[str, Any]]:
        try:
            logger.debug("TryOnGenerator: attempting AI generation")
            result = await self._generate_with_ai(body_image_url, clothing_items)
            if result:
                return result
        except Exception as e:
            logger.warning(f"AI try-on failed: {e}")

        # fallback
        try:
            return await self._generate_with_pillow(body_image_url, clothing_items)
        except Exception as e:
            logger.error(f"Pillow try-on failed: {e}")
            return None

    async def _generate_with_ai(self, body_image_url: str, clothing_items: List[dict]) -> Optional[Dict[str, Any]]:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not endpoint or not key:
            logger.info("Azure OpenAI not configured, skipping AI try-on")
            return None

        # Download images
        import asyncio

        all_urls = [body_image_url]
        clothing_metadata = []
        for item in clothing_items:
            item_url = item.get("mask_url") or item.get("image_url")
            if item_url:
                all_urls.append(item_url)
                clothing_metadata.append({
                    "category": item.get("category", "clothing item"),
                    "sub_category": item.get("sub_category", ""),
                    "body_region": item.get("body_region", ""),
                })

        all_images = await asyncio.gather(*[self._load_image(url) for url in all_urls])
        body_img = all_images[0] if all_images else None
        if not body_img:
            logger.error("Could not load body image for AI try-on")
            return None

        clothing_images = []
        clothing_descriptions = []
        for i, (img, meta) in enumerate(zip(all_images[1:], clothing_metadata)):
            if img:
                clothing_images.append(img)
                sub_cat = meta["sub_category"]
                cat = meta["category"]
                region = meta["body_region"]
                desc = f"{sub_cat} {cat} for {region}" if sub_cat else f"{cat} for {region}"
                clothing_descriptions.append(desc)

        if not clothing_images:
            logger.error("No clothing images loaded for AI try-on")
            return None

        try:
            clothing_list = ", ".join(clothing_descriptions)
            prompt = (
                f"Virtual try-on: Dress the person in the first image wearing the clothing items from the other images: {clothing_list}.\n\n"
                "Requirements:\n"
                "- The person is fully clothed in a neutral outfit; no nudity or revealing content\n"
                "- Keep the person's face, body shape, skin tone, hairstyle, and pose EXACTLY the same\n"
                "- Apply each clothing item to the correct body region naturally\n"
                "- Match colors, patterns, and style precisely from the reference images\n"
                "- Create realistic fabric folds, shadows, and natural fit\n"
                "- Professional fashion photography quality, studio lighting\n\n"
                "Output a single photorealistic image of the person wearing all the provided clothing."
            )

            endpoint = endpoint.rstrip("/")
            deployment = os.environ.get("AZURE_OPENAI_IMAGE_DEPLOYMENT")
            api_version = "2025-04-01-preview"
            url = f"{endpoint}/openai/deployments/{deployment}/images/edits?api-version={api_version}"

            headers = {"api-key": key}

            files = []
            body_bytes_input = self._image_to_bytes(body_img)
            files.append(("image[]", ("body.jpg", body_bytes_input, "image/jpeg")))
            for idx, clothing_img in enumerate(clothing_images):
                clothing_bytes_input = self._image_to_bytes(clothing_img)
                files.append(("image[]", (f"clothing_{idx}.jpg", clothing_bytes_input, "image/jpeg")))

            body_aspect = body_img.width / body_img.height
            output_size = "1024x1536" if body_aspect < 0.8 else "1536x1024" if body_aspect > 1.2 else "1024x1024"

            data = {"prompt": prompt, "n": "1", "size": output_size}

            resp = requests.post(url, headers=headers, data=data, files=files, timeout=180)
            if resp.status_code != 200:
                try:
                    error_payload = resp.json()
                except Exception:
                    error_payload = None
                error_code = None
                if isinstance(error_payload, dict):
                    error_code = (error_payload.get("error") or {}).get("code")
                if error_code == "moderation_blocked":
                    logger.warning("Azure OpenAI blocked the try-on request by safety policy; falling back to Pillow")
                    return None
                logger.error(f"Azure OpenAI API error: {resp.status_code} {resp.text[:400]}")
                return None

            result = resp.json()
            if result.get("data") and len(result["data"]) > 0:
                image_data = result["data"][0]
                if image_data.get("b64_json"):
                    generated_bytes = base64.b64decode(image_data["b64_json"])
                elif image_data.get("url"):
                    img_response = requests.get(image_data["url"], timeout=30)
                    img_response.raise_for_status()
                    generated_bytes = img_response.content
                else:
                    return None

                output_filename = f"tryon_ai_{uuid.uuid4().hex}.png"
                image_url = await storage_service.upload_file(generated_bytes, output_filename, "image/png")
                return {"url": image_url, "bytes": generated_bytes}

            return None
        except Exception as e:
            logger.error(f"Azure OpenAI image generation failed: {e}")
            return None

    def _image_to_bytes(self, img: Image.Image) -> bytes:
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        max_size = 1024
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.read()

    def _image_to_base64(self, img: Image.Image) -> str:
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        max_size = 1024
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    async def _generate_with_pillow(self, body_image_url: str, clothing_items: List[dict]) -> Optional[Dict[str, Any]]:
        logger.info("Falling back to Pillow compositing for try-on")
        body_img = await self._load_image(body_image_url)
        if not body_img:
            logger.error("Could not load body image for Pillow fallback")
            return None

        body_img = body_img.convert("RGBA")
        body_width, body_height = body_img.size

        region_positions = {
            "head": {"y": 0.0, "height": 0.15, "width": 0.25},
            "top": {"y": 0.15, "height": 0.30, "width": 0.50},
            "bottom": {"y": 0.45, "height": 0.35, "width": 0.45},
            "feet": {"y": 0.85, "height": 0.15, "width": 0.30},
            "full_body": {"y": 0.10, "height": 0.80, "width": 0.60},
        }

        for item in clothing_items:
            item_url = item.get("mask_url") or item.get("image_url")
            region = item.get("body_region", "top")
            if not item_url:
                continue
            clothing_img = await self._load_image(item_url)
            if not clothing_img:
                continue

            pos = region_positions.get(region, region_positions["top"])
            target_width = int(body_width * pos["width"])
            target_height = int(body_height * pos["height"])

            clothing_img = clothing_img.convert("RGBA")
            clothing_img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

            paste_x = (body_width - clothing_img.width) // 2
            paste_y = int(body_height * pos["y"])

            body_img.paste(clothing_img, (paste_x, paste_y), clothing_img)

        output_filename = f"tryon_{uuid.uuid4().hex}.png"
        img_buffer = io.BytesIO()
        body_img.convert("RGB").save(img_buffer, format="JPEG", quality=90)
        img_bytes = img_buffer.getvalue()

        image_url = await storage_service.upload_file(img_bytes, output_filename, "image/jpeg")
        return {"url": image_url, "bytes": img_bytes}

    async def resolve_image_url(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            return url
        if any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".avif"]):
            return url
        try:
            import httpx
            import re
            headers = {
                "User-Agent": "Mozilla/5.0",
            }
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return url
                html = response.text
                og_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
                if og_match:
                    image_url = og_match.group(1)
                    from urllib.parse import urljoin
                    image_url = urljoin(url, image_url)
                    return image_url
            return url
        except Exception:
            return url

    async def _load_image(self, image_path: str) -> Optional[Image.Image]:
        if not image_path:
            return None
        if image_path.startswith(("http://", "https://")):
            image_path = await self.resolve_image_url(image_path)
        try:
            if image_path.startswith("data:image"):
                header, encoded = image_path.split(",", 1)
                image_data = base64.b64decode(encoded)
                return Image.open(io.BytesIO(image_data))

            if not image_path.startswith(("http", "/")) and len(image_path) > 100:
                try:
                    image_data = base64.b64decode(image_path)
                    return Image.open(io.BytesIO(image_data))
                except Exception:
                    pass

            if "localhost" in image_path or "127.0.0.1" in image_path:
                from urllib.parse import urlparse
                parsed = urlparse(image_path)
                image_path = parsed.path

            if image_path.startswith(("http://", "https://")):
                import httpx
                headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.google.com/"}
                async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                    response = await client.get(image_path, headers=headers)
                    if response.status_code != 200:
                        return None
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "html" in content_type or not ("image" in content_type):
                        return None
                    return Image.open(io.BytesIO(response.content))

            else:
                rel_path = image_path.replace("/uploads/", "").lstrip("/")
                local_path = os.path.join(self.upload_dir, rel_path)
                if not os.path.exists(local_path):
                    local_path = image_path
                if os.path.exists(local_path):
                    return Image.open(local_path)
        except Exception as e:
            logger.error(f"Failed to load image {str(image_path)[:100]}: {e}")
        return None


# Singleton
tryon_generator = TryOnGenerator()
