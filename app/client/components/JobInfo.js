import JobButton from './JobButton';
import ResultsLink from './ResultsLink';
import { dateFormatter } from '../utils/date';
import fetcher from '../utils/fetcher';
import useSWR from 'swr';

const JobInfo = ({ jobId, job }) => {
  if (job) {
    return <JobDiv job={job} />;
  }
  if (jobId) {
    return <JobInfoFromId jobId={jobId} />;
  }
  console.error('Either jobId or job should be provided to JobInfo component');
  return <></>;
};

const JobDiv = ({ job }) => {
  const jobSpec = job.spec ? JSON.parse(job.spec) : {};
  return (
    <div className="w-full grid grid-cols-2 gap-y-2">
      <div>Name:</div>
      <div>{jobSpec.name}</div>
      <div>Status: </div>
      <div>{job.status}</div>
      <div>Created at:</div>
      <div>{dateFormatter(job.created_at)}</div>
      <div>Started at:</div>
      <div>{dateFormatter(job.started_at)}</div>
      <div>Finished at:</div>
      <div>{dateFormatter(job.finished_at)}</div>
      {job.signed_url && <div>Results:</div>}
      {job.signed_url && <ResultsLink signed_url={job.signed_url} />}
      <div className="mt-3 col-span-2">
        <JobButton jobId={job.id} jobStatus={job.status} width="w-32" />
      </div>
    </div>
  );
};

const JobInfoFromId = ({ jobId }) => {
  const { data } = useSWR(`/api/job/get/${jobId}`, fetcher, {
    refreshInterval: 3000,
  });
  if (data && data.id) {
    return <JobDiv job={data} />;
  } else {
    console.error('job data is either empty or has no id attribute');
    return <></>;
  }
};

export default JobInfo;
