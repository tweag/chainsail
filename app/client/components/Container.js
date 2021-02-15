const Container = ({ children, className }) => (
  <div className={`px-5 md:px-20 font-body ${className}`}>{children}</div>
);

export default Container;
