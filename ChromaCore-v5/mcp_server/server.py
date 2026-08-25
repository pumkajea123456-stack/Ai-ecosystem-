"""MCP-facing tool contracts. Adapter layer can be bound to an MCP SDK."""

def process_image(filename: str):
    return {"tool": "process_image", "filename": filename}

def process_video(filename: str):
    return {"tool": "process_video", "filename": filename}

def analyze_scene(source: str):
    return {"tool": "analyze_scene", "source": source}

def generate_preset(name: str = "default"):
    return {"tool": "generate_preset", "name": name}

def batch_process(items: list[str]):
    return {"tool": "batch_process", "count": len(items)}

TOOLS = [process_image, process_video, analyze_scene, generate_preset, batch_process]
