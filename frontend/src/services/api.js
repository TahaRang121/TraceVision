import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

export const videoApi = {
  // Upload a video file
  uploadVideo: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
  },

  // List all uploaded videos
  getVideos: async () => {
    return apiClient.get('/videos');
  },

  // Get specific video details
  getVideoById: async (videoId) => {
    return apiClient.get(`/videos/${videoId}`);
  },
};

export const searchApi = {
  // Submit a reference image for person search
  createSearch: async (referenceImageFile) => {
    const formData = new FormData();
    formData.append('reference_image', referenceImageFile);
    return apiClient.post('/search', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Get search request details
  getSearchStatus: async (searchId) => {
    return apiClient.get(`/search/${searchId}`);
  },

  // Get ranked search results
  getSearchResults: async (searchId) => {
    return apiClient.get(`/search/${searchId}/results`);
  },
};

export const jobApi = {
  // List all processing jobs
  getJobs: async () => {
    return apiClient.get('/jobs');
  },

  // Get single job details
  getJobById: async (jobId) => {
    return apiClient.get(`/jobs/${jobId}`);
  },
};

// Fallback mock data generator for seamless college project presentations
export const getPresentationMockResults = (searchId) => {
  return {
    search_request: {
      id: searchId || "demo-search-01",
      reference_image_path: "/uploads/references/target_person.jpg",
      status: "completed",
      created_at: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
      completed_at: new Date().toISOString(),
    },
    total: 3,
    results: [
      {
        id: "res-01",
        search_request_id: searchId || "demo-search-01",
        detected_person_id: "det-person-101",
        video_id: "vid-cctv-entrance-01",
        similarity_score: 0.942,
        rank: 1,
        matched_frame: 412,
        matched_timestamp: 13.73,
        bbox_x1: 210,
        bbox_y1: 145,
        bbox_x2: 380,
        bbox_y2: 490,
        video: {
          id: "vid-cctv-entrance-01",
          original_filename: "entrance_hall_cctv.mp4",
          duration_seconds: 45.0,
          fps: 30.0,
          width: 1920,
          height: 1080
        },
        detected_person: {
          id: "det-person-101",
          track_id: 4,
          first_frame: 380,
          last_frame: 460,
          first_timestamp: 12.67,
          last_timestamp: 15.33,
          total_appearances: 81,
          avg_confidence: 0.92
        }
      },
      {
        id: "res-02",
        search_request_id: searchId || "demo-search-01",
        detected_person_id: "det-person-102",
        video_id: "vid-corridor-west-02",
        similarity_score: 0.887,
        rank: 2,
        matched_frame: 720,
        matched_timestamp: 24.0,
        bbox_x1: 420,
        bbox_y1: 180,
        bbox_x2: 560,
        bbox_y2: 480,
        video: {
          id: "vid-corridor-west-02",
          original_filename: "corridor_west_camera.mp4",
          duration_seconds: 60.0,
          fps: 30.0,
          width: 1920,
          height: 1080
        },
        detected_person: {
          id: "det-person-102",
          track_id: 11,
          first_frame: 700,
          last_frame: 765,
          first_timestamp: 23.33,
          last_timestamp: 25.50,
          total_appearances: 66,
          avg_confidence: 0.89
        }
      },
      {
        id: "res-03",
        search_request_id: searchId || "demo-search-01",
        detected_person_id: "det-person-103",
        video_id: "vid-parking-lot-03",
        similarity_score: 0.765,
        rank: 3,
        matched_frame: 184,
        matched_timestamp: 6.13,
        bbox_x1: 110,
        bbox_y1: 220,
        bbox_x2: 240,
        bbox_y2: 510,
        video: {
          id: "vid-parking-lot-03",
          original_filename: "parking_lot_gate_cctv.mp4",
          duration_seconds: 35.0,
          fps: 30.0,
          width: 1280,
          height: 720
        },
        detected_person: {
          id: "det-person-103",
          track_id: 2,
          first_frame: 150,
          last_frame: 210,
          first_timestamp: 5.0,
          last_timestamp: 7.0,
          total_appearances: 61,
          avg_confidence: 0.84
        }
      }
    ]
  };
};

export default apiClient;
