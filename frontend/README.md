# TraceVision — React.js Frontend Application

Modern Single-Page Application (SPA) for **TraceVision**, enabling users to upload target person reference photos, ingest multi-camera surveillance video footage, and visualize real-time person re-identification results.

---

## 1. Overview

The frontend interface provides an intuitive operator experience for security and video analysis tasks:
- **Reference Image Selection:** Simple drag-and-drop target photo upload with instant thumbnail preview.
- **Batch Video Ingestion:** Multi-file upload interface with file size and format inspection.
- **Progress Tracking:** Live pipeline status for frame decoding, person detection, tracking, and vector indexing.
- **Interactive Results Dashboard:** Ranked match cards showing similarity score percentages, video filenames, exact frame timestamps, and bounding box coordinates.
- **Demonstration Mode:** Built-in presentation support with representative ReID matches for Tuesday's college project review.

---

## 2. Directory Structure

```text
frontend/
├── src/
│   ├── assets/              # Icons, logos, and static graphics
│   ├── components/
│   │   ├── Navbar.jsx           # Sticky navigation header with status indicators
│   │   ├── FileUpload.jsx       # Reusable drag-and-drop file uploader
│   │   ├── SearchResultCard.jsx # Match display card with score, timestamp & video metadata
│   │   └── ProcessingStatus.jsx # Pipeline progress indicator banner
│   ├── pages/
│   │   ├── HomePage.jsx         # Landing page with project highlights and CTA
│   │   ├── SearchPage.jsx       # Target upload + surveillance video upload view
│   │   └── ResultsPage.jsx      # Similarity search results dashboard
│   ├── services/
│   │   └── api.js               # Axios REST client with fallback presentation dataset
│   ├── App.jsx                  # React Router configuration
│   ├── App.css                  # Component styling & layouts
│   ├── index.css                # CSS variables, dark theme reset & typography
│   └── main.jsx                 # Application entry point
├── package.json
├── vite.config.js
└── README.md
```

---

## 3. Technology Stack

- **Framework:** React 18 + Vite
- **Routing:** React Router v6
- **HTTP Client:** Axios
- **Iconography:** Lucide React
- **Design System:** Custom Dark Theme (`#0f172a` primary background, `#1e293b` cards, `#2563eb` accent)

---

## 4. Setup and Installation

### Prerequisites
- Node.js 18+ and npm installed

### Step 1: Install Dependencies
```bash
cd F:\TraceVision-POCs\frontend
npm install
```

### Step 2: Run Development Server
```bash
npm run dev
```

The frontend will start at:
`http://localhost:5173/`

### Step 3: Build for Production
```bash
npm run build
```

---

## 5. User Workflow

1. Open `http://localhost:5173/` and click **"Start Person Search"**.
2. Upload the target person's photo on the left panel.
3. Select one or more surveillance video clips (`.mp4`, `.mov`, `.avi`) on the right panel.
4. Click **"Launch Search Pipeline"**.
5. View ranked Re-ID matches on the results page showing detection confidence, matched frame timestamp, and track IDs.
