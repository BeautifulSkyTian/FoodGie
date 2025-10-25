// Camera module - handles all camera-related functionality
class CameraController {
  constructor() {
    this.video = document.getElementById("video");
    this.preview = document.getElementById("preview");
    this.startCameraBtn = document.getElementById("start-camera");
    this.captureBtn = document.getElementById("capture");
    this.retakeBtn = document.getElementById("retake");
    
    this.stream = null;
    this.capturedBlob = null;
    
    this.initEventListeners();
  }

  initEventListeners() {
    this.startCameraBtn.addEventListener("click", () => this.startCamera());
    this.captureBtn.addEventListener("click", () => this.capturePhoto());
    this.retakeBtn.addEventListener("click", () => this.retakePhoto());
  }

  async startCamera() {
    try {
      // Request camera with higher resolution for better quality
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: "environment", // Prefer back camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      
      this.video.srcObject = this.stream;
      
      // Wait for video to be ready before showing
      await new Promise((resolve) => {
        this.video.onloadedmetadata = () => {
          this.video.play();
          resolve();
        };
      });
      
      this.video.classList.remove("hidden");
      this.preview.classList.add("hidden");
      this.startCameraBtn.classList.add("hidden");
      this.captureBtn.classList.remove("hidden");
      this.retakeBtn.classList.add("hidden");
      
      console.log("Camera started successfully");
    } catch (err) {
      console.error("Camera error:", err);
      alert("Could not access camera: " + err.message);
    }
  }

  capturePhoto() {
    const canvas = document.createElement("canvas");
    canvas.width = this.video.videoWidth;
    canvas.height = this.video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(this.video, 0, 0);
    
    canvas.toBlob((blob) => {
      this.capturedBlob = blob;
      const imageUrl = URL.createObjectURL(blob);
      this.preview.src = imageUrl;
      
      // Stop and hide video, show preview
      this.stopCamera();
      this.video.classList.add("hidden");
      this.preview.classList.remove("hidden");
      
      this.captureBtn.classList.add("hidden");
      this.retakeBtn.classList.remove("hidden");
      
      // Dispatch custom event that analyzer can listen to
      window.dispatchEvent(new CustomEvent('photoCapture', { 
        detail: { message: "Photo captured! Click 'Analyze Food' to process." }
      }));
      
      console.log("Photo captured:", blob.size, "bytes");
    }, "image/jpeg", 0.9);
  }

  async retakePhoto() {
    try {
      this.capturedBlob = null;
      await this.startCamera();
      
      this.retakeBtn.classList.add("hidden");
      this.captureBtn.classList.remove("hidden");
      
      // Clear any previous messages
      window.dispatchEvent(new CustomEvent('photoRetake'));
      
      console.log("Ready to capture again");
    } catch (err) {
      console.error("Camera error:", err);
      alert("Could not access camera: " + err.message);
    }
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }
    this.video.pause();
    this.video.srcObject = null;
    console.log("Camera stopped");
  }

  getCapturedBlob() {
    return this.capturedBlob;
  }

  reset() {
    this.capturedBlob = null;
    this.stopCamera();
    this.video.classList.add("hidden");
    this.preview.classList.add("hidden");
    this.startCameraBtn.classList.remove("hidden");
    this.captureBtn.classList.add("hidden");
    this.retakeBtn.classList.add("hidden");
  }
}

// Initialize camera controller when DOM is ready
const camera = new CameraController();
