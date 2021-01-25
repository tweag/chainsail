import { FlexRow } from './Flex';
import Link from 'next/link';
import { useState } from 'react';

const NavItem = (props) => {
  return (
    <Link href={props.href}>
      <a
        className={`mx-2 py-2 px-4 border-white border-opacity-20 ${
          props.isActive ? 'border-b-2' : 'border-b-0'
        } hover:opacity-60 transition duration-300`}
        onClick={props.onClick}
      >
        {props.children}
      </a>
    </Link>
  );
};

const Navbar = () => {
  const [activeItem, setAcitveItem] = useState('home');
  return (
    <FlexRow className="items-center h-16 text-sm md:text-base">
      <NavItem href="/" isActive={activeItem === 'home'} onClick={() => setAcitveItem('home')}>
        Home
      </NavItem>
    </FlexRow>
  );
};
export default Navbar;
