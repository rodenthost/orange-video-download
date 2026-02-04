from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs("static", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <title>Reddit Video Downloader</title>
    </head>
    <body>
        <h2>Reddit Video Downloader with Preview (No App Needed)</h2>
        <form action="/preview" method="post">
            <input type="text" name="url" placeholder="Reddit post URL" required>
            <button type="submit">Preview</button>
        </form>
    </body>
    </html>
    """

@app.post("/preview", response_class=HTMLResponse)
async def preview(url: str = Form(...)):
    try:
        # Convert normal URL to JSON endpoint
        if not url.endswith(".json"):
            if url.endswith("/"):
                url += ".json"
            else:
                url += "/.json"

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()

        # Navigate to video URL
        post = data[0]["data"]["children"][0]["data"]
        if not post.get("is_video"):
            return "<h3>This Reddit post does not contain a video.</h3>"

        video_url = post["media"]["reddit_video"]["fallback_url"]
        video_id = post["id"]
        local_path = f"static/{video_id}.mp4"

        # Download video temporarily
        if not os.path.exists(local_path):
            r = requests.get(video_url, stream=True)
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

        return f"""
        <h3>Preview: {post['title']}</h3>
        <video width="480" controls>
            <source src="/{local_path}" type="video/mp4">
        </video>
        <br>
        <a href="/download/{video_id}"><button>Download Video</button></a>
        """
    except Exception as e:
        return f"<h3>Error: {str(e)}</h3>"

@app.get("/download/{video_id}")
async def download(video_id: str):
    path = f"static/{video_id}.mp4"
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=f"{video_id}.mp4")
    return {"error": "Video not found."}
