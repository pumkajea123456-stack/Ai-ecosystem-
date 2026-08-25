from io import BytesIO
from PIL import Image
from app.engines.image_engine import inspect_image
from app.engines.video_engine import inspect_video

def test_image_engine_baseline():
    buf=BytesIO()
    Image.new('RGB',(8,6)).save(buf,format='PNG')
    result=inspect_image(buf.getvalue())
    assert result['format']=='PNG'
    assert result['width']==8 and result['height']==6

def test_video_engine_contract_without_media_dependency_assumption():
    result=inspect_video(b'not-a-video','sample.bin')
    assert result['engine']=='ffprobe'
    assert result['status'] in {'dependency_missing','invalid_media'}
