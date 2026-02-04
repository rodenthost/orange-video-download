from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import requests
import os

app = FastAPI()

# Serve static files (downloaded videos)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure static folder exists
os.makedirs("static", exist_ok=True)

# Home page (serves HTML frontend)
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reddit Video Downloader</title>
    </head>
    <body>
        <h2>Reddit Video Downloader with Instant Preview</h2>
        <input type="text" id="url" placeholder="Reddit post URL" style="width: 300px;">
        <button onclick="previewVideo()">Preview</button>

        <div id="preview" style="margin-top:20px;"></div>

        <script>
            async function previewVideo() {
                const url = document.getElementById("url").value;
                const previewDiv = document.getElementById("preview");
                previewDiv.innerHTML = "Loading...";

                const formData = new FormData();
                formData.append("url", url);

                const response = await fetch("/get_video", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();
                if (data.error) {
                    previewDiv.innerHTML = "<h3 style='color:red;'>" + data.error + "</h3>";
                    return;
                }

                previewDiv.innerHTML = `
                    <h3>${data.title}</h3>
                    <video width="480" controls>
                        <source src="${data.video_path}" type="video/mp4">
                    </video>
                    <br>
                    <a href="${data.download_path}"><button>Download Video</button></a>
                `;
            }
        </script>
    </body>
    </html>
    """

# AJAX endpoint to fetch and save Reddit video
@app.post("/get_video")
async def get_video(url: str = Form(...)):
    try:
        # Convert Reddit URL to JSON endpoint
        if not url.endswith(".json"):
            if url.endswith("/"):
                url += ".json"
            else:
                url += "/.json"

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()

        post = data[0]["data"]["children"][0]["data"]
        if not post.get("is_video"):
            return JSONResponse({"error": "This Reddit post does not contain a video."})

        video_url = post["media"]["reddit_video"]["fallback_url"]
        video_id = post["id"]
        local_path = f"static/{video_id}.mp4"

        # Download video temporarily if not exists
        if not os.path.exists(local_path):
            r = requests.get(video_url, stream=True)
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

        return JSONResponse({
            "title": post["title"],
            "video_path": f"/{local_path}",
            "download_path": f"/download/{video_id}"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

# Endpoint to download video
@app.get("/download/{video_id}")
async def download(video_id: str):
    path = f"static/{video_id}.mp4"
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=f"{video_id}.mp4")
    return JSONResponse({"error": "Video not found."})
