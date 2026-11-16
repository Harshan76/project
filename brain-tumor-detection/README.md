# Generative AI-Assisted Brain Tumor Detection with MRI Enhancement

An end-to-end medical imaging and computer-aided diagnosis (CADx) web application. This platform integrates OpenCV image enhancement, deep convolutional neural networks (TensorFlow / Keras), Grad-CAM explainability, and automated clinical report generation into a modern dark-navy healthcare dashboard.

---

## 🌟 Key Capabilities

1. **OpenCV MRI Enhancement Pipeline**:
   - Contrast Limited Adaptive Histogram Equalization (CLAHE) in LAB space.
   - Bilateral and Fast Non-Local Means (NLM) noise reduction preserving tissue borders.
   - Unsharp masking sharpening and dynamic range normalization.
   - Interactive 3-panel visual inspection: Original MRI, Enhanced MRI, and Magma Contrast Delta Map.

2. **Deep Learning Brain Tumor Classification**:
   - 4 diagnostic categories:
     - **Glioma** (Intra-axial glial neoplasm)
     - **Meningioma** (Dural-based extra-axial mass)
     - **Pituitary Tumor** (Sellar / suprasellar adenoma)
     - **No Tumor** (Unremarkable healthy scan)
   - Standardized 224 × 224 tensor preprocessing and intensity normalization.
   - Full categorical Softmax probability distribution and confidence score metrics.

3. **Grad-CAM (Gradient-Weighted Class Activation Mapping)**:
   - Visualizes gradient attribution maps from the final convolutional layers.
   - Color scale (JET colormap) overlay revealing features influencing the model's prediction.
   - Explicit clinical disclaimer: identifies model attention patterns, not histological tumor margins.

4. **AI-Assisted Diagnostic Reporting & PDF Generation**:
   - Structured clinical narrative summarizing study metadata, technical operations, and pathophysiological descriptions.
   - Deterministic local medical intelligence knowledge base with cloud generative fallback.
   - Professional PDF compilation using ReportLab complete with MRI figures and regulatory disclaimers.

5. **Scan Archival Registry & Real-Time Analytics**:
   - SQLite persistent database storing study records, parameters, predictions, and report references.
   - Interactive analytics dashboard with Recharts category distributions and activity timeline charts.
   - Search by Scan ID or Patient ID, category filtering, and record deletion with confirmation.

---

## 🏗️ Project Architecture

```
brain-tumor-detection/
├── frontend/                     # React 18 + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx       # Dark navy navigation sidebar
│   │   │   └── Header.jsx        # Model status and quick actions
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx     # Clinical metrics & Recharts graphs
│   │   │   ├── UploadMRI.jsx     # Drag-and-drop ingestion & sample selector
│   │   │   ├── MRIEnhancement.jsx# OpenCV filters & 3-panel comparison
│   │   │   ├── DetectionResults.jsx# Inference, bar charts, Grad-CAM, report
│   │   │   ├── ScanHistory.jsx   # SQLite scan registry & search
│   │   │   └── AboutProject.jsx  # Academic documentation
│   │   ├── services/
│   │   │   └── api.js            # REST API client
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── backend/                      # Python Flask REST API & AI Engine
│   ├── database/
│   │   ├── db.py                 # SQLite database schema and operations
│   │   └── brain_tumor.db        # SQLite database file (auto-created)
│   ├── models/
│   │   └── brain_tumor_model.keras # Trained CNN weights
│   ├── routes/
│   │   └── api_routes.py         # REST endpoints
│   ├── services/
│   │   ├── image_enhancement.py  # OpenCV CLAHE, Bilateral filter, unsharp mask
│   │   ├── prediction.py         # TensorFlow inference & probability scoring
│   │   ├── gradcam.py            # Grad-CAM heatmap generation & overlays
│   │   └── report_generator.py   # Clinical knowledge base & ReportLab PDF
│   ├── uploads/                  # Ingested MRI scans
│   ├── enhanced_images/          # Enhanced images & Grad-CAM overlays
│   ├── reports/                  # Generated PDF diagnostic reports
│   ├── sample_mris/              # Preloaded benchmark MRIs for 1-click evaluation
│   ├── train_model.py            # Deep CNN training pipeline
│   ├── requirements.txt          # Python dependencies
│   └── app.py                    # Flask server entrypoint
│
└── README.md                     # Comprehensive setup guide
```

---

## 🚀 Step-by-Step Installation & Setup

### Prerequisites
- **Python**: 3.10 or 3.12+
- **Node.js**: v18+ (tested on Node v24)
- **Git** / PowerShell / Bash

---

### Step 1: Install Python Backend Dependencies

Open a terminal in the project root:

```bash
cd brain-tumor-detection/backend
pip install -r requirements.txt
```

*Requirements include:*
- `flask`, `flask-cors`
- `tensorflow`, `keras`
- `opencv-python`
- `numpy`, `scikit-learn`
- `pillow`
- `reportlab`

---

### Step 2: Model Training & Dataset Preparation

You have two options for training the CNN model:

#### Option A: Immediate Academic Benchmark (No external download needed)
Run the training script directly. It will detect that the Kaggle dataset is not present, generate calibrated representative MRI morphological structures, train the 4-block deep CNN, and save the model to `models/brain_tumor_model.keras`:

```bash
cd brain-tumor-detection/backend
python train_model.py --epochs 6 --batch-size 16
```

This also generates 4 test MRIs (`sample_glioma.jpg`, `sample_meningioma.jpg`, `sample_pituitary_tumor.jpg`, `sample_no_tumor.jpg`) in `backend/sample_mris/` for immediate 1-click evaluation in the web interface.

#### Option B: Full Kaggle Brain Tumor MRI Dataset
1. Download the [Brain Tumor MRI Dataset from Kaggle](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset).
2. Extract the dataset into `backend/dataset/`:
   ```
   backend/dataset/
   ├── Training/
   │   ├── glioma/
   │   ├── meningioma/
   │   ├── notumor/
   │   └── pituitary/
   └── Testing/
       ├── glioma/
       ├── meningioma/
       ├── notumor/
       └── pituitary/
   ```
3. Run the training script on the dataset:
   ```bash
   python train_model.py --dataset-dir ./dataset --epochs 15 --batch-size 32
   ```

---

### Step 3: Start the Backend Server

```bash
cd brain-tumor-detection/backend
python app.py
```

The Flask server will start at:
👉 `http://127.0.0.1:5000`

---

### Step 4: Install and Start Frontend

In a new terminal window:

```bash
cd brain-tumor-detection/frontend
npm install
npm run dev
```

The React + Vite application will open at:
👉 `http://localhost:3000`

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/model/status` | Check if model weights are loaded and get architecture info |
| `POST` | `/api/upload` | Multipart upload for cranial MRI scans (JPG, PNG, BMP) |
| `POST` | `/api/enhance` | Apply OpenCV CLAHE, bilateral filtering, and sharpening |
| `POST` | `/api/predict` | Run CNN inference and Grad-CAM explainability |
| `POST` | `/api/generate-report` | Generate structured clinical summary & ReportLab PDF |
| `GET` | `/api/history` | List scan history with category filtering & search |
| `GET` | `/api/history/<id>` | Fetch detailed record for a specific scan ID |
| `DELETE` | `/api/history/<id>` | Permanently purge scan and associated assets from DB & disk |
| `GET` | `/api/dashboard/stats` | Real-time analytics and category breakdown from SQLite |
| `GET` | `/api/sample-images` | Retrieve available demo MRIs for instant testing |

---

## 🔬 Radiological & Machine Learning Details

### Image Enhancement
- **CLAHE (Contrast Limited Adaptive Histogram Equalization)**: Operates on the luminance channel (L in LAB color space) with customizable tile grid size (8×8 default) and clip limit (2.5 default) to prevent over-amplification of acoustic noise.
- **Bilateral Filter**: Preserves sharp structural borders (calvarium, ventricles, sulci) while smoothing low-frequency sensor fluctuations.
- **Unsharp Masking**: High-pass accentuation using Gaussian difference convolution:
  $$\text{Sharpened} = \text{Image} + \alpha \times (\text{Image} - \text{Gaussian}(\text{Image}))$$

### Grad-CAM Interpretability
Grad-CAM computes the gradients of the unnormalized class score $y^c$ with respect to the feature map activations $A^k$ of the final convolutional layer:
$$\alpha_k^c = \frac{1}{Z} \sum_i \sum_j \frac{\partial y^c}{\partial A_{i,j}^k}$$
The activation map is synthesized using a rectified linear combination:
$$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$

---

## ⚖️ Statutory Clinical Disclaimer

> **IMPORTANT NOTICE:** This software application is engineered strictly for academic research, education, and decision-support exploration. It is **NOT** a certified medical device and **DOES NOT** provide definitive clinical diagnoses. All findings, probabilities, and Grad-CAM visualizations must be reviewed and verified by a licensed neuroradiologist or attending physician before making any diagnostic or patient care decisions.
