import Link from 'next/link';

import { FlexRow } from './Flex';
import { useAuth } from './Auth';

const NavItem = (props) => {
  return (
    <Link href={props.href}>
      <div
        className="mx-2 py-2 px-4 border-white border-opacity-20 hover:opacity-60 transition duration-300"
        onClick={props.onClick}
      >
        {props.children}
      </div>
    </Link>
  );
};

const Navbar = () => {
  const user = useAuth();
  return (
    <FlexRow className="items-center h-16 text-sm md:text-base">
      <NavItem href="/">Home</NavItem>
      {!user && <NavItem href="/login">Login</NavItem>}
    </FlexRow>
  );
};
export default Navbar;
