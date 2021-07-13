// Scheduler endpoints
export const SCHEDULER_URL = process.env.SCHEDULER_URL || 'http://127.0.0.1:5000';
export const JOB_CREATION_URL = `${SCHEDULER_URL}/job`;
export const JOB_START_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}/start`;
export const JOB_STOP_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}/stop`;
export const JOB_GET_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}`;
export const JOBS_LIST_URL = `${SCHEDULER_URL}/jobs`;
export const USER_CREATION_URL = `${SCHEDULER_URL}/user`;

// Graphite
export const GRAPHITE_URL = process.env.GRAPHITE_URL || 'http://127.0.0.1:8080';
export const GRAPHITE_NEGLOGP_URL = (jobId, simulationRun) =>
  `${GRAPHITE_URL}/render?target=aggregate(job${jobId}.${simulationRun}.*.negative_log_prob,'sum')&format=json&from=-3hours&until=now`;
export const GRAPHITE_ACCEPTANCE_RATE_URL = (jobId, simulationRun) =>
  `${GRAPHITE_URL}/render?target=job${jobId}.${simulationRun}.replica*_replica*.acceptance_rate&format=json&from=-3hours&until=now`;
export const GRAPHITE_LOGS_URL = (jobId) =>
  `${GRAPHITE_URL}/events/get_data?tags=log&tags=job${jobId}&from=-3hours&until=now`;
