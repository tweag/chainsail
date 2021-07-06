import { FlexCenter } from './Flex';

const Modal = ({ children, isActive }) => {
  return (
    <FlexCenter
      className={`text-white bg-gray-900 transition duration-300 fixed h-full w-full p-5 md:p-0 ${
        isActive ? 'opacity-100' : 'opacity-0'
      }`}
      style={{ zIndex: isActive ? 1 : -1 }}
    >
      <div>{children}</div>
    </FlexCenter>
  );
};

export default Modal;
