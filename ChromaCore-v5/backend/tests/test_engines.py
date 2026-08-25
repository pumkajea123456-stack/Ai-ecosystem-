from io import BytesIO
from PIL import Image
from app.engines.image_engine import inspect_image
from app.engines.video_engine import inspect_video, transcode_video
from app.engines.vision_engine import analyze_image

def test_image_engine_baseline():
    buf=BytesIO(); Image.new('RGB',(8,6)).save(buf,format='PNG')
    result=inspect_image(buf.getvalue())
    assert result['format']=='PNG'; assert result['width']==8 and result['height']==6

def test_video_engine_contract_without_media_dependency_assumption():
    result=inspect_video(b'not-a-video','sample.bin')
    assert result['engine']=='ffprobe'; assert result['status'] in {'dependency_missing','invalid_media'}

def test_video_transcode_contract_rejects_unknown_format():
    result=transcode_video(b'not-a-video','sample.bin','avi')
    assert result['status']=='invalid_format'

def test_semantic_vision_is_explicitly_pluggable():
    buf=BytesIO(); Image.new('RGB',(2,2)).save(buf,format='PNG')
    result=analyze_image(buf.getvalue())
    assert result['engine']=='semantic-vision'
    assert result['status'] in {'adapter_ready','inferred','inference_error'}
