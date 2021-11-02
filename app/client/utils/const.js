// Scheduler endpoints
export const SCHEDULER_URL = process.env.SCHEDULER_URL || 'http://127.0.0.1:5000';
export const JOB_CREATION_URL = `${SCHEDULER_URL}/job`;
export const JOB_START_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}/start`;
export const JOB_STOP_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}/stop`;
export const JOB_GET_URL = (jobId) => `${SCHEDULER_URL}/job/${jobId}`;
export const JOBS_LIST_URL = `${SCHEDULER_URL}/jobs`;

// Graphite
export const GRAPHITE_URL = process.env.GRAPHITE_URL || 'http://127.0.0.1:8080';
export const GRAPHITE_LOGS_URL = (jobId) =>
  `${GRAPHITE_URL}/events/get_data?tags=log&tags=job${jobId}&from=-3hours&until=now`;

// MCMC stats
export const MCMC_STATS_URL = process.env.MCMC_STATS_URL || 'http://127.0.0.1:8081';
export const MCMC_STATS_NEGLOGP_URL = (jobId, simulationRun) =>
  `${MCMC_STATS_URL}/mcmc_stats/${jobID}/${simulationRun}/neg_log_prob_sum`;
export const MCMC_STATS_ACCEPTANCE_RATE_URL = (jobId, simulationRun) =>
  `${MCMC_STATS_URL}/mcmc_stats/${jobId}/${simulationRun}/re_acceptance_rates`;
