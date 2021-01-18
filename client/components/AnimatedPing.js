export default AnimatedPing = () => (
  <div className="inline-block">
    <div className="flex w-3 h-3">
      <span className="absolute w-3 h-3 bg-purple-400 rounded-full opacity-75 animate-ping"></span>
      <span className="relative w-3 h-3 bg-purple-500 rounded-full"></span>
    </div>
  </div>
);
