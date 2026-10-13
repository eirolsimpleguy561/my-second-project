import os
import subprocess
import json
import shutil
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="Video Streaming Server")

# Configuration
VIDEO_DIR = Path("videos")
HLS_DIR = Path("hls")
UPLOAD_DIR = Path("uploads")
VIDEO_DIR.mkdir(exist_ok=True)
HLS_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

class VideoProcessor:
    def __init__(self):
        self.processing_queue = []
        self.active_jobs = {}
    
    async def transcode_to_hls(self, input_path: str, output_name: str, resolutions: list = None):
        """Convert video to HLS format with adaptive bitrates"""
        if resolutions is None:
            resolutions = [
                {'name': '240p', 'height': 240, 'bitrate': '400k'},
                {'name': '480p', 'height': 480, 'bitrate': '800k'},
                {'name': '720p', 'height': 720, 'bitrate': '2000k'},
                {'name': '1080p', 'height': 1080, 'bitrate': '4000k'}
            ]
        
        output_dir = HLS_DIR / output_name
        output_dir.mkdir(exist_ok=True)
        
        # Generate master playlist
        master_playlist = output_dir / "master.m3u8"
        master_content = "#EXTM3U\n#EXT-X-VERSION:3\n"
        
        # Generate each resolution variant
        variants = []
        for res in resolutions:
            variant_name = f"{res['name']}.m3u8"
            variant_path = output_dir / variant_name
            segment_pattern = f"{res['name']}_%03d.ts"
            
            # FFmpeg command for HLS transcoding
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-vf', f'scale=-2:{res["height"]}',
                '-b:v', res['bitrate'],
                '-maxrate', res['bitrate'],
                '-bufsize', str(int(res['bitrate'].replace('k', '')) * 2) + 'k',
                '-hls_time', '6',
                '-hls_list_size', '0',
                '-hls_segment_filename', str(output_dir / segment_pattern),
                '-hls_flags', 'program_date_time+append_list',
                str(variant_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")
            
            # Add to master playlist
            bandwidth = int(res['bitrate'].replace('k', '')) * 1000
            master_content += f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION=1920x{res['height']}\n{variant_name}\n"
            variants.append(variant_name)
        
        # Write master playlist
        with open(master_playlist, 'w') as f:
            f.write(master_content)
        
        return {
            'output_dir': str(output_dir),
            'master_playlist': str(master_playlist),
            'variants': variants
        }
    
    async def generate_thumbnail(self, input_path: str, output_path: str, timestamp: str = '00:00:05'):
        """Generate a thumbnail from the video"""
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', timestamp,
            '-vframes', '1',
            '-vf', 'scale=320:180',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        await process.communicate()
        return output_path
    
    async def get_video_info(self, input_path: str) -> dict:
        """Get video metadata using ffprobe"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams',
            '-show_format', input_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFprobe error: {stderr.decode()}")
        
        info = json.loads(stdout.decode())
        video_stream = None
        audio_stream = None
        
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
            elif stream.get('codec_type') == 'audio':
                audio_stream = stream
        
        format_info = info.get('format', {})
        
        return {
            'duration': float(format_info.get('duration', 0)),
            'size': int(format_info.get('size', 0)),
            'video_codec': video_stream.get('codec_name') if video_stream else None,
            'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
            'width': int(video_stream.get('width', 0)) if video_stream else 0,
            'height': int(video_stream.get('height', 0)) if video_stream else 0,
            'bitrate': int(format_info.get('bit_rate', 0))
        }

class VideoManager:
    def __init__(self):
        self.videos = {}
        self.processor = VideoProcessor()
        self.load_metadata()
    
    def load_metadata(self):
        """Load video metadata from JSON file"""
        metadata_file = VIDEO_DIR / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                self.videos = json.load(f)
    
    def save_metadata(self):
        """Save video metadata to JSON file"""
        metadata_file = VIDEO_DIR / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.videos, f, indent=2)
    
    async def add_video(self, file: UploadFile, title: str, description: str = ""):
        """Add a new video"""
        video_id = str(uuid.uuid4())[:8]
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{video_id}_{file.filename}"
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Get video info
        info = await self.processor.get_video_info(str(file_path))
        
        # Generate thumbnail
        thumbnail_path = VIDEO_DIR / f"{video_id}_thumb.jpg"
        await self.processor.generate_thumbnail(str(file_path), str(thumbnail_path))
        
        # Transcode to HLS
        hls_result = await self.processor.transcode_to_hls(str(file_path), video_id)
        
        # Store metadata
        self.videos[video_id] = {
            'id': video_id,
            'title': title,
            'description': description,
            'filename': file.filename,
            'file_path': str(file_path),
            'uploaded_at': datetime.now().isoformat(),
            'thumbnail': f"/videos/{video_id}_thumb.jpg",
            'hls': {
                'master': f"/hls/{video_id}/master.m3u8",
                'variants': hls_result['variants']
            },
            'info': info
        }
        
        self.save_metadata()
        return self.videos[video_id]
    
    def get_video(self, video_id: str):
        """Get video metadata"""
        return self.videos.get(video_id)
    
    def list_videos(self):
        """List all videos"""
        return [
            {
                'id': vid['id'],
                'title': vid['title'],
                'description': vid['description'],
                'thumbnail': vid['thumbnail'],
                'duration': vid['info']['duration'],
                'uploaded_at': vid['uploaded_at']
            }
            for vid in self.videos.values()
        ]
    
    def delete_video(self, video_id: str):
        """Delete a video and its files"""
        if video_id not in self.videos:
            return False
        
        video = self.videos[video_id]
        
        # Delete files
        if os.path.exists(video['file_path']):
            os.remove(video['file_path'])
        
        # Delete thumbnail
        thumb_path = VIDEO_DIR / f"{video_id}_thumb.jpg"
        if thumb_path.exists():
            os.remove(thumb_path)
        
        # Delete HLS files
        hls_dir = HLS_DIR / video_id
        if hls_dir.exists():
            shutil.rmtree(hls_dir)
        
        del self.videos[video_id]
        self.save_metadata()
        return True

# Initialize video manager
video_manager = VideoManager()

# Serve static files
app.mount("/hls", StaticFiles(directory=HLS_DIR), name="hls")
app.mount("/videos", StaticFiles(directory=VIDEO_DIR), name="videos")

@app.get("/")
async def serve_player():
    """Serve the HTML5 video player"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Streaming Player</title>
        <link href="https://vjs.zencdn.net/7.11.4/video-js.css" rel="stylesheet">
        <style>
            body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .video-container { background: #000; border-radius: 8px; overflow: hidden; margin: 20px 0; }
            #video-player { width: 100%; height: auto; }
            .video-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
            .video-item { cursor: pointer; border: 1px solid #ddd; border-radius: 8px; padding: 10px; transition: transform 0.2s; }
            .video-item:hover { transform: scale(1.02); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
            .video-item img { width: 100%; border-radius: 4px; }
            .video-item h3 { margin: 10px 0 5px; }
            .video-item p { color: #666; margin: 0; font-size: 14px; }
            .upload-form { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .upload-form input, .upload-form button { padding: 8px 12px; margin: 5px; }
            .upload-form button { background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .upload-form button:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <h1>📹 Video Streaming Server</h1>
        
        <div class="upload-form">
            <h3>Upload Video</h3>
            <form id="uploadForm">
                <input type="text" id="title" placeholder="Video Title" required>
                <input type="text" id="description" placeholder="Description">
                <input type="file" id="videoFile" accept="video/*" required>
                <button type="submit">Upload</button>
            </form>
            <div id="uploadStatus"></div>
        </div>
        
        <div id="playerSection">
            <div class="video-container">
                <video id="video-player" class="video-js vjs-default-skin" controls preload="auto">
                    <p class="vjs-no-js">Please enable JavaScript to view this video.</p>
                </video>
            </div>
        </div>
        
        <h3>Available Videos</h3>
        <div id="videoList" class="video-list"></div>
        
        <script src="https://vjs.zencdn.net/7.11.4/video.min.js"></script>
        <script>
            let player = null;
            
            function initPlayer(videoId) {
                if (player) player.dispose();
                
                const masterUrl = `/hls/${videoId}/master.m3u8`;
                player = videojs('video-player', {
                    controls: true,
                    autoplay: false,
                    preload: 'auto',
                    sources: [{
                        src: masterUrl,
                        type: 'application/x-mpegURL'
                    }]
                });
            }
            
            function loadVideoList() {
                fetch('/api/videos')
                    .then(res => res.json())
                    .then(videos => {
                        const container = document.getElementById('videoList');
                        container.innerHTML = videos.map(v => `
                            <div class="video-item" onclick="playVideo('${v.id}')">
                                <img src="${v.thumbnail}" alt="${v.title}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22320%22 height=%22180%22/%3E'">
                                <h3>${v.title}</h3>
                                <p>${v.description || 'No description'}</p>
                                <small>${Math.round(v.duration)}s</small>
                            </div>
                        `).join('');
                        
                        if (videos.length > 0) {
                            playVideo(videos[0].id);
                        }
                    });
            }
            
            function playVideo(videoId) {
                initPlayer(videoId);
            }
            
            document.getElementById('uploadForm').onsubmit = function(e) {
                e.preventDefault();
                const formData = new FormData();
                formData.append('title', document.getElementById('title').value);
                formData.append('description', document.getElementById('description').value);
                formData.append('file', document.getElementById('videoFile').files[0]);
                
                const status = document.getElementById('uploadStatus');
                status.textContent = 'Uploading...';
                
                fetch('/api/upload', { method: 'POST', body: formData })
                    .then(res => res.json())
                    .then(data => {
                        status.textContent = 'Upload successful!';
                        loadVideoList();
                        document.getElementById('videoFile').value = '';
                        document.getElementById('title').value = '';
                    })
                    .catch(err => {
                        status.textContent = 'Upload failed: ' + err.message;
                    });
            };
            
            loadVideoList();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

from fastapi.responses import HTMLResponse

@app.post("/api/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = "",
    description: str = ""
):
    """Upload a new video"""
    if not title:
        title = file.filename.rsplit('.', 1)[0]
    
    result = await video_manager.add_video(file, title, description)
    return {
        'success': True,
        'video': result
    }

@app.get("/api/videos")
async def list_videos():
    """List all videos"""
    return video_manager.list_videos()

@app.get("/api/videos/{video_id}")
async def get_video(video_id: str):
    """Get video metadata"""
    video = video_manager.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@app.delete("/api/videos/{video_id}")
async def delete_video(video_id: str):
    """Delete a video"""
    success = video_manager.delete_video(video_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    return {'success': True}

if __name__ == "__main__":
    print("=== Video Streaming Server ===")
    print("Web interface: http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    print("\nRequired: FFmpeg installed and in PATH")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Install: pip install fastapi uvicorn python-multipart
# FFmpeg required: https://ffmpeg.org/download.html