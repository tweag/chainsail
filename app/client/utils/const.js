// Scheduler endpoints
export const SCHEDULER_URL = process.env.FLASK_URL || 'http://127.0.0.1:5000';
export const JOB_CREATION_URL = `${SCHEDULER_URL}/job`;
export const JOB_START_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}/start`;
export const JOB_STOP_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}/stop`;
export const JOB_GET_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}`;
export const JOBS_LIST_URL = `${SCHEDULER_URL}/jobs`;

// Graphite
export const GRAPHITE_URL = process.env.GRAPHITE_URL || 'http://127.0.0.1:8080';
export const GRAPHITE_NEGLOGP_URL = (jobId, simulationRun) =>
  `${GRAPHITE_URL}/render?target=aggregate(${jobId}.${simulationRun}.*.negative_log_prob,'sum')&format=json&from=-5min`;
export const GRAPHITE_ACCEPTANCE_RATE_URL = (jobId, simulationRun) =>
  `${GRAPHITE_URL}/render?target=${jobId}.${simulationRun}.replica*_replica*.acceptance_rate&format=json`;
