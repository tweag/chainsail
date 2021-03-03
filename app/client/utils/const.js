// Scheduler endpoints
export const FLASK_URL = process.env.FLASK_URL || 'http://127.0.0.1:5000';
export const JOB_CREATION_ENDPOINT = '/job';
export const JOB_START_ENDPOINT = (jobId) => `/job/${jobId}/start`;
export const JOB_STOP_ENDPOINT = (jobId) => `/job/${jobId}/stop`;
export const JOB_GET_ENDPOINT = (jobId) => `/job/${jobId}`;
export const JOBS_LIST_ENDPOINT = '/jobs';

// Graphite
export const GRAPHITE_URL = process.env.GRAPHITE_URL || 'http://127.0.0.1';
export const GRAPHITE_PORT = process.env.GRAPHITE_PORT || '80';
