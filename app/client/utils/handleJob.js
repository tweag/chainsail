export const startJob = (jobId) => {
  const body = JSON.stringify({ jobId });
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  };
  fetch('/api/job/start', requestOptions).catch((err) => console.log(err));
};

export const stopJob = (jobId) => {
  const body = JSON.stringify({ jobId });
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  };
  fetch('/api/job/stop', requestOptions).catch((err) => console.log(err));
};
