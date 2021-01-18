import { FlexCol } from './Flex';
import AnimatedPing from './AnimatedPing';

export default Logs = ({ messages, jobId }) => {
  return (
    <FlexCol className="w-2/5 h-full">
      <div className="mb-5">
        <div className="inline-block mr-3">Log messages</div>
        <AnimatedPing />
      </div>
      <div className="h-full p-10 text-sm bg-gray-900 rounded-lg">
        {messages.map((msg, i) => (
          <div className="mb-5" key={i}>
            {`----Job Id: ${jobId}----`}
            <br />
            {msg}
          </div>
        ))}
      </div>
    </FlexCol>
  );
};
