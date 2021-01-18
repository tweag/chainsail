import { FlexCol } from './Flex';

const Container = ({ children, className }) => (
  <FlexCol between className={`px-5 md:px-20 font-body ${className}`}>
    {children}
  </FlexCol>
);

export default Container;
