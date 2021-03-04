import { startJob, stopJob } from '../utils/handleJob';
import AnimatedPing from './AnimatedPing';

const JobButton = ({ jobId, jobStatus }) => {
  const isInitialized = jobStatus === 'initialized';
  const isRunning = jobStatus === 'running';
  const isPending = jobStatus === 'starting';
  return (
    <div
      className={`py-1 text-center rounded-lg lg:transition lg:duration-100 text-white w-32
	      ${isInitialized ? 'bg-green-800 hover:bg-green-900 cursor-pointer' : ''}
	      ${isRunning ? 'bg-red-800 hover:bg-red-900 cursor-pointer' : ''}
	      ${isPending ? 'bg-yellow-800' : ''}
	      `}
      onClick={() => {
        if (isInitialized) startJob(jobId);
        if (isRunning) stopJob(jobId);
      }}
    >
      {isInitialized && 'START'}
      {isRunning && 'STOP'}
      {isPending && (
        <div>
          <div className="inline-block mr-3">PENDING</div>
          <AnimatedPing />
        </div>
      )}
    </div>
  );
};

export default JobButton;
