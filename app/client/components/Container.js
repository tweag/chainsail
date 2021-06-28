const Container = ({ children, className }) => (
  <div className={`px-5 md:px-10 lg:px-40 font-body ${className}`}>{children}</div>
);

export default Container;
