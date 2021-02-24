const Container = ({ children, className }) => (
  <div className={`px-10 md:px-20 lg:px-40 font-body ${className}`}>{children}</div>
);

export default Container;
