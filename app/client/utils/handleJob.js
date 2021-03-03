export const startJob = (jobId) => {
  const body = JSON.stringify({ jobId });
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  };
  fetch('/api/job/start', requestOptions);
};

export const stopJob = (jobId) => {
  const body = JSON.stringify({ jobId });
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  };
  fetch('/api/job/stop', requestOptions);
};

export const getJob = (jobId) => {
  const requestOptions = {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  };
  fetch(`/api/job/get?jobId=${jobId}`, requestOptions);
};
