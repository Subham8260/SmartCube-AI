# SmartCube AI

**AI-Powered Rubik’s Cube Solver using Computer Vision**

SmartCube AI is a backend-focused AI project that automatically scans, validates, and solves a Rubik’s Cube from images.
It combines **computer vision**, **robust validation logic**, and the **Kociemba solving algorithm** to generate step-by-step cube solutions, even when input data is imperfect.


## 🚀 Features

* **Image-Based Cube Scanning**
  Accepts images of cube faces (camera or uploaded images) and extracts sticker colors.

* **Robust Cube Validation**
  Automatically handles missing faces, invalid colors, and incomplete scans to ensure solver stability.

* **Automatic Cube Solving**
  Uses the Kociemba algorithm to compute optimal, step-by-step solving moves.

* **API-Driven Architecture**
  Built with FastAPI, making it easy to integrate with web or mobile frontends.

* **Error-Tolerant Design**
  Prevents solver crashes by normalizing cube data before solving.

## 🛠️ Tech Stack

* **Python**
* **FastAPI**
* **OpenCV**
* **NumPy**
* **Kociemba Solver**
* **Computer Vision & Image Processing**
  
## 🧠 How It Works

1. User uploads images of cube faces (up to 6).
2. The backend extracts individual tiles from each image.
3. Color prediction assigns a color to each tile.
4. Cube state is validated and normalized.
5. The solver computes the solution.
6. Step-by-step solving moves are returned via API.

## 📡 API Endpoints

### `POST /scan-all`

Scans multiple cube face images and returns detected colors.

**Request**

```json
{
  "images": ["base64_image_1", "base64_image_2", "..."]
}
```

**Response**

```json
{
  "cube_faces": [["white", "red", "..."], ...]
}
```
### `POST /solve`

Validates cube state and returns solving steps.

**Request**

```json
{
  "cube_faces": [["white", "red", "..."], ...]
}
```

**Response**

```json
{
  "success": true,
  "steps": ["R", "U", "R'", "U'"]
}
```
## ✅ Key Highlights

* Handles real-world imperfections in image-based inputs
* Ensures all six cube faces are present before solving
* Designed for scalability and future feature expansion
* Internship- and resume-ready project structure

## 🔮 Future Enhancements

* Real-time camera scanning
* 3D cube visualization
* ML-based color classification
* Frontend integration (Web / Mobile)
* Cloud deployment and Dockerization

## 📌 Use Cases

* AI & Computer Vision learning project
* Backend API development showcase
* Algorithmic problem-solving demonstration
* Internship and portfolio project

## 👨‍💻 Author

**Subham Dash**
B.Tech CSE | AI & ML Enthusiast

⭐ If you find this project useful, consider giving it a star!
